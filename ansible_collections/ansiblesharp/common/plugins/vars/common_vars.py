#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible.errors import AnsibleError
from ansible.plugins.vars import BaseVarsPlugin
from ansible_collections.ansiblesharp.common.plugins.module_utils.common_config import CommonConfig

class VarsModule(BaseVarsPlugin):
    """
    This class represents a custom Ansible vars plugin.
    It provides a method to retrieve variables from a YAML file.
    """

    def get_vars(self, loader, path, entities, cache=True):
        """
        Retrieve variables from a YAML file.

        Args:
            loader (ansible.parsing.dataloader.DataLoader): The Ansible data loader.
            path (str): The path to the YAML file.
            entities (list): The list of entities to retrieve variables for.
            cache (bool, optional): Whether to cache the variables. Defaults to True.

        Returns:
            dict: The variables retrieved from the YAML file.
        """
        super().get_vars(loader, path, entities)
        
        data = {}

        try:
            cfg = CommonConfig()
            data = cfg.data

        except Exception as e:
            raise AnsibleError(f"[Ansible-Sharp ERROR]: Failed to load YAML file: {e}")
        
        return data