#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

from ansible_collections.ansiblesharp.common.plugins.module_utils.azure_devops import AzureDevOps

class Test_AzureDevOps_Base(unittest.TestCase):

    def setUp(self):
        self.context = AzureDevOps()

    def test_projects(self):
        data = self.context.get_projects()

        self.assertGreater(len(data), 1)

    def test_project(self):
        data = self.context.get_project("CloudManagement")

        self.assertEqual(data.name, "CloudManagement")

    def test_areas(self):
        data = self.context.get_areas("CloudManagement")

        self.assertGreater(len(data), 1)