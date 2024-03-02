#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente



from ansible.module_utils.basic import AnsibleModule

class AnsibleSharpAzureModule(AnsibleModule):
    def __init__(self, argument_spec, supports_check_mode=False):
        super(AnsibleSharpAzureModule, self).__init__(
            argument_spec=argument_spec,
            supports_check_mode=supports_check_mode
        )

        self.result = dict(
            changed=False,
            failed=False,
            msg="",
            data=None
        )

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