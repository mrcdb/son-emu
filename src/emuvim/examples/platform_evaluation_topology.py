"""
Copyright (c) 2017 SONATA-NFV and Paderborn University
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV, Paderborn University
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""
import logging
import argparse
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint

logging.basicConfig(level=logging.INFO)
setLogLevel('info')  # set Mininet loglevel
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.base').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.compute').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.keystone').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.nova').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.neutron').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.heat').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.heat.parser').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.glance').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.helper').setLevel(logging.DEBUG)


def create_topology1(args):
    net = DCNetwork(monitor=False, enable_learning=False)

    dc1 = net.addDatacenter("dc1")
    # add OpenStack-like APIs to the emulated DC
    api1 = OpenstackApiEndpoint("0.0.0.0", 6001)
    api1.connect_datacenter(dc1)
    api1.start()
    api1.connect_dc_network(net)
    # add the command line interface endpoint to the emulated DC (REST API)
    rapi1 = RestApiEndpoint("0.0.0.0", 5001)
    rapi1.connectDCNetwork(net)
    rapi1.connectDatacenter(dc1)
    rapi1.start()

    net.start()
    net.CLI()
    # when the user types exit in the CLI, we stop the emulator
    net.stop()

class EvaluationTopology(object):

    def __init__(self, args):
        self.args = args
        self.net = None
        self.pops = list()
        self.osapis = list()
        # initialize global rest api
        self.rest_api = RestApiEndpoint("0.0.0.0", 5001)
        self.rest_api.start()
        # initialize topology
        self.create_environment()
        self.create_pops()
        self.create_links()
        self.start_topology()

    def create_environment(self):
        print("create environment")
        self.net = DCNetwork(monitor=False, enable_learning=False)
        self.rest_api.connectDCNetwork(self.net)

    def create_pops(self):
        print("create pops")
        for i in range(0, int(self.args.n_pops)):
            p = self.net.addDatacenter("dc{}".format(i))
            self.rest_api.connectDatacenter(p)
            a = OpenstackApiEndpoint("0.0.0.0", 6001 + i)
            a.connect_datacenter(p)
            a.start()
            a.connect_dc_network(self.net)
            self.pops.append(p)
            self.osapis.append(a)

    def create_links(self):
        if self.args.topology == "line":
            self._create_links_line()
        elif self.args.topology == "star":
            self._create_links_star()
        elif self.args.topology == "mesh":
            self._create_links_full_mesh()
        print("selected topology not implemented")

    def _create_links_line(self):
        print("create links line")
        for i in range(0, len(self.pops) - 1):
            self.net.addLink(self.pops[i], self.pops[i + 1])

    def _create_links_star(self):
        print("create links star")
        center_pop = self.pops[0]
        for i in range(1, len(self.pops)):
            self.net.addLink(center_pop, self.pops[i])

    def _create_links_full_mesh(self):
        print("create links full mesh")
        existing_links = list()
        for i in range(0, len(self.pops)):
            for j in range(0, len(self.pops)):
                print((self.pops[i].name, self.pops[j].name))
                if (self.pops[i].name == self.pops[j].name):
                    print("skipped: self-link")
                    continue
                if ((self.pops[i].name, self.pops[j].name) in existing_links or
                    (self.pops[j].name, self.pops[i].name) in existing_links):
                    print("skipped")
                    continue
                existing_links.append((self.pops[i].name, self.pops[j].name))
                self.net.addLink(self.pops[i], self.pops[j])

    def start_topology(self):
        print("start_topology")
        self.net.start()
        self.net.CLI()
        self.net.stop()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Emulator platform evaluation topology")

    parser.add_argument(
        "-n",
        "--n_pops",
        help="Number of PoPs, default=3",
        required=False,
        default=3,
        dest="n_pops")

    parser.add_argument(
        "-t",
        "--topology",
        help="Topology: line|start|mesh, default=line",
        required=False,
        default="line",
        dest="topology")

    parser.add_argument(
        "-r",
        "--repetitions",
         help="Number of repetitions, default=1",
        required=False,
        default=1,
        dest="repetitions")


    return parser.parse_args()


def main():
    args = parse_args()
    print("Args: {}".format(args))
    #TODO implement repetition mechanism
    t = EvaluationTopology(args)


if __name__ == '__main__':
    main()
