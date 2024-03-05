#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible_collections.ansiblesharp.az.plugins.module_utils.ansible_sharp_azure_module import AnsibleSharpAzureModule

AZURE_OBJECT_CLASS = 'ResourceGroup'

from azure.core.exceptions import ResourceNotFoundError

class ResourceGroup(AnsibleSharpAzureModule):
    def __init__(self, **kwargs):
        super(ResourceGroup, self).__init__(**kwargs)

    def run(self):

        msg_prefix = f"Resource group '{self.resource_config.name}'; Subscription ID '{self.resource_config.subscription_id}'; Location '{self.resource_config.resource_location}':"
        try:
            result = self.get_item()

            self.result["msg"] = f"{msg_prefix} has found."
            self.exit_success(json=result)
        except Exception as e:
            self.result["msg"] = f"{msg_prefix} has not found."
            self.exit_fail(msg="[Ansible-Sharp ERROR]: Failed to find resource group: {}; info: {}".format(e, msg_prefix))

    def get_item(self):
        self.log('Get properties for {0}'.format(self.resource_config.name))
        item = None
        result = []

        try:
            item = self.rm_client.resource_groups.get(self.resource_config.name)
        except ResourceNotFoundError:
            pass

        result = [self.serialize_obj(item, AZURE_OBJECT_CLASS)]

        return result
    
def main():
    my_module = ResourceGroup()
    my_module.exec_module()

if __name__ == '__main__':
    main()        