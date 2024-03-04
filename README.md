# ansible-sharp

Sharping the edges of Ansible for Azure and SecDevOps, with a strong integration with Change Management.

- [deixei.com](http://www.deixei.com)
- [linkedin](https://www.linkedin.com/company/deixei/)

About me: [Marcio Parente](./ABOUTME.md)

dx CLI: [dx](https://github.com/deixei/dx)

Getting context, read the book: [ENTERPRISE SOFTWARE DELIVERY: A ROADMAP FOR THE FUTURE](./BOOK.md)

## Configuration

Add a "user.vars.env" file with this content

```bash
PYTHONPATH=~/.ansible/collections/ansible_collections
AZURE_CLIENT_ID=change_me
AZURE_SECRET=change_me
AZURE_TENANT=change_me
```

## Build and Install collections

```bash
dx ansible build --name "/ansiblesharp"
```

## Run test cases

```bash
dx ansible test --name "/ansiblesharp"
```

## Executing a play with dx

Loads your configuration variables that where configure with [dx](https://github.com/deixei/dx) and executes

```bash
dx ansible play -n play.ansible.yml -i inventories/d1
```

With full debug flags:

```bash
dx ansible play -n play.ansible.yml -i inventories/d1 -v vvv
```

## Structure

This repos is made in a way that allows you to continually develop your playbooks along the development of the collections.

once you are just using the ansible sharp collection, you only need the workloads to serve as reference.

### Under "ansible_collections"

Contains 2 collections forming the ansible sharp.

- Common
- AZ

### Under "workload_playbooks"

Contains several workload examples, each workload contains many playbooks.

- workload_1

## VS Code Configuration

### Launch

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Ansible Module: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "args":[
                "${fileDirname}/args/${fileBasenameNoExtension}.json",
            ],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "AZURE_CLIENT_ID": "change me",
                "AZURE_SECRET": "change me",
                "AZURE_TENANT": "change me"
            }
        }
    ]
}
```

### Settings

```json
{
    "python.envFile": "${workspaceFolder}/.env",
    "python.testing.unittestArgs": [
        "-v",
        "-s",
        "${workspaceFolder}/ansible_collections",
        "-p",
        "test_*.py"
    ],
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "ansible_collections"
    ],
    "cSpell.words": [
        "ansiblesharp",
        "Marcio",
        "Parente"
    ],
}
```
