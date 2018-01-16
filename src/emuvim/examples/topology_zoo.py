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
import time
import pandas as pd
import psutil
import networkx as nx
import os
import sys
import random
import uuid
from geopy.distance import vincenty
from mininet.net import Containernet
from mininet.log import setLogLevel
from mininet.link import TCLink
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from processify import processify

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


SPEED_OF_LIGHT = 299792458  # meter per second
PROPAGATION_FACTOR = 0.77  # https://en.wikipedia.org/wiki/Propagation_delay


class TopologyZooTopology(object):

    def __init__(self, args, enable_rest_api=True):
        self.uuid = uuid.uuid4()
        self.args = args
        self.G = self._load_graphml(args.graph_file)
        self.G_name = os.path.basename(args.graph_file).replace(".graphml", "")
        self.r_id =  args.r_id
        self.net = None
        self.pops = list()
        self.osapis = list()
        self._used_labels = list()
        self.results = {
            "time_env_boot": 0,
            "time_pop_create": 0,
            "time_link_create": 0,
            "time_topo_start": 0,
            "time_total": 0,
            "time_total_vim_attach": 0,
            "time_total_on_board": 0,
            "time_service_start": 0,
            "mem_total": 0,
            "mem_available": 0,
            "mem_percent": 0,
            "mem_used": 0,
            "mem_free": 0,
            "n_pops": self.G.__len__(),
            "n_links": self.G.size(),
            "topology": self.G_name,
            "service_size": 0,
            "r_id": args.r_id,
            "run_uuid": self.uuid,
            "config_id": args.config_id
        }
        # initialize global rest api
        self.enable_rest_api = enable_rest_api
        if self.enable_rest_api:
            self.rest_api = RestApiEndpoint("0.0.0.0", 5001)
            self.rest_api.start()
        # initialize topology and record timings
        self.timer_start("time_total")
        self.timer_start("time_env_boot")
        self.create_environment()
        self.timer_stop("time_env_boot")
        self.timer_start("time_pop_create")
        self.create_pops()
        self.timer_stop("time_pop_create")
        self.timer_start("time_link_create")
        self.create_links()
        self.timer_stop("time_link_create")
        self.timer_start("time_topo_start")
        self.start_topology()
        self.timer_stop("time_topo_start")
        self.timer_stop("time_total")
        self.log_mem()

    def _load_graphml(self, path):
        G = nx.read_graphml(path, node_type=int)
        print("Loaded graph from '{}' with {} nodes and {} edges."
              .format(path, G.__len__(), G.size()))
        print(G.adjacency_list())
        return G

    def log_mem(self):
        """
        Record memory statistics
        """
        vm = psutil.virtual_memory()
        self.results["mem_total"] = vm.total
        self.results["mem_available"] = vm.available
        self.results["mem_percent"] = vm.percent
        self.results["mem_used"] = vm.used
        self.results["mem_free"] = vm.free

    def timer_start(self, name):
        self.results[name] = time.time()
        print("timer start {}@{}".format(name, self.results[name]))

    def timer_stop(self, name):
        self.results[name] = time.time() - self.results[name]
        print("timer stop {} = {}".format(name, self.results[name]))

    def create_environment(self):
        print("create environment")
        self.net = DCNetwork(monitor=False, enable_learning=False)
        if self.enable_rest_api:
            self.rest_api.connectDCNetwork(self.net)

    def create_pops(self):
        print("create pops")
        i = 0
        for n in self.G.nodes(data=True):
            name = n[1].get("label")
            if name is None or name == "" or name in self._used_labels:
                name = "dc{}".format(i)
            p = self.net.addDatacenter("{}".format(name))
            self._used_labels.append(name)
            print(p)
            if self.enable_rest_api:
                self.rest_api.connectDatacenter(p)
            a = OpenstackApiEndpoint("0.0.0.0", 6001 + i)
            a.connect_datacenter(p)
            a.start()
            a.connect_dc_network(self.net)
            self.pops.append(p)
            self.osapis.append(a)
            i += 1

    def create_links(self):
        for e in self.G.edges(data=True):
            # parse bw limit from edge
            bw_mbps = self._parse_bandwidth(e)
            # calculate delay from nodes
            delay = self._calc_delay_ms(e[0], e[1])
            try:
                self.net.addLink(self.pops[e[0]], self.pops[e[1]],
                                 cls=TCLink,
                                 delay='{}ms'.format(int(delay)),
                                 bw=min(bw_mbps, 1000))
                print("Created link: {}".format(e))
            except:
                    print("Error in experiment: {}".format(sys.exc_info()[1]))

    def _parse_bandwidth(self, e):
        """
        Calculate the link bandwith based on LinkLabel field.
        Default: 1 Mbps (if field is not given)
        Result is returned in Mbps and down scaled by 10x to fit in the Mininet range.
        """
        ll = e[2].get("LinkLabel")
        if ll is None:
            return 1
        ll = ll.strip(" <>=")
        mbits_factor = 1.0
        if "g" in ll.lower():
            mbits_factor = 1000
        elif "k" in ll.lower():
            mbits_factor = (1.0 / 1000)
        ll = ll.strip("KMGkmpsbit/-+ ")
        try:
            bw = float(ll) * mbits_factor
        except:
            print("ERROR: Parse error: {}".format(ll))
            bw = 1000
        print("- Bandwidth {}-{} = {} Mbps"
              .format(e[0], e[1], bw))    
        return bw / 10.0  # downscale to fit in mininet supported range

    def _calc_distance_meter(self, n1id, n2id):
        """
        Calculate distance in meter between two geo positions.
        """
        n1 = self.G.nodes(data=True)[n1id]
        n2 = self.G.nodes(data=True)[n2id]
        n1_lat, n1_long = n1[1].get("Latitude"), n1[1].get("Longitude")
        n2_lat, n2_long = n2[1].get("Latitude"), n2[1].get("Longitude")
        try:
            return vincenty((n1_lat, n1_long), (n2_lat, n2_long)).meters
        except:
            print("ERROR: Could calculate distance between nodes: {}/{}"
                  .format(n1id, n2id))
        return 0

    def _calc_delay_ms(self, n1id, n2id):
        meter = self._calc_distance_meter(n1id, n2id)
        print("- Distance {}-{} = {} km"
              .format(n1id, n2id, meter / 1000))
        # calc delay
        delay = (meter / SPEED_OF_LIGHT * 1000) * PROPAGATION_FACTOR  # in milliseconds
        print("- Delay {}-{} = {} ms"
              .format(n1id, n2id, delay))
        return delay

    def start_topology(self):
        print("start_topology")
        self.net.start()

    def start_service(self, size):
        """
        Starts a service with 'size' VNFs (empty Ubuntu containers).
        VNF placement is randomized over available nodes.
        """
        print("Starting randomized service with size={}".format(size))
        self.results["service_size"] = size

        self.timer_start("time_service_start")
        for i in range(0, size):
            target_node = random.randint(0, len(self.pops) - 1)
            print("Starting vnf{} on dc{}".format(i, target_node))
            self.pops[target_node].startCompute("vnf{}".format(i))
        self.timer_stop("time_service_start")

    def cli(self):
        self.net.CLI()
        
    def stop_topology(self):
        if self.enable_rest_api:
            self.rest_api.stop()
        for a in self.osapis:
            a.stop()
        self.net.stop()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Emulator TopologyZoo evaluation topology")

    parser.add_argument(
        "-g",
        "--graph",
        help="Input GraphML file",
        required=False,
        default=None,
        dest="graph_file")

    return parser.parse_args()

def main():
    args = parse_args()
    args.r_id = 0
    print("Args: {}".format(args))
    t = TopologyZooTopology(args)
    t.cli()
    t.stop_topology()
    print(t.results)

if __name__ == '__main__':
    main()
