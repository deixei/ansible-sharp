#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

from ansible_collections.ansiblesharp.az.plugins.module_utils.azure_common import AzureMapping

class Test_AzureMapping(unittest.TestCase):

    def setUp(self):
        self.context = AzureMapping()

    def test_a_simple(self):
        self.context.print_tenant()
