#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

from ansible_collections.ansiblesharp.az.plugins.module_utils.cloud_config import CloudConfig, EnviromentVariables

class Test_CloudConfig(unittest.TestCase):

    def setUp(self):
        self.context = CloudConfig()

    def test_data_foundation(self):
        data = self.context.data
        self.assertEqual(data['cloud_vars']['version'], "1.0.0")
        self.assertEqual(data['cloud_vars']['kind'], "cloud_vars")

    def test_cloud_vars_foundation(self):
        cloud_vars = self.context.cloud_vars
        self.assertEqual(cloud_vars['version'], "1.0.0")
        self.assertEqual(cloud_vars['kind'], "cloud_vars")
    
    def test_defaults_foundation(self):
        defaults = self.context.defaults
        self.assertEqual(defaults['location'], "westeurope")

    def test_resource_group_kind(self):
        resource_group = self.context.cloud_vars["resources"]['resource_group']
        self.assertEqual(resource_group['resource_location'], "westeurope")
        self.assertEqual(resource_group['tags']['CDK'], "AnsibleSharp")
        self.assertEqual(resource_group['kind'], "resource_group")

    def test_storage_account_kind(self):
        storage_account = self.context.cloud_vars["resources"]['storage_account']
        self.assertEqual(storage_account['resource_location'], "westeurope")
        self.assertEqual(storage_account['tags']['CDK'], "AnsibleSharp")
        self.assertEqual(storage_account['kind'], "storage_account")        

    def test_env_vars_has_data(self):
        self.assertNotEqual(self.context.env_vars, None)

    def test_env_vars_tenant_id_is_string(self):
        self.assertIsInstance(self.context.env_vars.tenant_id, str)

class Test_EnviromentVariables(unittest.TestCase):

    def setUp(self):
        self.context = EnviromentVariables()

    def test_env_vars_tenant_id_is_string(self):
        self.assertIsInstance(self.context.tenant_id, str)

    def test_env_vars_client_id_is_string(self):
        self.assertIsInstance(self.context.client_id, str)
    
    def test_env_vars_client_secret_is_string(self):
        self.assertIsInstance(self.context.client_secret, str)