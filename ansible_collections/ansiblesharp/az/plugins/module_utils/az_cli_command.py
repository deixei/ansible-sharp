#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import subprocess
import shutil
import os
from ansible_collections.ansiblesharp.az.plugins.module_utils import common
import json

class AzureCliCommand:
    def __init__(self):
        # Check if Azure CLI is installed.
        self.az_path = shutil.which('az')
        if self.az_path is None:
            raise Exception("[AnsibleSharp ERROR]: az command not found")

    def run(self, cmd, output_format='json', query=None, subscription=None):
        result_json = {}
        output_option = ""
        query_option = ""
        subscription_option = ""

        if common.is_not_empty(output_format):
            output_option = f'--output {output_format}'

        if common.is_not_empty(query):
            query_option = f'--query "{query}"'

        if common.is_not_empty(subscription):
            subscription_option = f'--subscription {subscription}'

        # Set output format to JSON.
        os.environ['AZURE_CLI_OUTPUT_FORMAT'] = output_format

        if common.is_empty(cmd):
            raise Exception("[AnsibleSharp ERROR]: Azure CLI command is empty")

        # Construct Azure CLI command to execute.
        command = f'"{self.az_path}" {cmd} {output_option} {query_option} {subscription_option}'

        try:
            # Execute Azure CLI command and get the result.
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            return_code = e.returncode
            output = e.output

            if output:
                output_str =  output.decode('utf-8')

            if return_code == 1:

                result_json = {
                    'error': output_str
                }
            else:
                result_json = {
                    'warning': output_str
                }
            # If there is an error, fail and return the error message.
            #raise Exception("[AnsibleSharp ERROR]: Failed to run Azure CLI command: %s" % e.output)

        if result:
            # Parse the result into a dictionary.

            content = result.decode('utf-8')

            try:
                result_json = json.loads(content)
            except json.JSONDecodeError as e:
                result_json = {
                    'msg': self.convert_to_json(content)
                }

        return result_json

    def convert_to_json(self, input_string):
        lines = input_string.split('\n')
        result = []
        for line in lines:
            if line:
                result.append(line)
        return result