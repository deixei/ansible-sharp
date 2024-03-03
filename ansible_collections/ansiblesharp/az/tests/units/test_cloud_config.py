#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

from ansible_collections.ansiblesharp.az.plugins.module_utils.cloud_config import CloudConfig

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

    def test_resoure_group_kind(self):
        resource_group = self.context.cloud_vars["resources"]['resource_group']
        self.assertEqual(resource_group['resource_location'], "westeurope")
        self.assertEqual(resource_group['tags']['CDK'], "AnsibleSharp")
        self.assertEqual(resource_group['kind'], "resource_group")

    def test_storage_account_kind(self):
        storage_account = self.context.cloud_vars["resources"]['storage_account']
        self.assertEqual(storage_account['resource_location'], "westeurope")
        self.assertEqual(storage_account['tags']['CDK'], "AnsibleSharp")
        self.assertEqual(storage_account['kind'], "storage_account")        