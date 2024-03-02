#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import time
import os
import re
from ansible.module_utils.basic import AnsibleModule
from collections import namedtuple
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient


COMMON_ARGS={
                "azure_login": {"type": "dict", "required": True},
                "state": {"type": "str", "choices": ["present", "absent"], "default": "present"},
                "resource_config": {
                    "type": "dict",
                    "required": True
                }
            }

AZURE_CREDENTIAL_ENV_MAPPING = dict(
    client_id='AZURE_CLIENT_ID',
    secret='AZURE_SECRET',
    tenant='AZURE_TENANT'
)

def get_defaults_azure_login_credential(azure_login_credential=None):
    """
    Returns a dictionary containing default values for Azure credentials,
    optionally updated with the values from the provided AzureLoginCredential object.

    :param azure_login_credential: An AzureLoginCredential object containing values to update defaults (optional).
    :return: A dictionary containing default values for Azure credentials.
    """
    renew_token = False

    # Set default values for credential dictionary
    default_credential = {
        'token': "",
        'expires_on': 0,
        'credential': {
            'client_id': os.environ.get('AZURE_CLIENT_ID', ''),
            'client_secret': os.environ.get('AZURE_SECRET', ''),
            'tenant_id': os.environ.get('AZURE_TENANT', '')
        }
    }

    # Update defaults with values from AzureLoginCredential object (if provided)
    if azure_login_credential != None:

        # Update token and expires_on values (if provided)
        if azure_login_credential['token'] is not None and azure_login_credential['token'] != "":
            default_credential['token'] = azure_login_credential['token']

        if azure_login_credential['expires_on'] != 0:
            default_credential['expires_on'] = azure_login_credential['expires_on']
            # Get the current time in seconds
            current_time = time.time()

            # Check if `expires_on` has expired
            if default_credential.get("expires_on", 0) < current_time:
                # Token has expired, renew it
                renew_token = True

        # Update credential dictionary values (if provided)
        if azure_login_credential['credential'] != None:

            if azure_login_credential['credential']['client_id']:
                default_credential['credential']['client_id'] = azure_login_credential['credential']['client_id']

            if azure_login_credential['credential']['client_secret']:
                default_credential['credential']['client_secret'] = azure_login_credential['credential']['client_secret']

            if azure_login_credential['credential']['tenant_id']:
                default_credential['credential']['tenant_id'] = azure_login_credential['credential']['tenant_id']

    # Check if credential values are empty
    if not default_credential['credential']['client_id'] or not default_credential['credential']['client_secret'] or not default_credential['credential']['tenant_id']:
        raise ValueError("Azure credentials not set.")

    credential = ClientSecretCredential(
        client_id=default_credential['credential']['client_id'],
        client_secret=default_credential['credential']['client_secret'],
        tenant_id=default_credential['credential']['tenant_id']
    )

    if renew_token==True or default_credential.get("expires_on", 0) == 0:

        token = credential.get_token("https://management.azure.com/.default")

        default_credential['token'] = token.token
        default_credential['expires_on'] = token.expires_on


    return default_credential, credential


class AnsibleSharpAzureModule(AnsibleModule):
    def __init__(self, supports_check_mode=False, **kwargs,):
        merged_arg_spec = dict()
        merged_arg_spec.update(COMMON_ARGS)

        self.argument_spec = merged_arg_spec

        super(AnsibleSharpAzureModule, self).__init__(
            argument_spec=merged_arg_spec,
            supports_check_mode=supports_check_mode,
            **kwargs
        )

        self.state = self.params["state"]

        self.init_resource_config()

        self.credential_data, self.credential = self.get_azure_login_credential()

        self._resource_client = None        

        self.result = dict(
            changed=False,
            failed=False,
            msg="",
            data=None
        )

    @property
    def rm_client(self):
        self.log('Getting resource manager client')
        if not self._resource_client:
            self._resource_client = ResourceManagementClient(self.credential, self.resource_config.subscription_id)
        return self._resource_client

    def execute_module(self):
        try:
            self.run()
        except Exception as e:
            self.result["failed"] = True
            self.result["msg"] = f"Failed to execute module: {e}"
        finally:
            self.exit_json(**self.result)

    def run(self):
        raise NotImplementedError("You must implement the run method in your module")

    def exit_json(self, **kwargs):
        self.result.update(kwargs)
        super().exit_json(**self.result)

    def exit_fail(self, msg):
        self.result["failed"] = True
        self.result["msg"] = msg
        super().fail_json(**self.result)

    def exit_success(self, data=None):
        self.result["changed"] = True
        self.result["data"] = data
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

        subscription_id = resource_config.get("subscription_id")
        if not subscription_id:
            self.exit_fail(msg="subscription_id is required")

        if not re.match(r'^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', subscription_id):
            self.exit_fail(msg="subscription_id is not a valid GUID")

        resource_location = resource_config.get("resource_location")
        if not resource_location:
            self.exit_fail(msg="resource_location is required")

        name = resource_config.get("name")
        if not name:
            self.exit_fail(msg="name is required")

        resource_group_name = resource_config.get("resource_group_name")
        if not resource_group_name:
            self.exit_fail(msg="resource_group_name is required")

        tags = resource_config.get("tags")
        if not tags:
            self.exit_fail(msg="tags is required")

        # Create a namedtuple class with fields for each key in the dictionary
        ResourceConfig = namedtuple("ResourceConfig", resource_config.keys())

        # Create an instance of the Config class with values from the dictionary
        self.resource_config = ResourceConfig(**resource_config)

