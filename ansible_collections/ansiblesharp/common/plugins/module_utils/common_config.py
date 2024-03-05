
#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente


import yaml
import os

from ansible.errors import AnsibleError


COMMON_VARS = '''
common_vars:
  version: 1.0.0
  kind: common_vars
  validation:
    stages:
      d: ["Development", "dev", 0, "l"]
      t: ["Testing", "tst", 1, "l"]
      s: ["Staging", "stg", 2, "h"]
      p: ["Production", "prd", 3, "h"]
      g: ["Global", "glb", 4, "h"]
    stage_classifications:
      l: ["Lower", "lw", 0]
      h: ["Higher", "hr", 1]

  central_data:
    url: "http://localhost:8080"
    
'''


class CommonConfig():
    """
    Class representing the Base Config.

    This class provides a way to load data from a YAML file and store it in the `data` property.

    Methods:
        data: Property method that returns the loaded data. If the data is not loaded yet, it calls the `get_data` method to load it.
        get_data: Method that loads the data from the YAML file and returns it.
    Examples:
        CommonConfig = CommonConfig()
        CommonConfig.data

        common_vars:
            version: 1.0.0
            kind: common_vars
            validation: ...
            central_data: ...

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
    def common_vars(self):
        return self.data['common_vars']

    @property
    def central_data(self):
        return self.common_vars['central_data']

    @property
    def stages(self):
        return self.common_vars["validation"]["stages"]
    
    @property
    def stage_classifications(self):
        return self.common_vars["validation"]["stage_classifications"]
    
    def get_data(self):
        data = {}

        try:
            data = yaml.safe_load(COMMON_VARS)
        except Exception as e:
            raise AnsibleError(f"[Ansible-Sharp ERROR]: Failed to load 'COMMON_VARS': {e}")
        
        return data
    
    def validate_stage(self, stage):
        if stage not in self.stages:
            return False
        return True

        