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


