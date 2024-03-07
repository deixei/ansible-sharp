#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

from ansible_collections.ansiblesharp.az.plugins.module_utils.azure_common import AzureMapping, AzureCommonBase

class Test_AzureMapping(unittest.TestCase):

    def setUp(self):
        self.context = AzureMapping()

    def test_a_simple(self):
        self.context.tenant.load_subscriptions()

        l = self.context.tenant.subscriptions

        self.assertGreater(len(l), 0)

    def test_b_simple(self):
        self.context.tenant.load_managementgroups()

        l = self.context.tenant.managementgroups

        self.assertGreater(len(l), 0)

    def test_c_simple(self):
        self.context.tenant.load_subscriptions_by_managementgroup("development")

        l = self.context.tenant.subscriptions

        self.assertGreater(len(l), 0)

class Test_AzureCommonBase(unittest.TestCase):

    def setUp(self):
        self.context = AzureCommonBase()

    def test_run_query_simple(self):
        q = self.context.run_query("project id, tags, properties | limit 2")

        self.assertIsNotNone(q)
        self.assertGreater(q.count, 0)
