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
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint

logging.basicConfig(level=logging.INFO)
setLogLevel('info')  # set Mininet loglevel
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('api.openstack.base').setLevel(logging.INFO)
logging.getLogger('api.openstack.compute').setLevel(logging.INFO)
logging.getLogger('api.openstack.keystone').setLevel(logging.INFO)
logging.getLogger('api.openstack.nova').setLevel(logging.INFO)
logging.getLogger('api.openstack.neutron').setLevel(logging.INFO)
logging.getLogger('api.openstack.heat').setLevel(logging.INFO)
logging.getLogger('api.openstack.heat.parser').setLevel(logging.INFO)
logging.getLogger('api.openstack.glance').setLevel(logging.INFO)
logging.getLogger('api.openstack.helper').setLevel(logging.INFO)


STEP_SIZE_POPS = 5


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
        self.results = {
            "time_env_boot": 0,
            "time_pop_create": 0,
            "time_link_create": 0,
            "time_topo_start": 0,
            "time_total": 0,
            "mem_total": 0,
            "mem_available": 0,
            "mem_percent": 0,
            "mem_used": 0,
            "mem_free": 0,
            "n_pops": args.n_pops,
            "topology": args.topology,
            "r_id": args.r_id
        }
        # initialize global rest api
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
                # print((self.pops[i].name, self.pops[j].name))
                if (self.pops[i].name == self.pops[j].name):
                    # print("skipped: self-link")
                    continue
                if ((self.pops[i].name, self.pops[j].name) in existing_links or
                    (self.pops[j].name, self.pops[i].name) in existing_links):
                    # print("skipped")
                    continue
                existing_links.append((self.pops[i].name, self.pops[j].name))
                self.net.addLink(self.pops[i], self.pops[j])

    def start_topology(self):
        print("start_topology")
        self.net.start()

    def cli(self):
        self.net.CLI()
        
    def stop_topology(self):
        self.rest_api.stop()
        for a in self.osapis:
            a.stop()
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

    parser.add_argument(
        "--result-path",
         help="Outputs, default=result.pkl",
        required=False,
        default="result.pkl",
        dest="result_path")

    parser.add_argument(
        "--experiments",
        help="Run all experiments.",
        required=False,
        default=False,
        dest="experiments",
        action="store_true")

    parser.add_argument(
        "--no-run",
        help="Just generate. No execution.",
        required=False,
        default=False,
        dest="no_run",
        action="store_true")


    return parser.parse_args()

def run_experiments(args):
    """
    Run all startup timing experiments
    """
    # result collection
    result_dict_list = list()
    # setup parameter lists
    args.topology_list = ["line", "star", "mesh"]
    # iterate over configs and execute
    for topo in args.topology_list:
        if topo == "mesh":
           max_pops = 50
        else:
           max_pops = 100
        # remove to use cli parameter
        args.n_pops = max_pops
        args.pop_configs = [1]
        args.pop_configs += list(range(5, int(args.n_pops) + 1, STEP_SIZE_POPS))
        for pc in args.pop_configs:
            for r_id in range(0, int(args.repetitions)):
                args.topology = topo
                args.n_pops = pc
                args.r_id = r_id
                print("Running experiment topo={} n_pops={} r_id={}".format(
                    args.topology,
                    args.n_pops,
                    args.r_id
                ))
                if not args.no_run:
                    t = EvaluationTopology(args)
                    time.sleep(2)
                    t.stop_topology()
                    time.sleep(2)
                    # collect and store results
                    result_dict_list.append(t.results)
    # results to dataframe
    return pd.DataFrame(result_dict_list)

def main():
    args = parse_args()
    args.r_id = 0
    print("Args: {}".format(args))

    if args.experiments == False:
        # form manual tests and debugging
        t = EvaluationTopology(args)
        t.cli()
        t.stop_topology()
        print(t.results)
    elif args.experiments == True:
        df = run_experiments(args)
        # write results to disk
        print(df)
        df.to_pickle(args.result_path)
        print("Experiments done. Written to {}".format(args.result_path))


if __name__ == '__main__':
    main()
