
#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente


import yaml
import os

class BaseConfig():
    """
    Class representing the Base Config.

    This class provides a way to load data from a YAML file and store it in the `data` property.

    Methods:
        data: Property method that returns the loaded data. If the data is not loaded yet, it calls the `get_data` method to load it.
        get_data: Method that loads the data from the YAML file and returns it.
    Examples:
        baseconfig = BaseConfig()
        baseconfig.data

        baseconfig:
            validation:
            inventories:
            central_data:
                readme: "baseconfig data"

    """

    def __init__(self):
        self._data = {}
    
    @property
    def data(self):
        if not self._data:
            self._data = self.get_data().get('baseconfig')
        return self._data

    @property
    def central_data(self):
        return self.data['central_data']

    def get_data(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_path,"..","vars", "common_vars.yml")

        data = {}

        try:
            with open(yaml_path, 'r') as stream:
                data = yaml.safe_load(stream)
        except Exception as e:
            raise Exception(f"Failed to load YAML file {yaml_path}: {e}")
        
        return data