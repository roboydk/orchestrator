# orchestrator
Topology Orchestration using Ansible

## Required stuff

pykwalify used to validate topology against scheme. Read more about [pyKwalify](https://github.com/grokzen/pykwalify)

All required packages are in file requirements.txt Issue the command to install them:

```shell
pip install -r requirements.txt
```

## Run  

To execute the topology Vagrantfile creation (if method Vagrant in topo file choosen) run the python command with scheme and topologies files.
 
 
```shell
 $ python topo_spin_up.py ../yml/scheme.yaml ../yml/topo_3_nodes.yaml 
Topology validated
Vagrantfile created
```
 
 
