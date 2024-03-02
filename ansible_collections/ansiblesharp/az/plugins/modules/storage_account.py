#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible_collections.ansiblesharp.az.plugins.module_utils.common import AnsibleSharpAzureModule


class StorageAccount(AnsibleSharpAzureModule):
    def __init__(self, **kwargs):
        super(StorageAccount, self).__init__(**kwargs)

    def run(self):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, self.resource_config[key])

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        if len(self.name) < 3 or len(self.name) > 24:
            self.exit_fail("Parameter error: name length must be between 3 and 24 characters.")

        # TODO: all
        
        self.exit_json(**self.result)
        


def main():
    my_module = StorageAccount()
    my_module.exec_module()

if __name__ == '__main__':
    main()    