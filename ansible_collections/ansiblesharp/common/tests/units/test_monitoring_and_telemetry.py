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
        

        
        self.play = PlayData("test_002_common_vars",
                             "eco_1", 
                             "prj_1", 
                             "wrkl_1")

    def test_task_data_init(self):

        self.task_data.add_host(self.host_data)
        self.task_data.add_host(self.host_data)
        
        self.assertEqual(self.task_data.host_data["976c1cfe-d829-40af-b9da-c68670c14099"].name, "host1")
        

    def test_play(self):
        self.play.add_task(self.task_data)
        
        
        self.assertEqual(self.play.tasks["976c1cfe-d829-40af-b9da-c68670c14099"].name, "demo")


    def test_playbook(self):
        self.playbook = PlaybookData("/home/marcio/repos/deixei/ansible-sharp/ansiblesharp/common/tests/integration/case_1/test_002_common_vars.ansible.yml", 
                                     "eco_1", 
                                     "prj_1", 
                                     "wrkl_1")        