#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible.errors import AnsibleError
from ansible.plugins.vars import BaseVarsPlugin
from ansiblesharp.common.plugins.module_utils.base_config import BaseConfig

class VarsModule(BaseVarsPlugin):

    def get_vars(self, loader, path, entities, cache=True):
        super().get_vars(loader, path, entities)
        
        data = {}

        try:
            cfg = BaseConfig()
            data  = cfg.data()

        except Exception as e:
            raise AnsibleError(f"Failed to load YAML file: {e}")
        
        return data