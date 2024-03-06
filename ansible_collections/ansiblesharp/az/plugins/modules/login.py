#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente


from ansible.module_utils.basic import AnsibleModule
import os
import sys


from ansible_collections.ansiblesharp.az.plugins.module_utils import common
from ansible_collections.ansiblesharp.az.plugins.module_utils.cloud_config import EnviromentVariables


class Login(AnsibleModule):
    def __init__(self):
        env_vars = EnviromentVariables()
        super(Login, self).__init__(
            argument_spec={
                "client_id": {"type": "str", "default": env_vars.client_id},
                "client_secret": {"type": "str", "default": env_vars.client_secret},
                "tenant_id": {"type": "str", "default": env_vars.tenant_id},
                "azure_login_credential": {"type": "dict", "required": False},
            }
        )

        self.client_id = self.params["client_id"]
        self.client_secret = self.params["client_secret"]
        self.tenant_id = self.params["tenant_id"]

        self.result = dict(
            changed=False,
            client_id=self.client_id,
            client_secret=self.client_secret,
            tenant_id=self.tenant_id
        )

    def exec_module(self):

        azure_login_credential = {
            'token': "",
            'expires_on': 0,
            'credential': {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'tenant_id': self.tenant_id
            }
        }

        output_var, credential = common.get_defaults_azure_login_credential(azure_login_credential)

        self.exit_json(changed=False, azure_login_credential=output_var)


def main():
    my_module = Login()
    my_module.exec_module()


if __name__ == '__main__':
    main()
