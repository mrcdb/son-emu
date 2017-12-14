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
import os
import sys
import pandas as pd
import psutil
import subprocess
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from processify import processify
from topology_zoo import TopologyZooTopology

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


class OsmZooTopology(TopologyZooTopology):

    def __init__(self, *args, **kwargs):
        super(OsmZooTopology, self).__init__(*args, **kwargs)
        self.osm_set_environment()
        self.osm_results = list()

    def _add_result(self, action, t):
        self.osm_results.append(
            {
                "r_id": self.r_id,
                "action": action,
                "time": t,
                "config_uuid": self.uuid
            }
        )

    def get_keystone_endpoints(self):
        return [a.port for a in self.osapis]

    def osm_set_environment(self):
        self.ip_so = subprocess.check_output(
            """lxc list | awk '($2=="SO-ub"){print $6}'""",
            shell=True).strip()
        self.ip_ro = subprocess.check_output(
            """lxc list | awk '($2=="RO"){print $6}'""",
            shell=True).strip()

    def _osm_create_vim(self, port):
        cmd = "osm --hostname {} --ro-hostname {} vim-create --name pop{} --user username --password password --auth_url http://127.0.0.1:{}/v2.0 --tenant tenantName --account_type openstack".format(
            self.ip_so,
            self.ip_ro,
            port,
            port
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("vim-create", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")

    def _osm_delete_vim(self, port):
        cmd = "osm --hostname {} --ro-hostname {} vim-delete pop{}".format(
            self.ip_so,
            self.ip_ro,
            port
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("vim-delete", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")

    def _osm_show_vim(self, port):
        cmd = "osm --hostname {} --ro-hostname {} vim-show pop{}".format(
            self.ip_so,
            self.ip_ro,
            port
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("vim-show", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")

    def _osm_onboard_nsd(self, path):
        cmd = "osm --hostname {} --ro-hostname {} upload-package {}".format(
            self.ip_so,
            self.ip_ro,
            path
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("nsd-onboard", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")

    def _osm_onboard_vnfd(self, path):
        cmd = "osm --hostname {} --ro-hostname {} upload-package {}".format(
            self.ip_so,
            self.ip_ro,
            path
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("vnfd-onboard", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")

    def _osm_delete_nsd(self, name):
        cmd = "osm --hostname {} --ro-hostname {} nsd-delete {}".format(
            self.ip_so,
            self.ip_ro,
            name
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("nsd-delete", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")

    def _osm_delete_vnfd(self, name):
        cmd = "osm --hostname {} --ro-hostname {} vnfd-delete {}".format(
            self.ip_so,
            self.ip_ro,
            name
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("vnfd-delete", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")

    def osm_create_vims(self):
        """
        Adds the emulated VIMs to a local OSM installation.
        """
        for p in self.get_keystone_endpoints():
            self._osm_create_vim(p)

    def osm_delete_vims(self):
        """
        Removes the emulated VIMs from the local OSM installation.
        """
        for p in self.get_keystone_endpoints():
            self._osm_delete_vim(p)

    def osm_show_vims(self):
        for p in self.get_keystone_endpoints():
            self._osm_show_vim(p)

    def osm_onboard_service(self):
        self._osm_onboard_vnfd("examples/osm_pkgs/pong.tar.gz")
        self._osm_onboard_vnfd("examples/osm_pkgs/ping.tar.gz")
        self._osm_onboard_nsd("examples/osm_pkgs/pingpong_nsd.tar.gz")

    def osm_delete_service(self):
        self._osm_delete_nsd("pingpong")
        self._osm_delete_vnfd("ping")
        self._osm_delete_vnfd("pong")

    def osm_instantiate_service(self):
        """
        Instantiates the experiment service(s) using the local OSM installation.
        One service per PoP (OSM can does currently not support cross-PoP services)
        Uses random placement for the VNFs.
        """
        pass

    def osm_terminate_service(self):
        pass




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
        "--experiment",
        help="none|scaling|zoo|service",
        required=False,
        default=None,
        dest="experiment")

    parser.add_argument(
        "--no-run",
        help="Just generate. No execution.",
        required=False,
        default=False,
        dest="no_run",
        action="store_true")

    return parser.parse_args()


def get_graph_files(args):
    # collect topologies to be tested
    graph_files = list()
    for (dirpath, dirnames, filenames) in os.walk(args.zoo_path):
        for f in filenames:
            if ".graphml" in f:
                if f in args.topology_list:
                    graph_files.append(os.path.join(args.zoo_path, f))
    print("Found {} TopologyZoo graphs to be emulated.".format(len(graph_files)))
    return graph_files


@processify
def run_experiment(args, topo_cls, service_size=None):
    """
    Run a single experiment (as sub-process)
    """
    t = topo_cls(args)
    time.sleep(2)
    if service_size is not None:
        t.start_service(service_size)
    time.sleep(5)
    t.stop_topology()
    time.sleep(2)
    return t.results.copy()

                    
def run_service_experiments(args):
    """
    Start up to args.service_sizes VNFs in given topologies.
    """
    # result collection
    result_dict_list = list()

    for g in get_graph_files(args):
        args.graph_file = g
        for s in args.service_sizes:  # start s VNFs
            for r_id in range(0, int(args.repetitions)):
                args.r_id = r_id
                print("Running experiment topo={} service_size={} r_id={}".format(
                    g,
                    s,
                    args.r_id
                ))
                if not args.no_run:
                    try:
                        result_dict_list.append(
                            run_experiment(args, OsmZooTopology, service_size=s)
                        )
                    except:
                        print("Error in experiment: {}".format(sys.exc_info()[1]))
                        print("Topology: {}".format(args.graph_file))

    # results to dataframe
    return pd.DataFrame(result_dict_list)

def main():
    args = parse_args()
    args.r_id = 0
    print("Args: {}".format(args))

    if args.experiment is None or str(args.experiment).lower() == "none":
        # form manual tests and debugging
        args.graph_file = "examples/topology_zoo/Abilene.graphml"
        t = OsmZooTopology(args)
        print("Keystone endpoints: {}".format(t.get_keystone_endpoints()))
        t.osm_create_vims()
        t.osm_show_vims()
        t.osm_onboard_service()
        t.cli()
        t.osm_delete_service()
        t.osm_delete_vims()
        t.stop_topology()
        print(t.results)
        print(pd.DataFrame(t.osm_results))
    elif str(args.experiment).lower() == "zoo":
        args.topology_list = ["Abilene.graphml", "DeutscheTelekom.graphml", "UsCarrier.graphml"]
        args.zoo_path = "examples/topology_zoo/"
        args.service_sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256]
        df = run_service_experiments(args)
        # write results to disk
        print(df)
        df.to_pickle(args.result_path)
        print("Experiments done. Written to {}".format(args.result_path))

if __name__ == '__main__':
    main()

"""
Examples:

    * sudo python examples/evaluation_starttimes.py --experiment none
    * sudo python examples/evaluation_starttimes.py --experiment scaling -r 5
    * sudo python examples/evaluation_starttimes.py --experiment scaling -r 5 --no-run
    * sudo python examples/evaluation_starttimes.py --experiment zoo -r 5 --no-run
    * sudo python examples/evaluation_starttimes.py --experiment service -r 5 --no-run
"""
