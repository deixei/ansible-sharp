#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente
import os

from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.managementgroups import ManagementGroupsAPI as ManagementGroupsClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.cli.core.cloud import Cloud, AZURE_PUBLIC_CLOUD

from ansible_collections.ansiblesharp.az.plugins.module_utils.common import get_defaults_azure_login_credential

from ansible_collections.ansiblesharp.az.plugins.module_utils.cloud_config import CloudConfig
from ansible_collections.ansiblesharp.common.plugins.module_utils.common_config import CommonConfig

from collections import OrderedDict

class AzureCommonBase():
    @property
    def _cloud_environment(self) -> Cloud:
        return AZURE_PUBLIC_CLOUD
    
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

    def __init__(self, azure_login: dict = None):
        self._common_config = None
        self._cloud_config = None

        # Clients
        self._resource_client = OrderedDict()
        self._management_group_client = None
        self._subscription_client = None

        # Creds
        self.azure_login, self.credential = self.get_azure_login_credential(azure_login)

    def get_azure_login_credential(self, azure_login: dict = None):
        if azure_login != None:
            credential_data, credential = get_defaults_azure_login_credential(azure_login)
        else:
            credential_data, credential = get_defaults_azure_login_credential()

        return credential_data, credential
    
    def rm_client(self, subscription_id: str):
        if not self._resource_client.get(subscription_id):
            self._resource_client[subscription_id] = ResourceManagementClient(self.credential, subscription_id)
        return self._resource_client[subscription_id]
    
    @property
    def management_groups_client(self):
        if not self._management_group_client:
            self._management_group_client = ManagementGroupsClient(self.credential, base_url=self._cloud_environment.endpoints.resource_manager)
        return self._management_group_client
    
    @property
    def subscription_client(self):
        if not self._subscription_client:
            self._subscription_client = SubscriptionClient(self.credential, base_url=self._cloud_environment.endpoints.resource_manager)
        return self._subscription_client
     

class Resource(AzureCommonBase):
    def __init__(self, resource_name: str, resource_type: str, resource_location: str, azure_login: dict = None):
        super().__init__(azure_login)
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.resource_location = resource_location


    def get_properties(self):
        return {
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "resource_location": self.resource_location
        }
      

class ResourceGroup(AzureCommonBase):
    def __init__(self, 
                 subscription_id: str, 
                 resource_group_name: str, 
                 resource_group_location: str, 
                 azure_login: dict = None):
        
        super().__init__(azure_login)
        
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.resource_group_location = resource_group_location

        self._resources = OrderedDict()

    @property
    def resources(self):
        if not self._resources:
            self.load()

        return self._resources

    def load(self):
        resources = self.rm_client(self.subscription_id).resources.list_by_resource_group(self.resource_group_name)
        for resource in resources: 
            self.add_resource(Resource(
                resource.name, 
                resource.type, 
                resource.location,
                azure_login=self.azure_login))

    def add_resource(self, resource: Resource):
        self.resources[resource.resource_name] = resource

    def get_resource(self, resource_name: str):
        return self.resources[resource_name]

    def get_resources(self):
        return self.resources.values()

    def get_resource_names(self):
        return self.resources.keys()          

class Subscription(AzureCommonBase):
    def __init__(self, subscription_id: str, subscription_name: str, subscription_state: str, azure_login: dict = None):
        super().__init__(azure_login)
        self.subscription_id = subscription_id
        self.subscription_name = subscription_name
        self.subscription_state = subscription_state

        self._resource_groups = OrderedDict()

    @property
    def resource_groups(self):
        if not self._resource_groups:
            self.load()

        return self._resource_groups

    def load(self):
        # TODO: Load resource groups
        resource_groups = self.rm_client(self.subscription_id).resource_groups.list()
        for resource_group in resource_groups:
            self.add_resource_group(ResourceGroup(
                self.subscription_id,
                resource_group.name, 
                resource_group.location,
                azure_login=self.azure_login))
        

    def add_resource_group(self, resource_group: ResourceGroup):
        self.resource_groups[resource_group.resource_group_name] = resource_group
    
    def get_resource_group(self, resource_group_name: str):
        return self.resource_groups[resource_group_name]
    
    def get_resource_groups(self):
        return self.resource_groups.values()    
    
    def get_resource_group_names(self):
        return self.resource_groups.keys()

class Tenant(AzureCommonBase):
    def __init__(self, tenant_id: str, tenant_name: str, azure_login: dict = None):
        super().__init__(azure_login)
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name

        self._subscriptions = OrderedDict()

    @property
    def subscriptions(self):
        if not self._subscriptions:
            self.load()

        return self._subscriptions

    def load(self):
        for subscription in self.subscription_client.subscriptions.list():
            obj = Subscription(
                subscription_id=subscription.subscription_id, 
                subscription_name=subscription.display_name, 
                subscription_state=subscription.state,
                azure_login=self.azure_login)
            
            self.add_subscription(obj)

    def add_subscription(self, subscription: Subscription):
        self.subscriptions[subscription.subscription_id] = subscription

    def get_subscription(self, subscription_id: str):
        return self.subscriptions[subscription_id]
    
    def get_subscriptions(self):
        return self.subscriptions.values()
    
    def get_subscription_ids(self):
        return self.subscriptions.keys()




class AzureMapping(AzureCommonBase):

    def __init__(self, azure_login: dict = None):
        super().__init__(azure_login)

        self.tenant = Tenant(tenant_id=self.cloud_config.env_vars.tenant_id, tenant_name=self.cloud_config.env_vars.tenant_id, azure_login=azure_login)
        self.tenant.load()

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

