#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente
import os
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from ansible_collections.ansiblesharp.common.plugins.module_utils.common_config import CommonConfig

class AzureDevOps():
    @property
    def common_vars(self):
        return self._config.common_vars
        
    def __init__(self, organization=None, personal_access_token=None):
        
        self._config = CommonConfig()

        if not organization:
            self.organization = self._config.common_vars["central_data"]["ado_organization"]
        else:
            self.organization = organization
        
        if not personal_access_token:
            self.personal_access_token = os.environ.get('AZURE_DEVOPS_EXT_PAT')
        else:
            self.personal_access_token = personal_access_token

        self._connection = None
        self._core_client = None
        self._git_client = None
        self._build_client = None
        self._release_client = None
        self._task_agent_client = None
        self._test_client = None
        self._policy_client = None

    @property
    def connection(self):
        if not self._connection:
            self._connection = self.get_connection()
        return self._connection

    def get_connection(self):
        # Create a connection to the org
        credentials = BasicAuthentication('', self.personal_access_token)
        organization_url = f"https://dev.azure.com/{self.organization}"
        connection = Connection(base_url=organization_url, creds=credentials)

        return connection

    @property
    def core_client(self):
        if not self._core_client:
            self._core_client = self.get_core_client()
        return self._core_client
    
    @property
    def git_client(self):
        if not self._git_client:
            self._git_client = self.get_git_client()
        return self._git_client
    
    @property
    def build_client(self):
        if not self._build_client:
            self._build_client = self.get_build_client()
        return self._build_client
    
    @property
    def release_client(self):
        if not self._release_client:
            self._release_client = self.get_release_client()
        return self._release_client
    
    @property
    def task_agent_client(self):
        if not self._task_agent_client:
            self._task_agent_client = self.get_task_agent_client()
        return self._task_agent_client
    
    @property
    def test_client(self):
        if not self._test_client:
            self._test_client = self.get_test_client()
        return self._test_client
    
    @property
    def policy_client(self):
        if not self._policy_client:
            self._policy_client = self.get_policy_client()
        return self._policy_client
    

    def get_core_client(self):
        client = self.connection.clients.get_core_client()
        return client
    
    def get_git_client(self):
        client = self.connection.clients.get_git_client()
        return client

    def get_build_client(self):
        client = self.connection.clients.get_build_client()
        return client
    
    def get_release_client(self):
        client = self.connection.clients.get_release_client()
        return client
    
    def get_task_agent_client(self):
        client = self.connection.clients.get_task_agent_client()
        return client
    
    def get_test_client(self):  
        client = self.connection.clients.get_test_client()
        return client
    
    def get_policy_client(self):
        client = self.connection.clients.get_policy_client()
        return client   
    
    def get_projects(self):
        # Get the first page of projects
        get_projects_response = self.core_client.get_projects()
        return get_projects_response
    
    def get_project(self, project_name):
        get_projects_response = self.core_client.get_project(project_id = project_name)

        return get_projects_response
    
    def get_repos(self, project_id):
        repos = self.git_client.get_repositories(project_id)

        return 

    def create_work_item(self, project_id, work_item):
        work_item = self.core_client.create_work_item(project_id, work_item)

        return work_item