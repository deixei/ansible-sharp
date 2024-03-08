#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import os
from jinja2 import Template

from ansible_collections.ansiblesharp.common.plugins.module_utils.ansible_sharp_module import AnsibleSharpModule
from ansible_collections.ansiblesharp.common.plugins.module_utils.common_config import CommonConfig


class ExecutiveReport(AnsibleSharpModule):
    def __init__(self):
        super(ExecutiveReport, self).__init__(
            argument_spec={
                "report": {
                    "type": "list",
                    "options": {
                        "section": {
                            "type": "dict",
                            "options": {
                                "level": {"type": "str", "required": True, "default": "1"},
                                "title": {"type": "str", "required": True},
                                "paragraphs": {"type": "list"},
                                "items": {"type": "list"},
                            }
                        },
                        "table": {
                            "type": "dict",
                            "options": {
                                "title": {"type": "str", "required": True},
                                "headers": {"type": "list", "required": True},
                                "rows": {"type": "list", "required": True},
                            }
                        },
                        
                        "markdown_file": { "type": "str" },
                        
                        "template": {
                            "type": "dict",
                            "options":{
                                "file_path": {"type": "str", "required": True},
                                "data": {"type": "dict", "required": True, "default": {}}
                            }
                        }
                        
                    }

                },
                
                "file_path": { "type": "str", "required": True },
                "state": { "type": "str", "choices": ["start", "add", "end"], "default": "start" },
            }
        )

        self._config = CommonConfig()

        self.state = self.params["state"]
        self.file_path = self.params["file_path"]

        # check if file_path is valid and if it does not exist ans state is start create the file, if it is "add" or "end" and the file does not exist, raise an error
        if self.state == "start":
            if not os.path.exists(self.file_path):
                self.file = open(self.file_path, "x")
                self.file.close()
            else:
                self.file = open(self.file_path, "w")
                self.file.close()
        elif self.state == "add" or self.state == "end":
            try:
                self.file = open(self.file_path, "r")
                self.file.close()
            except FileNotFoundError as e:
                self.exit_fail(f"File {self.file_path} does not exist. You must start the file with state=start")

        self.report = self.params.get("report", [])

    def run(self):

        with open(self.file_path, "a") as file:

            for section in self.report:
                report_section = section.get("section", None)
                if report_section is not None:
                    title = report_section.get("title", "")
                    paragraphs = report_section.get("paragraphs", [])
                    items = report_section.get("items", [])
                    level = int(report_section.get("level", "1"))

                    header = "#" * level
                    if level > 1:
                        file.write(f"\n")

                    file.write(f"{header} {title}\n\n")
                    for paragraph in paragraphs:
                        file.write(f"{paragraph}\n\n")

                    for item in items:
                        file.write(f"- {item}\n")

                    if items:
                        file.write(f"\n")

                report_table = section.get("table", None)
                if report_table is not None:
                    title = report_table.get("title", "")
                    headers = report_table.get("headers", [])
                    rows = report_table.get("rows", [])

                    file.write(f"{title}\n\n")
                    file.write(" | ".join(headers) + "\n")
                    file.write(" | ".join(["---"] * len(headers)) + "\n")

                    for row in rows:
                        file.write(" | ".join(row) + "\n")

                    file.write("\n")

                markdown_file = section.get("markdown_file", None)
                if markdown_file is not None:
                    with open(markdown_file, "r") as markdown:
                        file.write(markdown.read())

                template = section.get("template", None)
                if template is not None:
                    file_path = template.get("file_path", "")
                    data = template.get("data", {})
                    template_content = ""
                    with open(file_path, "r") as template_file:
                        template_content = template_file.read()

                    # Create a template from the string
                    template = Template(template_content)

                    # Render the template with the variables
                    rendered_string = template.render(data)

                    file.write(rendered_string)

        
        self.exit_success(self.report)

    @property
    def config(self):
        return self._config.data
    

def main():
    my_module = ExecutiveReport()
    my_module.exec_module()

if __name__ == '__main__':
    main()
