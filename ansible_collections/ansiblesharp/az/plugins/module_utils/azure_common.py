#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente
import os

from azure.mgmt.resource import ResourceManagementClient
from ansible_collections.ansiblesharp.az.plugins.module_utils.common import get_defaults_azure_login_credential

from ansible_collections.ansiblesharp.az.plugins.module_utils.cloud_config import CloudConfig
from ansible_collections.ansiblesharp.common.plugins.module_utils.common_config import CommonConfig
from collections import OrderedDict

class Resource():
    def __init__(self, resource_name: str, resource_type: str, resource_location: str):
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.resource_location = resource_location

      

class ResourceGroup:
    def __init__(self, resource_group_name: str, resource_group_location: str):
        self.resource_group_name = resource_group_name
        self.resource_group_location = resource_group_location

        self.resources = OrderedDict()

    def add_resource(self, resource: Resource):
        self.resources[resource.resource_name] = resource

    def get_resource(self, resource_name: str):
        return self.resources[resource_name]

    def get_resources(self):
        return self.resources.values()

    def get_resource_names(self):
        return self.resources.keys()          

class Subscription:
    def __init__(self, subscription_id: str, subscription_name: str, subscription_state: str):
        self.subscription_id = subscription_id
        self.subscription_name = subscription_name
        self.subscription_state = subscription_state

        self.resource_groups = OrderedDict()

    def add_resource_group(self, resource_group: ResourceGroup):
        self.resource_groups[resource_group.resource_group_name] = resource_group
    
    def get_resource_group(self, resource_group_name: str):
        return self.resource_groups[resource_group_name]
    
    def get_resource_groups(self):
        return self.resource_groups.values()    
    
    def get_resource_group_names(self):
        return self.resource_groups.keys()

class Tenant:
    def __init__(self, tenant_id: str, tenant_name: str):
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name

        self.subscriptions = OrderedDict()

    def add_subscription(self, subscription: Subscription):
        self.subscriptions[subscription.subscription_id] = subscription

    def get_subscription(self, subscription_id: str):
        return self.subscriptions[subscription_id]
    
    def get_subscriptions(self):
        return self.subscriptions.values()
    
    def get_subscription_ids(self):
        return self.subscriptions.keys()
    





class AzureCommon():

    @property
    def common_config(self) -> CommonConfig:
        if not self._common_config:
            self._common_config = CommonConfig()
        return self._common_config

    @property
    def cloud_config(self) -> CloudConfig:
        if not self._cloud_config:
            self._cloud_config = CloudConfig()
        return self._cloud_config

    @property
    def rm_client(self):
        if not self._resource_client:
            self._resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        return self._resource_client


    def __init__(self, azure_login: dict = None, subscription_id: str = None):
        self.tenant = Tenant()
        
        self.tenant.tenant_id = self.cloud_config.env_vars.tenant_id
        self.tenant.tenant_name = self.cloud_config.env_vars.tenant_id

        self._common_config = None
        self._cloud_config = None

        self._resource_client = None

        self.azure_login, self.credential = self.get_azure_login_credential(azure_login)

        if subscription_id == None:
            self.subscription_id = self.cloud_config.env_vars.subscription_id
        else:
            self.subscription_id = subscription_id

        self.tenant.add_subscription(Subscription(self.subscription_id, self.subscription_id, "Enabled"))


    def get_azure_login_credential(self, azure_login: dict = None):
        if azure_login != None:
            credential_data, credential = get_defaults_azure_login_credential(azure_login['azure_login_credential'])
        else:
            credential_data, credential = get_defaults_azure_login_credential()

        return credential_data, credential

    def get_resource_groups(self):
        resource_groups = self.rm_client.resource_groups.list()
        return resource_groups

    def get_resources(self, resource_group_name: str):
        resources = self.rm_client.resources.list_by_resource_group(resource_group_name)
        return resources

    def get_all_resources(self):
        resources = self.rm_client.resources.list()
        return resources


    def print_tenant(self):
        for subscription in self.tenant.get_subscriptions():
            print(f"Subscription: {subscription.subscription_id}")
            for resource_group in subscription.get_resource_groups():
                print(f"Resource Group: {resource_group.resource_group_name}")
                for resource in resource_group.get_resources():
                    print(f"Resource: {resource.resource_name}")
                    print(f"Resource Type: {resource.resource_type}")
                    print(f"Resource Location: {resource.resource_location}")
                    print("")

                    