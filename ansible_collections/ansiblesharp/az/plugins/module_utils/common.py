#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente
import os
import hmac
from datetime import datetime
from azure.identity import ClientSecretCredential
from ansible_collections.ansiblesharp.az.plugins.module_utils.cloud_config import EnviromentVariables

try:
    from ansible.module_utils.ansible_release import __version__ as ANSIBLE_VERSION
except Exception:
    ANSIBLE_VERSION = 'unknown'

from collections.abc import MutableMapping

def merge_dict(dst, src):
    for k, v in src.items():
        if isinstance(v, MutableMapping):
            dst[k] = merge_dict(dst.get(k, {}), v)
        else:
            dst[k] = v
    return dst

AZURE_RG_OBJECT_CLASS = 'ResourceGroup'

AZURE_SUCCESS_STATE = "Succeeded"
AZURE_FAILED_STATE = "Failed"

ANSIBLE_USER_AGENT = 'AnsibleSharp/{0}'.format(ANSIBLE_VERSION)

COMMON_ARGS={
                "azure_login": {"type": "dict", "required": True},
                "state": {"type": "str", "choices": ["present", "absent"], "default": "present"},
                "resource_config": {
                    "type": "dict",
                    "required": True
                }
            }

def is_empty(value):
    """
    Check if a value is empty.

    Args:
        value: The value to check.

    Returns:
        True if the value is None or an empty string, False otherwise.
    """
    return value is None or value == ""

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
    env_var = EnviromentVariables()

    # Set default values for credential dictionary
    default_credential = {
        'token': "",
        'expires_on': 0,
        'credential': {
            'client_id': env_var.client_id,
            'client_secret': env_var.client_secret,
            'tenant_id': env_var.tenant_id        
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

