#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

import sys

sys.path.append('~/repos/deixei/ansible-sharp/')
from ansiblesharp.common.plugins.module_utils.base_config import BaseConfig

class Test_BaseConfig(unittest.TestCase):

    def setUp(self):
        self.context = BaseConfig()

    def test_2(self):
        data = self.context.data()
        self.assertEqual(data.common_vars.version, "1.0.0")
        self.assertEqual(data.common_vars.kind, "common_vars")

