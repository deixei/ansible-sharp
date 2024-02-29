#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

from ansible.plugins.filter.core import to_json, quote, to_native, from_yaml

DOCUMENTATION = r"""
module:
short_description:
description:
  -
version_added: "0.1.0"
options:
"""
EXAMPLES = r"""
"""
RETURN = r"""
{{ key }}:
  description:
  returned:
  type:
  sample:
"""

class FilterModule(object):
    ''' Nested dict filter '''

    def filters(self):
        return {
            'nesteddict2items': self.nesteddict2items,
            'select_by': self.select_by
        }

    def nesteddict2items(self, vlans_live):
        vlans = []

        for v_key, v_value in vlans_live.items():
            vlans.append(v_value)

        return vlans

    def select_by(self, to_search_list, reference_code , desired_id):
        my_dict = {item[reference_code]: item for item in to_search_list}

        selected_item = my_dict.get(desired_id)
        
        return selected_item

## Info
# https://www.lilatomic.ca/posts/ansible_writing_filter_plugin/