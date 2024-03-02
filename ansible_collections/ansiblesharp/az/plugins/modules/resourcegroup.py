#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible_collections.ansiblesharp.az.plugins.module_utils.common import AnsibleSharpAzureModule


class ResourceGroup(AnsibleSharpAzureModule):
    def __init__(self, **kwargs):
        super(ResourceGroup, self).__init__(**kwargs)

    def run(self):
        pass


def main():
    my_module = ResourceGroup()
    my_module.exec_module()

if __name__ == '__main__':
    main()    