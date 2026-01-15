# Contributing to ansible-sharp

Thanks for taking the time to contribute!

## Getting Started

- Review the [Code of Conduct](./CODE_OF_CONDUCT.md).
- Check existing issues or open a new one to discuss significant changes.

## Development Workflow

1. Create a `user.vars.env` file as described in the [README](./README.md).
2. Build and install the collections:

```bash
dx ansible build --name "/ansiblesharp"
```

3. Run tests:

```bash
mkdir ~/testing
cd ~/testing
dx ansible test --name "/ansiblesharp"
```

## Pull Requests

- Keep changes focused and describe the motivation.
- Update documentation when behavior changes.
- Use the pull request template checklist and include testing results (or note why tests were not run).
