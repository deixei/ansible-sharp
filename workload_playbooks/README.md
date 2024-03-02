# Workload Playbooks

Examples of multiple workloads going into Azure.

Each workload folder contains an set of examples, from simple to more complex.

## Executing a play with dx

Loads your configuration variables that where configure with [dx](https://github.com/deixei/dx) and executes

```bash
dx ansible play -n play.ansible.yml -i inventories/d1
```

With full debug flags:

```bash
dx ansible play -n play.ansible.yml -i inventories/d1 -v vvv
```

### without dx

With this method you rely on the environment variable you have setup

```bash
ansible-playbook -i inventories/d1 play.ansible.yml
```
