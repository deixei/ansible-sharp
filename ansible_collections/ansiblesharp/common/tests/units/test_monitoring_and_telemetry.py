#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import unittest

from ansible_collections.ansiblesharp.common.plugins.module_utils.base_config import BaseConfig
from ansible_collections.ansiblesharp.common.plugins.callback.monitoring_and_telemetry import TaskData, HostData, PlaybookData, PlayData

class Test_MonAndTelemetry(unittest.TestCase):

    def setUp(self):
        self.host_data = HostData("976c1cfe-d829-40af-b9da-c68670c14099", "host1", "included", "result")

        self.task_data = TaskData("976c1cfe-d829-40af-b9da-c68670c14099",
                                  "demo",
                                  "demo",
                                  "playname",
                                  "test",
                                  "noargs")
        

    def test_task_data_init(self):

        self.task_data.add_host(self.host_data)
        self.task_data.add_host(self.host_data)
        
        self.assertEqual(self.task_data.host_data["976c1cfe-d829-40af-b9da-c68670c14099"].name, "host1")
        
