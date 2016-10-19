import random
import sys

import io

import vagrant
import yaml
from pykwalify.core import Core


# from spin_vagrant import vagrant_spin_up

gp_values = {'ssh': 22, 'ssh_xr': 22, 'ssh_xr_shell': 57722, 'netconf': 830}


class TopologyRunner:
    def __init__(self, scheme_file, data_file):
        self.validate_topology(scheme_file, data_file)

    @staticmethod
    def validate_topology(scheme_file, data_file):
        c = Core(source_file=data_file, schema_files=[scheme_file])
        c.validate(raise_exception=True)
        print 'Topology validated'

    @staticmethod
    def topology_spin_up(self, data_file):
        with open(data_file, 'r') as stream:
            try:
                topo_yaml = (yaml.load(stream))
            except yaml.YAMLError as exc:
                print(exc)
                sys.exit('YAML file not available')

                # if topo_yaml['orchestration'] == 'vagrant':
                #     vagrant_spin_up(topo_yaml)


class VagrantRunner(TopologyRunner):
    def devbox_wrapper(self, node):
        cfg = '\n  # node ' + node['name'] + '\n'
        cfg += '  config.vm.define "{0}" do |{0}|\n'.format(node['name'])
        cfg += '    {0}.vm.box = "{1}"\n'.format(node['name'], node['box'])
        cfg += '    {0}.vm.hostname = "{1}"\n'.format(node['name'], node['name'].replace('_', '-'))
        if 'ports' in node.keys():
            for i in range(0, len(node['ports'])):
                cfg += '    {0}.vm.network "forwarded_port",' \
                       'guest: {1}, host: {2}, auto_correct: true\n' \
                    .format(node['name'],
                            gp_values[node['ports'][i]['type']],
                            node['ports'][i]['value'])

        for wire in node['interfaces']:
            # print wire
            cfg += '    {0}.vm.network :private_network, auto_config: false, virtualbox__intnet: "{1}"\n' \
                .format(node['name'], wire['link-name'])
        # cfg += '    {0}.vm.provision :shell, path: "../ubuntu.sh", privileged: false\n'.format(node['name'])
        cfg += '   end\n'
        return cfg

    def iosxr_node_wrapper(self, node):
        # print node
        cfg = '\n  # node ' + node['name'] + '\n'
        cfg += '  config.vm.define "{0}" do |{0}|\n'.format(node['name'])
        cfg += '    {0}.vm.box = "IOS-XRv"\n'.format(node['name'])
        # cfg += '    {0}.vm.provision "file",' \
        #        ' source: "../configs/{0}_config", destination: "/home/vagrant/{0}_config"\n'.format(node['name'])

        if 'ports' in node.keys():
            for i in range(0, len(node['ports'])):
                cfg += '    {0}.vm.network "forwarded_port",id: "{1}",' \
                       'guest: {2}, host: {3}, auto_correct: true\n' \
                    .format(node['name'],
                            node['ports'][i]['type'],
                            gp_values[node['ports'][i]['type']],
                            node['ports'][i]['value'])

        for wire in node['interfaces']:
            cfg += '    {0}.vm.network :private_network, auto_config: false, virtualbox__intnet: "{1}"\n' \
                .format(node['name'], wire['link-name'])

        # ZTP provision
        # cfg += '\n    {0}.vm.provision "shell" do |s|\n' \
        #        '      s.path =  "../scripts/apply_config.sh"\n' \
        #        '      s.args = ["/home/vagrant/{0}_config"]\n' \
        #        '    end\n'.format(node['name'])

        # Interface modification
        cfg += '\n    {0}.vm.provider :virtualbox do |vb|\n'.format(node['name'])
        # for i in range(0, len(node['interfaces'])):
        # cfg += '      vb.customize ["modifyvm", :id, "--nictype{0}", "virtio" ]\n'.format(i+1)
        cfg += '      vb.customize ["modifyvm", :id, "--uart1", "0x3F8", 4, "--uartmode1", "server", "/tmp/{0}"]\n'.format(
            node['name'])
        cfg += '    end\n'
        cfg += '  end\n'
        conf_name = "../configs/" + node['name'] + "_config"

        mode = 'w+'
        with io.FileIO(conf_name, mode) as d:
            d.write("hostname %s\n" % node['name'])
            for i in range(0, len(node['interfaces'])):
                d.write('!\n')
                d.write('interface GigabitEthernet0/0/0/' + str(i) + '\n')
                # d.write(' ipv4 address {0} {1}'.
                # format(node['interfaces'][i]['ip'], node['interfaces'][i]['mask']) + '\n')
                d.write(' no shutdown\n')
                d.write('!\n')

        return cfg

    def topology_spin_up(self, data_file):

        with open(data_file, 'r') as stream:
            try:
                topo_yaml = (yaml.load(stream))
                # print str(topo_yaml).replace("'", '"')
            except yaml.YAMLError as exc:
                print(exc)
                sys.exit('YAML file not available')
        file_name = "Vagrantfile"
        mode = 'w'
        nodes = topo_yaml['nodes']

        with io.FileIO(file_name, mode) as f:
            f.write("# -*- mode: ruby -*-\n")
            f.write("# vi: set ft=ruby :\n")
            f.write("\n")
            f.write("Vagrant.configure(2) do |config|\n")
            f.write("  config.vm.box_check_update = false\n")
            f.write("  # nodes section\n\n")
            for node in nodes:
                if node['box'] == "IOS-XRv" or node['box'] == "IOS-XRv6gb":
                    f.write(self.iosxr_node_wrapper(node))
                elif node['box'] == "ubuntu/trusty64":
                    f.write(self.devbox_wrapper(node))
            f.write("\nend")
            print 'Vagrantfile created'
            f.close()
        with io.FileIO("../ansible/ansible_hosts", mode) as h:
            h.write("[network-nodes]\n")
            for node in nodes:
                if 'ports' in node.keys():

                    k = 0
                    if len(node['ports']) > 1:
                        for port in node['ports']:
                            if port['type'] == 'ssh' or port['type'] == 'ssh_xr_shell':
                                k = node['ports'].index(port)
                    h.write(node['name'] +
                            " ansible_ssh_host=127.0.0.1"
                            " ansible_ssh_port=" + str(node['ports'][k]['value']) +
                            " ansible_ssh_user=vagrant ansible_ssh_pass=vagrant\n")
            h.write("\n")
            h.close()


scheme = sys.argv[1]
data_file = sys.argv[2]
vr = VagrantRunner(scheme, data_file)
vr.topology_spin_up(data_file)
#
# v = vagrant.Vagrant()
# v.up()
# env = {}
# env.hosts = [v.user_hostname_port()]
# env.key_filename = v.keyfile()
# env.disable_known_hosts = True
# print env
