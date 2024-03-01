#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

from ansible_collections.ansiblesharp.common.plugins.module_utils.base_config import BaseConfig

class Test_BaseConfig(unittest.TestCase):

    def setUp(self):
        self.context = BaseConfig()

    def test_data_foundation(self):
        data = self.context.data
        self.assertEqual(data['common_vars']['version'], "1.0.0")
        self.assertEqual(data['common_vars']['kind'], "common_vars")

    def test_validate_stage(self):
        value = self.context.validate_stage("d")

        self.assertEqual(value, True)

    def test_validate_invalid_stage(self):
        value = self.context.validate_stage("n")

        self.assertEqual(value, False)
