#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import copy
from ansible_collections.ansiblesharp.az.plugins.module_utils.common import AnsibleSharpAzureModule, AZURE_SUCCESS_STATE
from ansible.module_utils._text import to_native

from azure.storage.blob import BlobServiceClient

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

        self.account_dict = None

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
            account_kind=dict(type='str', default='Storage', choices=['Storage', 'StorageV2', 'BlobStorage', 'FileStorage', 'BlockBlobStorage']),
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

        if self.resource_config.custom_domain:
            if self.resource_config.custom_domain.get('name', None) is None:
                self.exit_fail("Parameter error: expecting custom_domain to have a name attribute of type string.")
            if self.resource_config.custom_domain.get('use_sub_domain', None) is None:
                self.exit_fail("Parameter error: expecting custom_domain to have a use_sub_domain "
                          "attribute of type boolean.")

        if self.resource_config.account_kind in ['FileStorage', 'BlockBlobStorage', ] and self.resource_config.account_type not in ['Premium_LRS', 'Premium_ZRS']:
            self.exit_fail("Parameter error: Storage account with {0} account_kind require account type is Premium_LRS or Premium_ZRS".format(self.resource_config.account_kind))
        
        self.account_dict = self.get_account()

        if self.state == 'present' and self.account_dict and \
           self.account_dict['provisioning_state'] != AZURE_SUCCESS_STATE:
            self.exit_fail("Error: storage account {0} has not completed provisioning. State is {1}. Expecting state "
                      "to be {2}.".format(self.resource_config.name, self.account_dict['provisioning_state'], AZURE_SUCCESS_STATE))

        if self.account_dict is not None:
            self.result['json'] = self.account_dict
        else:
            self.result['json'] = dict()

        if self.state == 'present':
            if not self.account_dict:
                self.result['json'] = self.create_account()
            else:
                self.update_account()
        elif self.state == 'absent' and self.account_dict:
            self.delete_account()
            self.result['json'] = dict(Status='Deleted')
        elif self.state == 'failover' and self.account_dict:
            self.failover_account()
            self.result['json'] = self.get_account()
        
        self.exit_json(**self.result)
        
    def check_name_availability(self):
        self.log('Checking name availability for {0}'.format(self.resource_config.name))
        try:
            account_name = self.storage_models.StorageAccountCheckNameAvailabilityParameters(name=self.resource_config.name)
            self.storage_client.storage_accounts.check_name_availability(account_name)
        except Exception as e:
            self.log('Error attempting to validate name.')
            self.exit_fail("Error checking name availability: {0}".format(str(e)))

    def get_account(self):
        self.log('Get properties for account {0}'.format(self.resource_config.name))
        account_obj = None
        blob_mgmt_props = None
        blob_client_props = None
        account_dict = None

        try:
            account_obj = self.storage_client.storage_accounts.get_properties(self.resource_config.resource_group_name, self.resource_config.name)
            blob_mgmt_props = self.storage_client.blob_services.get_service_properties(self.resource_config.resource_group_name, self.resource_config.name)
            if self.resource_config.account_kind != "FileStorage":
                blob_client_props = self.get_blob_service_client(self.resource_config.resource_group_name, self.resource_config.name).get_service_properties()
        except Exception:
            pass

        if account_obj:
            account_dict = self.account_obj_to_dict(account_obj, blob_mgmt_props, blob_client_props)

        return account_dict

    def account_obj_to_dict(self, account_obj, blob_mgmt_props=None, blob_client_props=None):
        account_dict = dict(
            id=account_obj.id,
            name=account_obj.name,
            location=account_obj.location,
            failover_in_progress=(account_obj.failover_in_progress
                                  if account_obj.failover_in_progress is not None else False),
            resource_group=self.resource_config.resource_group_name,
            type=account_obj.type,
            access_tier=account_obj.access_tier,
            sku_tier=account_obj.sku.tier,
            sku_name=account_obj.sku.name,
            provisioning_state=account_obj.provisioning_state,
            secondary_location=account_obj.secondary_location,
            status_of_primary=account_obj.status_of_primary,
            status_of_secondary=account_obj.status_of_secondary,
            primary_location=account_obj.primary_location,
            https_only=account_obj.enable_https_traffic_only,
            minimum_tls_version=account_obj.minimum_tls_version,
            public_network_access=account_obj.public_network_access,
            allow_blob_public_access=account_obj.allow_blob_public_access,
            network_acls=account_obj.network_rule_set,
            is_hns_enabled=account_obj.is_hns_enabled if account_obj.is_hns_enabled else False,
            enable_nfs_v3=account_obj.enable_nfs_v3 if hasattr(account_obj, 'enable_nfs_v3') else None,
            large_file_shares_state=account_obj.large_file_shares_state,
            static_website=dict(
                enabled=False,
                index_document=None,
                error_document404_path=None,
            ),
        )
        account_dict['custom_domain'] = None
        if account_obj.custom_domain:
            account_dict['custom_domain'] = dict(
                name=account_obj.custom_domain.name,
                use_sub_domain=account_obj.custom_domain.use_sub_domain
            )

        account_dict['primary_endpoints'] = None
        if account_obj.primary_endpoints:
            account_dict['primary_endpoints'] = dict(
                blob=account_obj.primary_endpoints.blob,
                queue=account_obj.primary_endpoints.queue,
                table=account_obj.primary_endpoints.table
            )
        account_dict['secondary_endpoints'] = None
        if account_obj.secondary_endpoints:
            account_dict['secondary_endpoints'] = dict(
                blob=account_obj.secondary_endpoints.blob,
                queue=account_obj.secondary_endpoints.queue,
                table=account_obj.secondary_endpoints.table
            )
        account_dict['tags'] = None
        if account_obj.tags:
            account_dict['tags'] = account_obj.tags
        if blob_mgmt_props and blob_mgmt_props.cors and blob_mgmt_props.cors.cors_rules:
            account_dict['blob_cors'] = [dict(
                allowed_origins=[to_native(y) for y in x.allowed_origins],
                allowed_methods=[to_native(y) for y in x.allowed_methods],
                max_age_in_seconds=x.max_age_in_seconds,
                exposed_headers=[to_native(y) for y in x.exposed_headers],
                allowed_headers=[to_native(y) for y in x.allowed_headers]
            ) for x in blob_mgmt_props.cors.cors_rules]

        if blob_client_props and blob_client_props['static_website']:
            static_website = blob_client_props['static_website']
            account_dict['static_website'] = dict(
                enabled=static_website.enabled,
                index_document=static_website.index_document,
                error_document404_path=static_website.error_document404_path,
            )

        account_dict['network_acls'] = None
        if account_obj.network_rule_set:
            account_dict['network_acls'] = dict(
                bypass=account_obj.network_rule_set.bypass,
                default_action=account_obj.network_rule_set.default_action
            )
            account_dict['network_acls']['virtual_network_rules'] = []
            if account_obj.network_rule_set.virtual_network_rules:
                for rule in account_obj.network_rule_set.virtual_network_rules:
                    account_dict['network_acls']['virtual_network_rules'].append(dict(id=rule.virtual_network_resource_id, action=rule.action))

            account_dict['network_acls']['ip_rules'] = []
            if account_obj.network_rule_set.ip_rules:
                for rule in account_obj.network_rule_set.ip_rules:
                    account_dict['network_acls']['ip_rules'].append(dict(value=rule.ip_address_or_range, action=rule.action))
            account_dict['encryption'] = dict()
            if account_obj.encryption:
                account_dict['encryption']['require_infrastructure_encryption'] = account_obj.encryption.require_infrastructure_encryption
                account_dict['encryption']['key_source'] = account_obj.encryption.key_source
                if account_obj.encryption.services:
                    account_dict['encryption']['services'] = dict()
                    if account_obj.encryption.services.file:
                        account_dict['encryption']['services']['file'] = dict(enabled=True)
                    if account_obj.encryption.services.table:
                        account_dict['encryption']['services']['table'] = dict(enabled=True)
                    if account_obj.encryption.services.queue:
                        account_dict['encryption']['services']['queue'] = dict(enabled=True)
                    if account_obj.encryption.services.blob:
                        account_dict['encryption']['services']['blob'] = dict(enabled=True)

        return account_dict

    def get_blob_service_client(self, resource_group_name, storage_account_name):
        try:
            self.log("Getting storage account detail")
            account = self.storage_client.storage_accounts.get_properties(resource_group_name=resource_group_name, account_name=storage_account_name)
            account_keys = self.storage_client.storage_accounts.list_keys(resource_group_name=resource_group_name, account_name=storage_account_name)
        except Exception as exc:
            self.exit_fail("Error getting storage account detail for {0}: {1}".format(storage_account_name, str(exc)))

        try:
            self.log("Create blob service client")
            return BlobServiceClient(
                account_url=account.primary_endpoints.blob,
                credential=account_keys.keys[0].value,
            )
        except Exception as exc:
            self.exit_fail("Error creating blob service client for storage account {0} - {1}".format(storage_account_name, str(exc)))



    def failover_account(self):

        if str(self.account_dict['sku_name']) not in ["Standard_GZRS", "Standard_GRS", "Standard_RAGZRS", "Standard_RAGRS"]:
            self.exit_fail("Storage account SKU ({0}) does not support failover to a secondary region.".format(self.account_dict['sku_name']))
        try:
            account_obj = self.storage_client.storage_accounts.get_properties(self.resource_config.resource_group_name, self.resource_config.name, expand='georeplicationstats')
        except Exception as exc:
            self.exit_fail("Error occurred while acquiring geo-replication status. {0}".format(str(exc)))

        if account_obj.failover_in_progress:
            self.exit_fail("Storage account is already in process of failing over to secondary region.")

        if not account_obj.geo_replication_stats.can_failover:
            self.exit_fail("Storage account is unable to failover.  Secondary region has status of {0}".format(account_obj.geo_replication_stats.status))

        try:
            poller = self.storage_client.storage_accounts.begin_failover(self.resource_config.resource_group_name, self.resource_config.name)
            result = self.get_poller_result(poller)
        except Exception as exc:
            self.exit_fail("Error occured while attempting a failover operation. {0}".format(str(exc)))

        self.result['changed'] = True
        return result

    def update_network_rule_set(self):
        if not self.check_mode:
            try:
                parameters = self.storage_models.StorageAccountUpdateParameters(network_rule_set=self.resource_config.network_acls)
                self.storage_client.storage_accounts.update(self.resource_config.resource_group_name,
                                                            self.resource_config.name,
                                                            parameters)
            except Exception as exc:
                self.exit_fail("Failed to update account type: {0}".format(str(exc)))

    def sort_list_of_dicts(self, rule_set, dict_key):
        return sorted(rule_set, key=lambda i: i[dict_key])



    def update_account(self):
        self.log('Update storage account {0}'.format(self.resource_config.name))
        if self.resource_config.network_acls:
            if self.resource_config.network_acls.get('default_action', 'Allow') != self.account_dict['network_acls']['default_action']:
                self.result['changed'] = True
                self.account_dict['network_acls']['default_action'] = self.resource_config.network_acls['default_action']
                self.update_network_rule_set()

            if self.resource_config.network_acls.get('default_action', 'Allow') == 'Deny':
                if self.resource_config.network_acls['bypass'] != self.account_dict['network_acls']['bypass']:
                    self.result['changed'] = True
                    self.account_dict['network_acls']['bypass'] = self.resource_config.network_acls['bypass']
                    self.update_network_rule_set()

                if self.resource_config.network_acls.get('virtual_network_rules', None) is not None and self.account_dict['network_acls']['virtual_network_rules'] != []:
                    if self.sort_list_of_dicts(self.resource_config.network_acls['virtual_network_rules'], 'id') != \
                            self.sort_list_of_dicts(self.account_dict['network_acls']['virtual_network_rules'], 'id'):
                        self.result['changed'] = True
                        self.account_dict['network_acls']['virtual_network_rules'] = self.resource_config.network_acls['virtual_network_rules']
                        self.update_network_rule_set()
                if self.resource_config.network_acls.get('virtual_network_rules', None) is not None and self.account_dict['network_acls']['virtual_network_rules'] == []:
                    self.result['changed'] = True
                    self.update_network_rule_set()

                if self.resource_config.network_acls.get('ip_rules', None) is not None and self.account_dict['network_acls']['ip_rules'] != []:
                    if self.sort_list_of_dicts(self.resource_config.network_acls['ip_rules'], 'value') != \
                            self.sort_list_of_dicts(self.account_dict['network_acls']['ip_rules'], 'value'):
                        self.result['changed'] = True
                        self.account_dict['network_acls']['ip_rules'] = self.resource_config.network_acls['ip_rules']
                        self.update_network_rule_set()
                if self.resource_config.network_acls.get('ip_rules', None) is not None and self.account_dict['network_acls']['ip_rules'] == []:
                    self.result['changed'] = True
                    self.update_network_rule_set()

        if self.resource_config.enable_nfs_v3 is not None and bool(self.resource_config.enable_nfs_v3) != bool(self.account_dict.get('enable_nfs_v3')):
            self.result['changed'] = True
            self.account_dict['enable_nfs_v3'] = self.resource_config.enable_nfs_v3

        if self.resource_config.is_hns_enabled is not None and bool(self.resource_config.is_hns_enabled) != bool(self.account_dict.get('is_hns_enabled')):
            self.result['changed'] = True
            self.account_dict['is_hns_enabled'] = self.resource_config.is_hns_enabled
            if not self.check_mode:
                self.exit_fail("The is_hns_enabled parameter not support to update, from {0} to {1}".
                          format(bool(self.account_dict.get('is_hns_enabled')), self.resource_config.is_hns_enabled))

        if self.resource_config.https_only is not None and bool(self.resource_config.https_only) != bool(self.account_dict.get('https_only')):
            self.result['changed'] = True
            self.account_dict['https_only'] = self.resource_config.https_only
            if not self.check_mode:
                try:
                    parameters = self.storage_models.StorageAccountUpdateParameters(enable_https_traffic_only=self.resource_config.https_only)
                    self.storage_client.storage_accounts.update(self.resource_config.resource_group_name,
                                                                self.resource_config.name,
                                                                parameters)
                except Exception as exc:
                    self.exit_fail("Failed to update https only: {0}".format(str(exc)))

        if self.resource_config.minimum_tls_version is not None and self.resource_config.minimum_tls_version != self.account_dict.get('minimum_tls_version'):
            self.result['changed'] = True
            self.account_dict['minimum_tls_version'] = self.resource_config.minimum_tls_version
            if not self.check_mode:
                try:
                    parameters = self.storage_models.StorageAccountUpdateParameters(minimum_tls_version=self.resource_config.minimum_tls_version)
                    self.storage_client.storage_accounts.update(self.resource_config.resource_group_name,
                                                                self.resource_config.name,
                                                                parameters)
                except Exception as exc:
                    self.exit_fail("Failed to update minimum tls: {0}".format(str(exc)))

        if self.resource_config.public_network_access is not None and self.resource_config.public_network_access != self.account_dict.get('public_network_access'):
            self.result['changed'] = True
            self.account_dict['public_network_access'] = self.resource_config.public_network_access
            if not self.check_mode:
                try:
                    parameters = self.storage_models.StorageAccountUpdateParameters(public_network_access=self.resource_config.public_network_access)
                    self.storage_client.storage_accounts.update(self.resource_config.resource_group_name,
                                                                self.resource_config.name,
                                                                parameters)
                except Exception as exc:
                    self.exit_fail("Failed to update public network access: {0}".format(str(exc)))

        if self.resource_config.allow_blob_public_access is not None and self.resource_config.allow_blob_public_access != self.account_dict.get('allow_blob_public_access'):
            self.result['changed'] = True
            self.account_dict['allow_blob_public_access'] = self.resource_config.allow_blob_public_access
            if not self.check_mode:
                try:
                    parameters = self.storage_models.StorageAccountUpdateParameters(allow_blob_public_access=self.resource_config.allow_blob_public_access)
                    self.storage_client.storage_accounts.update(self.resource_config.resource_group_name,
                                                                self.resource_config.name,
                                                                parameters)
                except Exception as exc:
                    self.exit_fail("Failed to update allow public blob access: {0}".format(str(exc)))

        if self.resource_config.account_type:
            if self.resource_config.account_type != self.account_dict['sku_name']:
                # change the account type
                SkuName = self.storage_models.SkuName
                if self.account_dict['sku_name'] in [SkuName.premium_lrs, SkuName.standard_zrs]:
                    self.exit_fail("Storage accounts of type {0} and {1} cannot be changed.".format(
                        SkuName.premium_lrs, SkuName.standard_zrs))
                if self.resource_config.account_type in [SkuName.premium_lrs, SkuName.standard_zrs]:
                    self.exit_fail("Storage account of type {0} cannot be changed to a type of {1} or {2}.".format(
                        self.account_dict['sku_name'], SkuName.premium_lrs, SkuName.standard_zrs))

                self.result['changed'] = True
                self.account_dict['sku_name'] = self.resource_config.account_type

                if self.result['changed'] and not self.check_mode:
                    # Perform the update. The API only allows changing one attribute per call.
                    try:
                        self.log("sku_name: %s" % self.account_dict['sku_name'])
                        self.log("sku_tier: %s" % self.account_dict['sku_tier'])
                        sku = self.storage_models.Sku(name=SkuName(self.account_dict['sku_name']))
                        sku.tier = self.storage_models.SkuTier(self.account_dict['sku_tier'])
                        parameters = self.storage_models.StorageAccountUpdateParameters(sku=sku)
                        self.storage_client.storage_accounts.update(self.resource_config.resource_group_name,
                                                                    self.resource_config.name,
                                                                    parameters)
                    except Exception as exc:
                        self.exit_fail("Failed to update account type: {0}".format(str(exc)))

        if self.resource_config.custom_domain:
            if not self.account_dict['custom_domain'] or self.account_dict['custom_domain'] != self.resource_config.custom_domain:
                self.result['changed'] = True
                self.account_dict['custom_domain'] = self.resource_config.custom_domain

            if self.result['changed'] and not self.check_mode:
                new_domain = self.storage_models.CustomDomain(name=self.resource_config.custom_domain['name'],
                                                              use_sub_domain=self.resource_config.custom_domain['use_sub_domain'])
                parameters = self.storage_models.StorageAccountUpdateParameters(custom_domain=new_domain)
                try:
                    self.storage_client.storage_accounts.update(self.resource_config.resource_group_name, self.resource_config.name, parameters)
                except Exception as exc:
                    self.exit_fail("Failed to update custom domain: {0}".format(str(exc)))

        if self.resource_config.access_tier:
            if not self.account_dict['access_tier'] or self.account_dict['access_tier'] != self.resource_config.access_tier:
                self.result['changed'] = True
                self.account_dict['access_tier'] = self.resource_config.access_tier

            if self.result['changed'] and not self.check_mode:
                parameters = self.storage_models.StorageAccountUpdateParameters(access_tier=self.resource_config.access_tier)
                try:
                    self.storage_client.storage_accounts.update(self.resource_config.resource_group_name, self.resource_config.name, parameters)
                except Exception as exc:
                    self.exit_fail("Failed to update access tier: {0}".format(str(exc)))

        if self.resource_config.large_file_shares_state is not None:
            if self.resource_config.large_file_shares_state != self.account_dict['large_file_shares_state']:
                self.result['changed'] = True
                self.account_dict['large_file_shares_state'] = self.resource_config.large_file_shares_state

            if self.result['changed'] and not self.check_mode:
                if self.resource_config.large_file_shares_state == 'Disabled':
                    parameters = self.storage_models.StorageAccountUpdateParameters(large_file_shares_state=None)
                else:
                    parameters = self.storage_models.StorageAccountUpdateParameters(large_file_shares_state=self.resource_config.large_file_shares_state)
                try:
                    self.storage_client.storage_accounts.update(self.resource_config.resource_group_name, self.resource_config.name, parameters)
                except Exception as exc:
                    self.exit_fail("Failed to update large_file_shares_state: {0}".format(str(exc)))

        update_tags, self.account_dict['tags'] = self.update_tags(self.account_dict['tags'])
        if update_tags:
            self.result['changed'] = True
            if not self.check_mode:
                parameters = self.storage_models.StorageAccountUpdateParameters(tags=self.account_dict['tags'])
                try:
                    self.storage_client.storage_accounts.update(self.resource_config.resource_group_name, self.resource_config.name, parameters)
                except Exception as exc:
                    self.exit_fail("Failed to update tags: {0}".format(str(exc)))

        if self.resource_config.blob_cors and not compare_cors(self.account_dict.get('blob_cors', []), self.resource_config.blob_cors):
            self.result['changed'] = True
            if not self.check_mode:
                self.set_blob_cors()

        if self.resource_config.static_website and self.resource_config.static_website != self.account_dict.get("static_website", dict()):
            self.result['changed'] = True
            self.account_dict['static_website'] = self.resource_config.static_website
            self.update_static_website()

        if self.resource_config.encryption is not None:
            encryption_changed = False
            if self.resource_config.encryption.get('require_infrastructure_encryption') and bool(self.resource_config.encryption.get('require_infrastructure_encryption')) \
                    != bool(self.account_dict['encryption']['require_infrastructure_encryption']):
                encryption_changed = True

            if self.resource_config.encryption.get('key_source') != self.account_dict['encryption']['key_source']:
                encryption_changed = True

            if self.resource_config.encryption.get('services') is not None:
                if self.resource_config.encryption.get('queue') is not None and self.account_dict['encryption']['services'].get('queue') is not None:
                    encryption_changed = True
                if self.resource_config.encryption.get('file') is not None and self.account_dict['encryption']['services'].get('file') is not None:
                    encryption_changed = True
                if self.resource_config.encryption.get('table') is not None and self.account_dict['encryption']['services'].get('table') is not None:
                    encryption_changed = True
                if self.resource_config.encryption.get('blob') is not None and self.account_dict['encryption']['services'].get('blob') is not None:
                    encryption_changed = True

            if encryption_changed and not self.check_mode:
                self.exit_fail("The encryption can't update encryption, encryption info as {0}".format(self.account_dict['encryption']))

    def create_account(self):
        self.log("Creating account {0}".format(self.resource_config.name))

        if not self.resource_config.resource_location:
            self.exit_fail('Parameter error: location required when creating a storage account.')

        if not self.resource_config.account_type:
            self.exit_fail('Parameter error: account_type required when creating a storage account.')

        if not self.resource_config.access_tier and self.resource_config.account_kind == 'BlobStorage':
            self.exit_fail('Parameter error: access_tier required when creating a storage account of type BlobStorage.')

        self.check_name_availability()
        self.result['changed'] = True

        if self.check_mode:
            account_dict = dict(
                location=self.resource_config.resource_location,
                account_type=self.resource_config.account_type,
                name=self.resource_config.name,
                resource_group=self.resource_config.resource_group_name,
                enable_https_traffic_only=self.resource_config.https_only,
                minimum_tls_version=self.resource_config.minimum_tls_version,
                public_network_access=self.resource_config.public_network_access,
                allow_blob_public_access=self.resource_config.allow_blob_public_access,
                encryption=self.resource_config.encryption,
                is_hns_enabled=self.resource_config.is_hns_enabled,
                enable_nfs_v3=self.resource_config.enable_nfs_v3,
                large_file_shares_state=self.resource_config.large_file_shares_state,
                tags=dict()
            )
            if self.resource_config.tags:
                account_dict['tags'] = self.resource_config.tags
            if self.resource_config.network_acls:
                account_dict['network_acls'] = self.resource_config.network_acls
            if self.resource_config.blob_cors:
                account_dict['blob_cors'] = self.resource_config.blob_cors
            if self.resource_config.static_website:
                account_dict['static_website'] = self.resource_config.static_website
            return account_dict
        sku = self.storage_models.Sku(name=self.storage_models.SkuName(self.resource_config.account_type))
        sku.tier = self.storage_models.SkuTier.standard if 'Standard' in self.resource_config.account_type else \
            self.storage_models.SkuTier.premium
        # pylint: disable=missing-kwoa
        parameters = self.storage_models.StorageAccountCreateParameters(sku=sku,
                                                                        kind=self.resource_config.account_kind,
                                                                        location=self.resource_config.resource_location,
                                                                        tags=self.resource_config.tags,
                                                                        enable_https_traffic_only=self.resource_config.https_only,
                                                                        minimum_tls_version=self.resource_config.minimum_tls_version,
                                                                        public_network_access=self.resource_config.public_network_access,
                                                                        allow_blob_public_access=self.resource_config.allow_blob_public_access,
                                                                        encryption=self.resource_config.encryption,
                                                                        is_hns_enabled=self.resource_config.is_hns_enabled,
                                                                        enable_nfs_v3=self.resource_config.enable_nfs_v3,
                                                                        access_tier=self.resource_config.access_tier,
                                                                        large_file_shares_state=self.resource_config.large_file_shares_state)
        self.log(str(parameters))
        try:
            poller = self.storage_client.storage_accounts.begin_create(self.resource_config.resource_group_name, self.resource_config.name, parameters)
            self.get_poller_result(poller)
        except Exception as e:
            self.log('Error creating storage account.')
            self.exit_fail("Failed to create account: {0}".format(str(e)))
        if self.resource_config.network_acls:
            self.set_network_acls()
        if self.resource_config.blob_cors:
            self.set_blob_cors()
        if self.resource_config.static_website:
            self.update_static_website()
        return self.get_account()

    def delete_account(self):
        if self.account_dict['provisioning_state'] == self.storage_models.ProvisioningState.succeeded.value and \
           not self.resource_config.force_delete_nonempty and self.account_has_blob_containers():
            self.exit_fail("Account contains blob containers. Is it in use? Use the force_delete_nonempty option to attempt deletion.")

        self.log('Delete storage account {0}'.format(self.resource_config.name))
        self.result['changed'] = True
        if not self.check_mode:
            try:
                status = self.storage_client.storage_accounts.delete(self.resource_config.resource_group_name, self.resource_config.name)
                self.log("delete status: ")
                self.log(str(status))
            except Exception as e:
                self.exit_fail("Failed to delete the account: {0}".format(str(e)))
        return True

    def account_has_blob_containers(self):
        '''
        If there are blob containers, then there are likely VMs depending on this account and it should
        not be deleted.
        '''
        if self.resource_config.account_kind == "FileStorage":
            return False
        self.log('Checking for existing blob containers')
        blob_service = self.get_blob_service_client(self.resource_config.resource_group_name, self.resource_config.name)
        try:
            response = blob_service.list_containers()
        except Exception:
            # No blob storage available?
            return False

        if len(list(response)) > 0:
            return True
        return False

    def set_blob_cors(self):
        try:
            cors_rules = self.storage_models.CorsRules(cors_rules=[self.storage_models.CorsRule(**x) for x in self.resource_config.blob_cors])
            self.storage_client.blob_services.set_service_properties(self.resource_config.resource_group_name,
                                                                     self.resource_config.name,
                                                                     self.storage_models.BlobServiceProperties(cors=cors_rules))
        except Exception as exc:
            self.exit_fail("Failed to set CORS rules: {0}".format(str(exc)))

    def update_static_website(self):
        if self.resource_config.account_kind == "FileStorage":
            return
        try:
            self.get_blob_service_client(self.resource_config.resource_group_name, self.resource_config.name).set_service_properties(static_website=self.resource_config.static_website)
        except Exception as exc:
            self.exit_fail("Failed to set static website config: {0}".format(str(exc)))

    def set_network_acls(self):
        try:
            parameters = self.storage_models.StorageAccountUpdateParameters(network_rule_set=self.resource_config.network_acls)
            self.storage_client.storage_accounts.update(self.resource_config.resource_group_name,
                                                        self.resource_config.name,
                                                        parameters)
        except Exception as exc:
            self.exit_fail("Failed to update account type: {0}".format(str(exc)))

def main():
    my_module = StorageAccount()
    my_module.exec_module()

if __name__ == '__main__':
    main()    