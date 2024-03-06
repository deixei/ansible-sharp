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
                "query": {"type": "str"},
                "output": {"type": "str", "options": ["json", "yaml"], "default": "json"},
                "subscription": {"type": "str"}
            }
        )

        self._engine = AzureCliCommand()

        self.command = self.params["cmd"]
        self.trace_flag = self.params["trace"]
        self.query = self.params.get("query", None)
        self.output = self.params.get("output", None)
        self.subscription = self.params.get("subscription", None)

    def run(self):
        return_data = self._engine.run(cmd=self.command, output_format=self.output,query= self.query,subscription= self.subscription)

        if self.trace_flag:
            msg_str = json.dumps(return_data, indent=4)
            self.warn(msg_str)

        self.exit_success(return_data)

def main():
    my_module = AzCliModule()
    my_module.exec_module()

if __name__ == '__main__':
    main()    