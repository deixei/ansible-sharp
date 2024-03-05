#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

from ansible_collections.ansiblesharp.az.plugins.module_utils.az_cli_command import AzureCliCommand

class Test_AzureCliCommand(unittest.TestCase):

    def setUp(self):
        self.context = AzureCliCommand()

    def test_a_simple(self):
        data = self.context.run("--version")

        errors = data.get("error", None)
        msg = data.get("msg", None)

        self.assertEqual(errors, None)

        self.assertGreater(len(msg), 0)