#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente
import os
from typing import Dict, List, Optional, Union
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.managementgroups import ManagementGroupsAPI as ManagementGroupsClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.cli.core.cloud import Cloud, AZURE_PUBLIC_CLOUD
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import *
from collections import namedtuple
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
    
    def get_management_groups(self):
        return self.run_query("managementgroups | project id, displayName, type, tenantId, details | limit 2")

    def run_query(self,
            query: str,
            subscriptions: Optional[List[str]] = None,
            management_groups: Optional[List[str]] = None):
        
        resourcegraph_client = ResourceGraphClient(
            credential=self.credential
        )
        # Basic query up to 2 pieces of object array
        query = QueryRequest(
                query=query,
                subscriptions=subscriptions,
                management_groups=management_groups,
                options=QueryRequestOptions(
                    result_format=ResultFormat.object_array
                )
            )
        query_response = resourcegraph_client.resources(query)
   
        return query_response

    def run_query_named(self,
            name: str,
            query: str,
            subscriptions: Optional[List[str]] = None,
            management_groups: Optional[List[str]] = None,):

        query_return_data = self.run_query(query, subscriptions, management_groups).data

        res = list()
        for item in query_return_data:
            Item = namedtuple(name, item.keys())
            data_object = Item(**item)
            res.append(data_object)
    
        return res
    

class Resource(AzureCommonBase):
    def __init__(self, resource_name: str, resource_type: str, resource_location: str, azure_login: dict = None):
        super().__init__(azure_login)
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.resource_location = resource_location


    def get_properties(self):
        q = '''resources
                | where name == "{self.resource_name}" and location == "{self.resource_location}"
            '''
        return self.run_query(q).data
      

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
    def __init__(self, id: str, name: str, subscription_id: str, subscription_object: dict, azure_login: dict = None):
        super().__init__(azure_login)
        self.subscription_id = subscription_id
        self.name = name
        self.id = id

        self.object = subscription_object

        self.resource_groups = OrderedDict()

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

        self.subscriptions = list()
        self.managementgroups = list()

    def load_managementgroups(self):
        query = '''resourcecontainers
                | where type == "microsoft.management/managementgroups"
            '''
        self.managementgroups = self.run_query_named("ManagementGroup", query)


    def load_subscriptions(self):
        query = '''resourcecontainers
                | where type == "microsoft.resources/subscriptions"
                | project name, id, subscriptionId, properties, ['tags']
                | sort by name asc
            '''
        self.subscriptions = self.run_query_named("Subscription", query)


    def load_subscriptions_by_managementgroup(self, managementgroup_name: str):
        query = f'''resourcecontainers
                | where type == 'microsoft.resources/subscriptions'
                | mv-expand managementGroupParent = properties.managementGroupAncestorsChain
                | where managementGroupParent.name =~ '{managementgroup_name}'
                | project name, id, subscriptionId, properties, ['tags']
                | sort by name asc
            '''
        self.subscriptions = self.run_query_named("Subscription", query)


    def get_subscription(self, subscription_id: str):
        return [subscription for subscription in self.subscriptions if subscription.subscription_id == subscription_id][0]
    
    def get_subscription_ids(self):
        return self.subscriptions.keys()




class AzureMapping(AzureCommonBase):

    def __init__(self, azure_login: dict = None):
        super().__init__(azure_login)

        self.tenant = Tenant(tenant_id=self.cloud_config.env_vars.tenant_id, tenant_name=self.cloud_config.env_vars.tenant_id, azure_login=azure_login)

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



class AzureResourceGraph():
    def __init__(self, azure_login: dict = None):
        self.azure_login = azure_login

    