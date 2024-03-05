#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible_collections.ansiblesharp.az.plugins.module_utils.az_cli_command import AzureCliCommand

from ansible.module_utils.basic import AnsibleModule
from ansible.errors import AnsibleModuleError

from ansible_collections.ansiblesharp.common.plugins.module_utils.ansible_sharp_module import AnsibleSharpModule
import json

class AzCliModule(AnsibleSharpModule):
    def __init__(self, **kwargs):
        super(AzCliModule, self).__init__(
            argument_spec={
                "cmd": {"type": "str", "required": True, "alias": "command"},
                "trace": {"type": "bool", "default": False},
            }
        )

        self._engine = AzureCliCommand()

        self.command = self.params["cmd"]
        self.trace_flag = self.params["trace"]

    def run(self):
        return_data = self._engine.run(self.command)

        if self.trace_flag:
            msg_str = json.dumps(return_data, indent=4)
            self.warn(msg_str)

        self.exit_success(return_data)

def main():
    my_module = AzCliModule()
    my_module.execute_module()

if __name__ == '__main__':
    main()    