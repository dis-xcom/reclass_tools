# reclass-tools
QA tools for manipulating reclass models

Install
=======

```
apt-get install python-virtualenv python-pip build-essential python-dev libssl-dev
pip install git+https://github.com/dis-xcom/reclass-tools
```

Contribute
==========

Please send patches using gerrithub.io:

```
git remote add gerrit ssh://review.gerrithub.io:29418/dis-xcom/reclass-tools
git review
```

Usage
=====

This tool can be used to create a new class 'environment' generated from custom inventory.

See all the nodes available from reclass inventory (including generated nodes):
```
reclass-tools list-nodes
```

See only VCP nodes for specific domain:
```
reclass-tools list-nodes -d mcp11-ovs-dpdk.local --vcp-only
```

See only non-VCP nodes for specific domain (baremetal nodes):
```
reclass-tools list-nodes -d mcp11-ovs-dpdk.local --non-vcp-only
```

Find specific key in the path (without reclass render):
```
reclass-tools get-key parameters._param.cluster_domain /srv/salt/reclass/classes/cluster/physical_mcp11_ovs_dpdk/
```

Collect all parameters._param into a single dict, to track _param changes from commit to commit:
```
reclass-tools list-params /srv/salt/reclass/classes/
```

Requirements
------------

- Installed and configured 'reclass' package
- Prepared 'cluster', 'system' and 'service' classes
- [Optional] Nodes generated with salt-call state.sls reclass.storage

Create 'environment' class
--------------------------

This is a PoC of creating the 'environment' class.
For CI tests, please generate your 'inventory.yaml' for step #3 and create
the cookiecutter template based on example template from /examples directory.

For this example will be used the 'cluster' model 'mcp11-ovs-dpdk.local'
from 'mcp-baremetal-lab' repo.

All steps should be performed on the installed salt-master node, when all
nodes have been generated with 'reclass.storage' state.

1. Create a context file with nodes list and 'linux.network.interface' configuration
from the current reclass inventory.

```
reclass-tools show-context -d mcp11-ovs-dpdk.local parameters.linux.network.interface > /tmp/context-mcp11-ovs-dpdk.local.yaml
```

2. Remove existing hardware-related 'linux.network.interface' object from 'cluster', 'system' and 'service' classes.
WARNING! Make sure that you have created the context file with 'linux.network.interface' as a backup.

```
reclass-tools del-key parameters.linux.network.interface /srv/salt/reclass/classes/cluster/physical_mcp11_ovs_dpdk
reclass-tools del-key parameters.linux.network.interface /srv/salt/reclass/classes/system/
reclass-tools del-key parameters.linux.network.interface /usr/share/salt-formulas/reclass/
```

3. Render the 'environment' class using example template based on cookiecutter:

```
git clone https://github.com/dis-xcom/reclass_tools ~/reclass_tools
reclass-tools render -t ~/reclass_tools/examples/environment -o /tmp/environment -c /tmp/context-mcp11-ovs-dpdk.local.yaml  # You can add multiple YAMLs here
```

4. Check that the 'environment' has been created

```
tree /tmp/environment/
```

5. Symlink 'environment' to the /srv/salt/reclass/classes

```
ln -s /tmp/environment /srv/reclass/salt/classes
```

6. Add new class '- environment.mcp11-ovs-dpdk.local' to the classes/cluster/<cluster_model>/infra/config.yml
(edit the file manually for now)

7. Update the nodes for reclass inventory

```
salt-call state.sls reclass.storage
```