#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import yaml
import os

from ansible.errors import AnsibleError
from jinja2 import Template

# using the cloud_vars.yaml file in vs code and copying the content to the CLOUD_VARS variable
CLOUD_VARS = '''
defaults:
  location: &location westeurope

  properties: &properties
    kind: ""
    name: ""
    resource_group_name: ""
    resource_location: *location
    subscription_id: "00000000-0000-0000-0000-000000000000"
    tags:
        CDK: AnsibleSharp
cloud_vars:
  version: 1.0.0
  kind: cloud_vars
  test_case1: "{{ defaults.location }}"
  resources:
    resource_group: 
      <<: *properties
      kind: resource_group
    storage_account: 
      <<: *properties
      kind: storage_account
      account_kind: "StorageV2"
      account_type: "Standard_LRS"
      access_tier: "Hot"
      minimum_tls_version: "TLS1_2"
      https_only: true
      public_network_access: "Enabled"
      allow_blob_public_access: false
      is_hns_enabled: true
      large_file_shares_state: "Disabled"
      enable_nfs_v3: false
      encryption:
        require_infrastructure_encryption: true
        key_source: "Microsoft.Storage"
        services:
          blob:
            enabled: true

'''

AZURE_CREDENTIAL_ENV_MAPPING = dict(
    client_id='AZURE_CLIENT_ID',
    secret='AZURE_SECRET',
    tenant='AZURE_TENANT',
    subscription_id='SUBSCRIPTION_ID'
)

class EnviromentVariables:
    def env_config(self, name, default=None):
        return os.environ.get(name, default),

    @property
    def subscription_id(self) -> str:
        return self.env_config(AZURE_CREDENTIAL_ENV_MAPPING.get('subscription_id', 'SUBSCRIPTION_ID'), '')

    @property
    def client_id(self) -> str:
        return self.env_config(AZURE_CREDENTIAL_ENV_MAPPING.get('client_id', 'AZURE_CLIENT_ID'), '')
    
    @property
    def client_secret(self) -> str:
        return self.env_config(AZURE_CREDENTIAL_ENV_MAPPING.get('secret', 'AZURE_SECRET'), '')

    @property
    def tenant_id(self) -> str:
        return self.env_config(AZURE_CREDENTIAL_ENV_MAPPING.get('tenant', 'AZURE_TENANT'), '')

class CloudConfig():
    """
    Class representing the Cloud Config.

    This class provides a way to load data from a YAML file and store it in the `data` property.

    Methods:
        data: Property method that returns the loaded data. If the data is not loaded yet, it calls the `get_data` method to load it.
        get_data: Method that loads the data from the YAML file and returns it.
    Examples:
        cloud_config = CloudConfig()
        cloud_config.data

        cloud_vars:
            version: 1.0.0
            kind: cloud_vars

        data['version'] # 1.0.0

    """

    @property
    def env_vars(self) -> EnviromentVariables:
        return EnviromentVariables()

    def __init__(self):
        self._data = {}
    
    @property
    def data(self):
        if not self._data:
            self._data = self.get_data()
        return self._data

    @property
    def cloud_vars(self):
        return self.data.get('cloud_vars', {})
    
    @property
    def defaults(self):
        return self.data.get('defaults', {})

    def get_data(self):
        data = {}
        try:
            variables = yaml.safe_load(CLOUD_VARS)
        except Exception as e:
            raise AnsibleError(f"[Ansible-Sharp ERROR]: Failed to load CLOUD_VARS: {e}")
        
        yaml_string = str(variables)
        # Create a template from the string
        template = Template(yaml_string)

        # Render the template with the variables
        rendered_string = template.render(variables)

        # Parse the rendered template as YAML
        #data = yaml.safe_load(rendered_string)
        data = list(yaml.full_load_all(rendered_string))

        return data[0]

        