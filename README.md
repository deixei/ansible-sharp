# ansible-sharp

Sharping the edges of Ansible for Azure and SecDevOps, with a strong integration with Change Management.

- [deixei.com](http://www.deixei.com)
- [linkedin](https://www.linkedin.com/company/deixei/)

About me: [Marcio Parente](./ABOUTME.md)

dx CLI: [dx](https://github.com/deixei/dx)

Getting context, buy the book: [ENTERPRISE SOFTWARE DELIVERY: A ROADMAP FOR THE FUTURE](https://www.amazon.de/-/en/Marcio-Parente/dp/B0CXTJZJ2X/ref=sr_1_2?crid=2WMPLAVA97359&dib=eyJ2IjoiMSJ9.uZ-anerlZaumQP_1MA3O82nuH7ArezxsMcK6KBZODqea9iaGz2-gYgIkJM-WjtN5IS6VTx5WR5iKzPgtzuiV-5x1GOJmqPAqhnxrd6cf8tztn4_asv3ZH_lowYizmFgSUN_dIez0twxJbu8FW3TtM8PcdqJlwrM5t0v-35s5C8sY56A0pTilntkej-vciGxkFw1ft_kbEdw7cSl6nzvTGVbi3kvRvg15JVx10B5rp80.ugVg-pG2AoXr7gUwn9QuYygFkcvyno9Vnhiipm-CmQg&dib_tag=se&keywords=enterprise+software+delivery&qid=1711349518&sprefix=%2Caps%2C82&sr=8-2)

## Configuration

Add a "user.vars.env" file with this content

```bash
PYTHONPATH=~/.ansible/collections/ansible_collections
AZURE_CLIENT_ID=change_me
AZURE_SECRET=change_me
AZURE_TENANT=change_me
SUBSCRIPTION_ID=???
```

## Build and Install collections

```bash
dx ansible build --name "/ansiblesharp"
```

## Run test cases

```bash
mkdir ~/testing
cd ~/testing
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
            "envFile": "${workspaceFolder}/user.vars.env",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

### Settings

```json
{
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
    "python.envFile": "${workspaceFolder}/user.vars.env"
}
```
