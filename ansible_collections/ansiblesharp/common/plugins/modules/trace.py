#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente <ansible-sharp@deixei.com>

import sys

DOCUMENTATION = '''
---
module: trace
version_added: "1.0.0"
short_description: does a remote trace to whatever is registered
description:
    - Send a display information about the trace
author:
    - Marcio Parente
'''

EXAMPLES = '''
- name: send out a trace
  ansiblesharp.common.trace:
    title: "demo of this trace"
    event: "trace"
    data: "nothing more"

'''

RETURN = '''
start_info:
    description:
        - plug for all plays. Serves as a validator on integrity
    returned: always
    type: dict

'''
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansiblesharp.common.plugins.module_utils import common as Common
from ansible_collections.ansiblesharp.common.plugins.module_utils.common import AnsibleSharpModule

class Trace(AnsibleSharpModule):
    def __init__(self):
        super(Trace, self).__init__(
            argument_spec={
                "title": {"type": "str", "required": True},
                "event": {"type": "str", "required": True},
                "data": {"type": "str", "required": True}
            }
        )


        self.title = self.params["title"]
        self.event = self.params["event"].upper()
        self.data = self.params["data"]

        self.result = dict(
            changed=False,
            title=self.title,
            event=self.event,
            data=self.data,
            )

    def run(self):
        msg = f"[{self.event}]: {self.title}; Data: {self.data}"
        self.warn(msg)

        self.exit_json(**self.result)


def main():
    my_module = Trace()
    my_module.execute_module()

if __name__ == '__main__':
    main()
