#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import time
import os
import re
import hmac
from datetime import datetime
from ansible.module_utils.basic import AnsibleModule
from ansible.errors import AnsibleModuleError
from collections import namedtuple
from azure.mgmt.resource import ResourceManagementClient
from azure.identity import ClientSecretCredential

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

def is_not_empty(value):
    """
    Check if a value is not empty.

    Args:
        value: The value to check.

    Returns:
        True if the value is not None and not an empty string, False otherwise.
    """
    return value is not None and value != ""

def get_defaults_azure_login_credential(azure_login_credential=None):
    """
    Returns a dictionary containing default values for Azure credentials,
    optionally updated with the values from the provided AzureLoginCredential object.

    :param azure_login_credential: An AzureLoginCredential object containing values to update defaults (optional).
    :return: A dictionary containing default values for Azure credentials.
    """
    # Set default values for credential dictionary
    default_credential = {
        'token': "",
        'expires_on': 0,
        'credential': {
            'client_id': os.environ.get(AZURE_CREDENTIAL_ENV_MAPPING.get('client_id', ''), ''),
            'client_secret': os.environ.get(AZURE_CREDENTIAL_ENV_MAPPING.get('secret', ''), ''),
            'tenant_id': os.environ.get(AZURE_CREDENTIAL_ENV_MAPPING.get('tenant', ''), '')
        }
    }

    # Update defaults with values from AzureLoginCredential object (if provided)
    if azure_login_credential:
        # Update token and expires_on values (if provided)
        token = azure_login_credential.get('token')
        expires_on = azure_login_credential.get('expires_on')

        if token and expires_on:
            current_time = datetime.now().timestamp()
            if expires_on > current_time:
                default_credential['token'] = token
                default_credential['expires_on'] = expires_on

        # Update credential dictionary values (if provided)
        credential = azure_login_credential.get('credential', default_credential['credential'])
        if credential:
            default_credential['credential']['client_id'] = credential.get('client_id', default_credential['credential']['client_id'])
            default_credential['credential']['client_secret'] = credential.get('client_secret', default_credential['credential']['client_secret'])
            default_credential['credential']['tenant_id'] = credential.get('tenant_id', default_credential['credential']['tenant_id'])

    # Check if credential values are empty
    if not all(default_credential['credential'].values()):
        raise ValueError("[Ansible-Sharp ERROR]: Azure credentials not set.")

    credential = ClientSecretCredential(
        client_id=default_credential['credential']['client_id'],
        client_secret=default_credential['credential']['client_secret'],
        tenant_id=default_credential['credential']['tenant_id']
    )

    if not hmac.compare_digest(default_credential.get('token', ''), '') or default_credential.get('expires_on', 0) == 0:
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
            json=None
        )

    @property
    def rm_client(self):
        self.log('Getting resource manager client')
        if not self._resource_client:
            self._resource_client = ResourceManagementClient(self.credential, self.resource_config.subscription_id)
        return self._resource_client

    def exec_module(self):
        try:
            self.run()
        except Exception as e:
            self.result["failed"] = True
            self.result["msg"] = f"[Ansible-Sharp ERROR]: Failed to execute module: {e}"
        #finally:
        #    self.exit_json(**self.result)

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

        tags = resource_config.get("tags")
        if not tags:
            raise AnsibleModuleError(message="[Ansible-Sharp ERROR]: tags is required")

        # Create a namedtuple class with fields for each key in the dictionary
        ResourceConfig = namedtuple("ResourceConfig", resource_config.keys())

        # Create an instance of the Config class with values from the dictionary
        self.resource_config = ResourceConfig(**resource_config)

