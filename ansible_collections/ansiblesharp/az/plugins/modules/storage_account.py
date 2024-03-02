#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import copy
from ansible_collections.ansiblesharp.az.plugins.module_utils.common import AnsibleSharpAzureModule


cors_rule_spec = dict(
    allowed_origins=dict(type='list', elements='str', required=True),
    allowed_methods=dict(type='list', elements='str', required=True),
    max_age_in_seconds=dict(type='int', required=True),
    exposed_headers=dict(type='list', elements='str', required=True),
    allowed_headers=dict(type='list', elements='str', required=True),
)

static_website_spec = dict(
    enabled=dict(type='bool', default=False),
    index_document=dict(type='str'),
    error_document404_path=dict(type='str'),
)


file_spec = dict(
    enabled=dict(type='bool')
)


queue_spec = dict(
    enabled=dict(type='bool')
)


table_spec = dict(
    enabled=dict(type='bool')
)


blob_spec = dict(
    enabled=dict(type='bool')
)

def compare_cors(cors1, cors2):
    if len(cors1) != len(cors2):
        return False
    copy2 = copy.copy(cors2)
    for rule1 in cors1:
        matched = False
        for rule2 in copy2:
            if (rule1['max_age_in_seconds'] == rule2['max_age_in_seconds']
                    and set(rule1['allowed_methods']) == set(rule2['allowed_methods'])
                    and set(rule1['allowed_origins']) == set(rule2['allowed_origins'])
                    and set(rule1['allowed_headers']) == set(rule2['allowed_headers'])
                    and set(rule1['exposed_headers']) == set(rule2['exposed_headers'])):
                matched = True
                copy2.remove(rule2)
        if not matched:
            return False
    return True

class StorageAccount(AnsibleSharpAzureModule):
    def __init__(self, **kwargs):

        self.module_arg_spec = dict(
            account_type=dict(type='str',
                              choices=['Premium_LRS', 'Standard_GRS', 'Standard_LRS', 'Standard_RAGRS', 'Standard_ZRS', 'Premium_ZRS',
                                       'Standard_RAGZRS', 'Standard_GZRS'],
                              aliases=['type']),
            custom_domain=dict(type='dict', aliases=['custom_dns_domain_suffix']),
            location=dict(type='str'),
            name=dict(type='str', required=True),
            resource_group=dict(required=True, type='str', aliases=['resource_group_name']),
            state=dict(default='present', choices=['present', 'absent', 'failover']),
            force_delete_nonempty=dict(type='bool', default=False, aliases=['force']),
            tags=dict(type='dict'),
            kind=dict(type='str', default='Storage', choices=['Storage', 'StorageV2', 'BlobStorage', 'FileStorage', 'BlockBlobStorage']),
            access_tier=dict(type='str', choices=['Hot', 'Cool']),
            https_only=dict(type='bool'),
            minimum_tls_version=dict(type='str', choices=['TLS1_0', 'TLS1_1', 'TLS1_2']),
            public_network_access=dict(type='str', choices=['Enabled', 'Disabled']),
            allow_blob_public_access=dict(type='bool'),
            network_acls=dict(type='dict'),
            blob_cors=dict(type='list', options=cors_rule_spec, elements='dict'),
            static_website=dict(type='dict', options=static_website_spec),
            is_hns_enabled=dict(type='bool'),
            large_file_shares_state=dict(type='str', choices=['Enabled', 'Disabled']),
            enable_nfs_v3=dict(type='bool'),
            encryption=dict(
                type='dict',
                options=dict(
                    services=dict(
                        type='dict',
                        options=dict(
                            blob=dict(
                                type='dict',
                                options=blob_spec
                            ),
                            table=dict(
                                type='dict',
                                options=table_spec
                            ),
                            queue=dict(
                                type='dict',
                                options=queue_spec
                            ),
                            file=dict(
                                type='dict',
                                options=file_spec
                            )
                        )
                    ),
                    require_infrastructure_encryption=dict(type='bool'),
                    key_source=dict(type='str', choices=["Microsoft.Storage", "Microsoft.Keyvault"], default='Microsoft.Storage')
                )
            )
        )


        self.config_spec = dict(
            account_dict=None
        )

        self.config_spec['account_dict'] = None

        super(StorageAccount, self).__init__(
            derived_arg_spec=self.module_arg_spec,
            **kwargs)

    def run(self):


        resource_group = self.get_resource_group(self.resource_config.resource_group_name)

        if resource_group is None:
            self.exit_fail(f"Resource group not found. {self.resource_message_id}")

        if not self.resource_config.resource_location:
            # Set default location
            self.resource_config.resource_location = resource_group.location

        if len(self.resource_config.name) < 3 or len(self.resource_config.name) > 24:
            self.exit_fail("Parameter error: name length must be between 3 and 24 characters.")

        # TODO: all
        
        self.exit_json(**self.result)
        


def main():
    my_module = StorageAccount()
    my_module.exec_module()

if __name__ == '__main__':
    main()    