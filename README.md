# reclass-tools
QA tools for manipulating reclass models

Install:
--------

    apt-get install python-virtualenv python-pip build-essential python-dev libssl-dev
    virtualenv venv-reclass-tools
    source venv-reclass-tools/bin/activate
    pip install https://github.com/dis-xcom/reclass-tools

Usage:
------

    This tool can be used to create a new class 'environment' generated from custom inventory.

Requirements
============

- Installed and configured 'reclass' package
- Prepared 'cluster', 'system' and 'service' classes
- [Optional] Nodes generated with salt-call state.sls reclass.storage

Create 'environment' class
==========================

    # 1. Create a context file from the current reclass inventory:

    reclass-create-inventory-context -d mcp11-ovs-dpdk.local > /tmp/context-mcp11-ovs-dpdk.local.yaml

    # 2. Remove existing hardware-related objects from 'cluster', 'system' and 'service' classes:

    reclass-remove-key -r parameters.linux.network.interface /srv/salt/reclass/classes/cluster/physical_mcp11_ovs_dpdk
    reclass-remove-key -r parameters.linux.network.interface /srv/salt/reclass/classes/system/
    reclass-remove-key -r parameters.linux.network.interface /usr/share/salt-formulas/reclass/

    # 3. Render the 'environment' class using example template based on cookiecutter:

    git clone https://github.com/dis-xcom/reclass_tools ~/reclass_tools
    reclass-render-dir -t ~/reclass_tools/examples/environment -o /tmp/environment -c /tmp/context-mcp11-ovs-dpdk.local.yaml  # You can add multiple YAMLs here

    # 4. Symlink 'environment' to the /srv/reclass/salt/classes

    ln -s /tmp/environment /srv/reclass/salt/classes

    # 5. Add new class '- environment.mcp11-ovs-dpdk.local' to the classes/cluster/<cluster_model>/infra/config.yml
