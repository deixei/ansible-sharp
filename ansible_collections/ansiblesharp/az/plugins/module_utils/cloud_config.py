
#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import yaml
import os

from ansible.errors import AnsibleError
from jinja2 import Template

CLOUD_CONFIG_FILE = "cloud_vars.yml"

class CloudConfig():
    """
    Class representing the Cloud Config.

    This class provides a way to load data from a YAML file and store it in the `data` property.

    Methods:
        data: Property method that returns the loaded data. If the data is not loaded yet, it calls the `get_data` method to load it.
        get_data: Method that loads the data from the YAML file and returns it.
    Examples:
        cloud_config = CloudConfig()
        cloud_config.data

        cloud_vars:
            version: 1.0.0
            kind: cloud_vars

        data['version'] # 1.0.0

    """

    def __init__(self):
        self._data = {}
    
    @property
    def data(self):
        if not self._data:
            self._data = self.get_data()
        return self._data

    @property
    def cloud_vars(self):
        return self.data.get('cloud_vars', {})
    
    @property
    def defaults(self):
        return self.data.get('defaults', {})

    def get_data(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_path,"..","vars", CLOUD_CONFIG_FILE)

        data = {}

        try:
            with open(yaml_path, 'r') as stream:
                variables = yaml.safe_load(stream)
        except Exception as e:
            raise AnsibleError(f"[Ansible-Sharp ERROR]: Failed to load YAML file {yaml_path}: {e}")
        
        yaml_string = str(variables)
        # Create a template from the string
        template = Template(yaml_string)

        # Render the template with the variables
        rendered_string = template.render(variables)

        # Parse the rendered template as YAML
        #data = yaml.safe_load(rendered_string)
        data = list(yaml.full_load_all(rendered_string))

        return data[0]

        