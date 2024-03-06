#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

DEBUG=True

import time
import base64

from ansible.module_utils.basic import AnsibleModule

class AnsibleSharpModule(AnsibleModule):
    def __init__(self, argument_spec, supports_check_mode=False):
        super(AnsibleSharpModule, self).__init__(
            argument_spec=argument_spec,
            supports_check_mode=supports_check_mode
        )

        self.result = dict(
            changed=False,
            failed=False,
            msg="",
            data=None
        )

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