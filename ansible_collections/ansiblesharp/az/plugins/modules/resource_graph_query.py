#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible_collections.ansiblesharp.common.plugins.module_utils.ansible_sharp_module import AnsibleSharpModule
from ansible_collections.ansiblesharp.az.plugins.module_utils.azure_common import AzureCommonBase

class ResourceGraphQuery(AnsibleSharpModule):
    def __init__(self, **kwargs):
        self.argument_spec = dict(
            query=dict(type='str', required=True),
            subscriptions=dict(type='list', elements='str'),
            management_groups=dict(type='list', elements='str')
        )

        super(ResourceGraphQuery, self).__init__(
            argument_spec=self.argument_spec,
            **kwargs)
        
        self.query = self.params["query"]
        self.subscriptions = self.params.get("subscriptions", [])
        self.management_groups = self.params.get("management_groups", [])


    def run(self):
        base = AzureCommonBase()

        query_data = base.run_query(self.query, self.subscriptions, self.management_groups)

        self.exit_success(query_data.data)
        


def main():
    my_module = ResourceGraphQuery()
    my_module.exec_module()

if __name__ == '__main__':
    main()        