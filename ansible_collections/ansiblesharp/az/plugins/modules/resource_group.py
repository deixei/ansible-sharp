#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible_collections.ansiblesharp.az.plugins.module_utils.ansible_sharp_azure_module import AnsibleSharpAzureModule


class ResourceGroup(AnsibleSharpAzureModule):
    def __init__(self, **kwargs):
        super(ResourceGroup, self).__init__(**kwargs)

    def run(self):

        msg_prefix = f"Resource group '{self.resource_config.name}'; Subscription ID '{self.resource_config.subscription_id}'; Location '{self.resource_config.resource_location}':"

        if self.state == "present":
            # Create or update resource group if it doesn't exist
            resource_group_params = {'location': self.resource_config.resource_location, 'tags': self.resource_config.tags}
            try:
                
                action_result = self.rm_client.resource_groups.create_or_update(self.resource_config.name, resource_group_params)
                
                action_result_json = action_result.as_dict()

                self.result["msg"] = f"{msg_prefix} has been created."
                self.exit_success(json=action_result_json)
            except Exception as e:
                self.exit_fail(msg="[Ansible-Sharp ERROR]: Failed to create resource group: {}".format(e))

        elif self.state == "absent":
            # Delete resource group if it exists
            try:
                action_result = self.rm_client.resource_groups.begin_delete(self.resource_config.name)
                self.result["msg"] = f"{msg_prefix} has been deleted."
                self.exit_success()
            except Exception as e:
                self.exit_fail(msg="[Ansible-Sharp ERROR]: Failed to delete resource group: {}".format(e))
        else:
            self.exit_fail(msg="[Ansible-Sharp ERROR]: Invalid state: {}".format(self.state))

        self.exit_json(**self.result)
        


def main():
    my_module = ResourceGroup()
    my_module.exec_module()

if __name__ == '__main__':
    main()    