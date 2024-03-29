#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

DEBUG=True

import re
import copy
from ansible.module_utils.basic import AnsibleModule
from ansible.errors import AnsibleModuleError
from collections import namedtuple
from azure.mgmt.resource import ResourceManagementClient

from azure.mgmt.core.tools import parse_resource_id, resource_id, is_valid_resource_id
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import ResourceNotFoundError

from ansible_collections.ansiblesharp.az.plugins.module_utils.common import COMMON_ARGS, AZURE_RG_OBJECT_CLASS, merge_dict, get_defaults_azure_login_credential

from ansible_collections.ansiblesharp.az.plugins.module_utils.cloud_config import CloudConfig
from ansible_collections.ansiblesharp.common.plugins.module_utils.common_config import CommonConfig


class AnsibleSharpAzureModule(AnsibleModule):

    @property
    def common_config(self) -> CommonConfig:
        if not self._common_config:
            self._common_config = CommonConfig()
        return self._common_config

    @property
    def cloud_config(self) -> CloudConfig:
        if not self._cloud_config:
            self._cloud_config = CloudConfig()
        return self._cloud_config
    
    def __init__(self, derived_arg_spec=None, bypass_checks=False, no_log=False,
                 check_invalid_arguments=None, mutually_exclusive=None, required_together=None,
                 required_one_of=None, add_file_common_args=False, supports_check_mode=False,
                 required_if=None, supports_tags=True, facts_module=False, skip_exec=False, is_ad_resource=False, **kwargs,):
        
        self._common_config = None
        self._cloud_config = None

        merged_arg_spec = dict()
        merged_arg_spec.update(COMMON_ARGS)

        if derived_arg_spec:
            merged_arg_spec["resource_config"].update(derived_arg_spec)

        self.argument_spec = merged_arg_spec

        super(AnsibleSharpAzureModule, self).__init__(
            argument_spec=merged_arg_spec,
            bypass_checks=bypass_checks,
            no_log=no_log,
            mutually_exclusive=mutually_exclusive,
            required_together=required_together,
            required_one_of=required_one_of,
            add_file_common_args=add_file_common_args,
            supports_check_mode=supports_check_mode,    
            **kwargs
        )

        self.state = self.params["state"]
        self.facts_module = facts_module

        self.result = dict(
            changed=False,
            failed=False,
            msg="",
            json=None
        )
        self.init_resource_config()

        self.credential_data, self.credential = self.get_azure_login_credential()

        self._resource_client = None
        self._storage_client = None



    @property
    def resource_message_id(self):
        return f"Resource group '{self.resource_config.resource_group_name}'; Subscription ID '{self.resource_config.subscription_id}'; Location '{self.resource_config.resource_location}':"

    @property
    def cloud_vars(self):
        return self.cloud_config.cloud_vars
    
    @property
    def common_vars(self):
        return self.common_config.common_vars
    
    @property
    def rm_client(self):
        self.log('Getting resource manager client')
        if not self._resource_client:
            self._resource_client = ResourceManagementClient(self.credential, self.resource_config.subscription_id)
        return self._resource_client

    @property
    def storage_client(self):
        self.log('Getting storage client...')
        if not self._storage_client:
            self._storage_client = StorageManagementClient(self.credential, self.resource_config.subscription_id, api_version="2023-01-01")
        return self._storage_client
    
    @property
    def storage_models(self):
        return StorageManagementClient.models("2023-01-01")

    def exec_module(self, **kwargs):
        if DEBUG:
            self.run()
        else:
            try:
                self.run()
            except Exception as e:
                self.result["failed"] = True
                self.result["msg"] = f"[Ansible-Sharp ERROR]: Failed to execute module: {e}"


    def run(self):
        raise NotImplementedError("[Ansible-Sharp ERROR]: You must implement the run method in your module")

    def exit_json(self, **kwargs):
        self.result.update(kwargs)
        super().exit_json(**self.result)

    def exit_fail(self, msg):
        self.result["failed"] = True
        self.result["msg"] = msg
        super().fail_json(**self.result)

    def exit_success(self, json=None):
        self.result["changed"] = True
        self.result["json"] = json
        super().exit_json(**self.result)

    def get_azure_login_credential(self):
        azure_login = self.params.get("azure_login", None)

        if azure_login != None:
            credential_data, credential = get_defaults_azure_login_credential(azure_login['azure_login_credential'])
        else:
            credential_data, credential = get_defaults_azure_login_credential()

        return credential_data, credential

    def init_resource_config(self):
        resource_config = self.params.get("resource_config", None)

        kind = resource_config.get("kind")
        if not kind:
            raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: kind is required")

        resource_default_values = self.cloud_vars["resources"][kind]
        if not resource_default_values:
            raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: Ansible Sharp Vars does not recognize the kind of resource")

        subscription_id = resource_config.get("subscription_id")
        if not subscription_id:
            raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: subscription_id is required")

        if not re.match(r'^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', subscription_id):
            raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: subscription_id is not a valid GUID")

        resource_location = resource_config.get("resource_location")
        if not resource_location:
            raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: resource_location is required")

        name = resource_config.get("name")
        if not name:
            raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: name is required")

        resource_group_name = resource_config.get("resource_group_name")
        if kind != "resource_group":
            if not resource_group_name:
                raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: resource_group_name is required")

        default_tags = resource_default_values.get("tags")
        current_tags = resource_config.get("tags")
        # Merge dict current_tags with default_tags
        tags = current_tags if current_tags else dict()
        tags.update(default_tags) 
        if not tags:
            raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: tags is required")
        else:
            self.validate_tags(tags)



        # assembly of the resource_config object
        for key in list(self.argument_spec["resource_config"].keys()):
            default_v = resource_default_values.get(key, None)
            value = resource_config.get(key, default_v)

            if hasattr(resource_config, key):
                setattr(resource_config, key, value)
            else:
                resource_config[key] = value

        #resource_config = merge_dict(resource_config, resource_default_values)
        
        # Create a namedtuple class with fields for each key in the dictionary
        ResourceConfig = namedtuple("ResourceConfig", resource_config.keys())

        # Create an instance of the Config class with values from the dictionary
        self.resource_config = ResourceConfig(**resource_config)


    def validate_tags(self, tags):
        '''
        Check if tags dictionary contains string:string pairs.

        :param tags: dictionary of string:string pairs
        :return: None
        '''
        if not self.facts_module:
            if not isinstance(tags, dict):
                self.exit_fail("Tags must be a dictionary of string:string values.")
            for key, value in tags.items():
                if not isinstance(value, str):
                    self.exit_fail("Tags values must be strings. Found {0}:{1}".format(str(key), str(value)))

    def update_tags(self, tags):
        '''
        Call from the module to update metadata tags. Returns tuple
        with bool indicating if there was a change and dict of new
        tags to assign to the object.

        :param tags: metadata tags from the object
        :return: bool, dict
        '''
        tags = tags or dict()
        new_tags = copy.copy(tags) if isinstance(tags, dict) else dict()
        param_tags = self.resource_config.tags if isinstance(self.resource_config.tags, dict) else dict()
        append_tags = self.resource_config.tags if self.resource_config.tags is not None else True
        changed = False
        # check add or update
        for key, value in param_tags.items():
            if not new_tags.get(key) or new_tags[key] != value:
                changed = True
                new_tags[key] = value
        # check remove
        if not append_tags:
            for key, value in tags.items():
                if not param_tags.get(key):
                    new_tags.pop(key)
                    changed = True
        return changed, new_tags

    def has_tags(self, obj_tags, tag_list):
        '''
        Used in fact modules to compare object tags to list of parameter tags. Return true if list of parameter tags
        exists in object tags.

        :param obj_tags: dictionary of tags from an Azure object.
        :param tag_list: list of tag keys or tag key:value pairs
        :return: bool
        '''

        if not obj_tags and tag_list:
            return False

        if not tag_list:
            return True

        matches = 0
        result = False
        for tag in tag_list:
            tag_key = tag
            tag_value = None
            if ':' in tag:
                tag_key, tag_value = tag.split(':')
            if tag_value and obj_tags.get(tag_key) == tag_value:
                matches += 1
            elif not tag_value and obj_tags.get(tag_key):
                matches += 1
        if matches == len(tag_list):
            result = True
        return result

    def get_resource_group(self, resource_group):
        '''
        Fetch a resource group.

        :param resource_group: name of a resource group
        :return: resource group object
        '''
        item = None
        result = None

        try:
            item = self.rm_client.resource_groups.get(resource_group)
        except ResourceNotFoundError as exc:
            return None

        result = self.serialize_obj(item, AZURE_RG_OBJECT_CLASS)

        return result

    def parse_resource_to_dict(self, resource):
        '''
        Return a dict of the give resource, which contains name and resource group.

        :param resource: It can be a resource name, id or a dict contains name and resource group.
        '''
        resource_dict = parse_resource_id(resource) if not isinstance(resource, dict) else resource
        resource_dict['resource_group'] = resource_dict.get('resource_group', self.resource_group)
        resource_dict['subscription_id'] = resource_dict.get('subscription_id', self.subscription_id)
        return resource_dict

    def serialize_obj(self, obj, class_name, enum_modules=None):
        '''
        Return a JSON representation of an Azure object.

        :param obj: Azure object
        :param class_name: Name of the object's class
        :param enum_modules: List of module names to build enum dependencies from.
        :return: serialized result
        '''
        return obj.as_dict()

    def get_poller_result(self, poller, wait=5):
        '''
        Consistent method of waiting on and retrieving results from Azure's long poller

        :param poller Azure poller object
        :return object resulting from the original request
        '''
        try:
            delay = wait
            while not poller.done():
                self.log("Waiting for {0} sec".format(delay))
                poller.wait(timeout=delay)
            return poller.result()
        except Exception as exc:
            self.log(str(exc))
            raise

    def get_multiple_pollers_results(self, pollers, wait=0.05):
        '''
        Consistent method of waiting on and retrieving results from multiple Azure's long poller

        :param pollers list of Azure poller object
        :param wait Period of time to wait for the long running operation to complete.
        :return list of object resulting from the original request
        '''

        def _continue_polling():
            return not all(poller.done() for poller in pollers)

        try:
            while _continue_polling():
                for poller in pollers:
                    if poller.done():
                        continue
                    self.log("Waiting for {0} sec".format(wait))
                    poller.wait(timeout=wait)
            return [poller.result() for poller in pollers]
        except Exception as exc:
            self.log(str(exc))
            raise
