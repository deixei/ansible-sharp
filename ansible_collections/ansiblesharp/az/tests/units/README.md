# How to execute

As part of VS code, add a "setting.json" to your workplace ".vscode" folder

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
        "ansiblesharp"
    ],
}
```

This will allow you to get unit test case visible in VS Code and to be able to debug them as well.

