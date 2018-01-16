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
import random
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from processify import processify
from topology_zoo import TopologyZooTopology

logging.basicConfig(level=logging.DEBUG)
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


class OsmZooTopology(TopologyZooTopology):

    def __init__(self, *args, **kwargs):
        super(OsmZooTopology, self).__init__(*args, enable_rest_api=False, **kwargs)
        self.osm_set_environment()
        self.osm_results = list()
        self.vim_port_list = list()
        self.running_services = 0

    def _add_result(self, action, t):
        r = {"action": action,
             "time_action": t,
             "run_uuid": self.uuid,
             "config_id": self.args.config_id,
             "ns_running": self.running_services,
             "vims_attached": len(self.vim_port_list)
            }
        r.update(self.results)
        self.osm_results.append(r)

    def get_keystone_endpoints(self):
        return [a.port for a in self.osapis]

    def osm_set_environment(self):
        self.ip_so = subprocess.check_output(
            """lxc list | awk '($2=="SO-ub"){print $6}'""",
            shell=True).strip()
        self.ip_ro = subprocess.check_output(
            """lxc list | awk '($2=="RO"){print $6}'""",
            shell=True).strip()
        self.ip_lxc_br = subprocess.check_output(
            """ifconfig lxdbr0 | awk '/inet addr/{print substr($2,6)}'""",
            shell=True).strip()
        if len(self.ip_lxc_br) < 1:
            self.ip_lxc_br = subprocess.check_output(
            """ifconfig lxdbr0 | awk '/inet /{print substr($2,0)}'""",
            shell=True).strip()

    def _osm_create_vim(self, port):
        cmd = "osm --hostname {} --ro-hostname {} vim-create --name pop{} --user username --password password --auth_url http://{}:{}/v2.0 --tenant tenantName --account_type openstack".format(
            self.ip_so,
            self.ip_ro,
            port,
            self.ip_lxc_br,
            port
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("vim-create", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")
            exit(1)
            return
        self.vim_port_list.append(port)

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

    def _osm_list_vim(self):
        cmd = "osm --hostname {} --ro-hostname {} vim-list".format(
            self.ip_so,
            self.ip_ro
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.check_output(cmd, shell=True)
        self._add_result("vim-list", abs(time.time() - t_start))
        #print("RETURN:\n{}".format(r))
        return r

    def _osm_parse_vim_list(self, r):
        lines = r.split("\n")
        res = list()
        for l in lines:
            parts = l.split(" ")
            for p in parts:
                if "pop6" in p:
                    res.append(int(p.strip("po")))
        return res

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
            exit(1)

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
            exit(1)

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
            exit(1)

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
            exit(1)

    def _osm_create_ns(self, name, iname, port, wait=False):
        cmd = "osm --hostname {} --ro-hostname {} ns-create --nsd_name {} --ns_name {} --vim_account pop{}".format(
            self.ip_so,
            self.ip_ro,
            name,
            iname,
            port
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        if wait:
            self._osm_wait_for_instantiation(iname)
        self._add_result("ns-create", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")
            exit(1)
            return
        self.running_services += 1

    def _osm_ns_list(self):
        cmd = "osm --hostname {} --ro-hostname {} ns-list".format(
            self.ip_so,
            self.ip_ro
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.check_output(cmd, shell=True)
        self._add_result("nsd-list", abs(time.time() - t_start))
        print("RETURN:\n{}".format(r))
        return r

    def _osm_ns_show(self, name):
        cmd = "osm --hostname {} --ro-hostname {} ns-show {}".format(
            self.ip_so,
            self.ip_ro,
            name
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.check_output(cmd, shell=True)
        self._add_result("nsd-show", abs(time.time() - t_start))
        #print("RETURN:\n{}".format(r))
        return r

    def _osm_parse_ns_status(self, output):
        """
        quick and dirty parsing
        """
        try:
            lines = str(output).split("\n")
            lines = [l for l in lines if ("config-status" in l
                                          or "operational-status" in l)]
            result = None
            return "".join(lines)
        except:
            print("Error: NS status parsing error.")
        return []

    def _osm_get_ns_status(self, ns_name):
        r = self._osm_parse_ns_status(self._osm_ns_show(ns_name))
        if ("running" in r and "configured" in r):
            return True
        return False
    
    def _osm_wait_for_instantiation(self, iname, timeout=60):
        """
        Poll ns-list and wait until given ns is in state: running && configured
        or timeout occurs.
        """
        c = 0
        while(c < timeout):
            s = self._osm_get_ns_status(iname)
            print("Waiting for NS '{}' instantiation and configuration. Status: {} ({}/{})"
                  .format(iname, s, c, timeout))
            if s:
                break
            time.sleep(.5)
            c += 1            

    def _osm_delete_ns(self, iname):
        cmd = "osm --hostname {} --ro-hostname {} ns-delete {}".format(
            self.ip_so,
            self.ip_ro,
            iname
        )
        print("CALL: {}".format(cmd))
        t_start = time.time()
        r = subprocess.call(cmd, shell=True)
        self._add_result("ns-delete", abs(time.time() - t_start))
        print("RETURN: {}".format(r))
        if r != 0:
            print("ERROR")
            exit(1)
            return
        self.running_services -= 1

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

    def osm_list_vims(self):
        """
        Returns a list with parsed VIMs.
        """
        r = self._osm_list_vim()
        l = self._osm_parse_vim_list(r)
        print("VIM list: {}".format(l))
        return l

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

    def osm_instantiate_service(self, iname, port):
        """
        Instantiates the experiment service(s) using the local OSM installation.
        One service per PoP (OSM can does currently not support cross-PoP services)
        Uses random placement for the VNFs.
        """
        self._osm_create_ns("pingpong", iname, port, wait=True)

    def osm_terminate_service(self, iname):
        self._osm_delete_ns(iname)




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
def run_setup_experiment(args, topo_cls):
    """
    Run a single experiment (as sub-process)
    """
    t = topo_cls(args)
    print("Keystone endpoints: {}".format(t.get_keystone_endpoints()))
    time.sleep(2)
    t.timer_start("time_total_vim_attach")
    t.osm_create_vims()
    t.timer_stop("time_total_vim_attach")
    t.osm_show_vims()
    time.sleep(2)
    t.osm_delete_vims()
    time.sleep(2)
    t.stop_topology()
    time.sleep(2)
    return t.results.copy(), t.osm_results

@processify
def run_service_experiment(args, topo_cls):
    """
    Run a single experiment (as sub-process)
    """
    t = topo_cls(args)
    print("Keystone endpoints: {}".format(t.get_keystone_endpoints()))
    time.sleep(2)
    t.timer_start("time_total_vim_attach")
    t.osm_create_vims()
    t.timer_stop("time_total_vim_attach")
    t.osm_show_vims()
    t.timer_start("time_total_on_board")
    t.osm_onboard_service()
    t.timer_stop("time_total_on_board")
    time.sleep(2)
    # get list of available pops for placement
    pop_list = t.osm_list_vims()
    # deploy services
    instances = list()
    t.timer_start("time_service_start")
    for i in range(0, args.max_services):
        iname = "PiPoInst{}".format(i)
        t.osm_instantiate_service(
            iname,
            random.choice(pop_list))  # random placement
        instances.append(iname)
    t.timer_stop("time_service_start")
    time.sleep(60)
    # stop services
    for iname in instances:
        t.osm_terminate_service(iname)
        time.sleep(5)
    time.sleep(20)
    t.osm_delete_service()
    time.sleep(20)
    t.osm_delete_vims()
    time.sleep(20)
    t.stop_topology()
    time.sleep(2)
    return t.results.copy(), t.osm_results


def run_setup_experiments(args):
    """
    Run TopologyZoo Setup Time experiments
    """
    # result collection
    result_dict_list = list()
    osm_result_dict_list = list()
    # collect topologies to be tested
    graph_files = list()
    for (dirpath, dirnames, filenames) in os.walk(args.zoo_path):
        for f in filenames:
            if ".graphml" in f and f in args.topology_list:
                graph_files.append(os.path.join(args.zoo_path, f))
    print("Found {} TopologyZoo graphs to be emulated.".format(len(graph_files)))
    print(graph_files)
    # run experiments
    for g in graph_files:
        args.graph_file = g
        for r_id in range(0, int(args.repetitions)):
            args.r_id = r_id
            print("Running experiment topo={} r_id={}".format(
                    g,
                    args.r_id
                ))
            if not args.no_run:
                try:
                    result, osm_results = run_setup_experiment(
                            args, OsmZooTopology)
                    result_dict_list.append(result)
                    osm_result_dict_list += osm_results
                except:
                    print("Error in experiment: {}".format(sys.exc_info()[1]))
                    print("Topology: {}".format(args.graph_file))
        args.config_id += 1
    # results to dataframe
    return pd.DataFrame(result_dict_list), pd.DataFrame(osm_result_dict_list)

def run_service_experiments(args):
    """
    Deploy args.max_services "ping-pong" services, randomly placed.
    """
    print(args)
    # result collection
    result_dict_list = list()
    osm_result_dict_list = list()
    # collect topologies to be tested
    graph_files = list()
    for (dirpath, dirnames, filenames) in os.walk(args.zoo_path):
        for f in filenames:
            if ".graphml" in f and f in args.topology_list:
                graph_files.append(os.path.join(args.zoo_path, f))
    print("Found {} TopologyZoo graphs to be emulated.".format(len(graph_files)))
    print(graph_files)
    # run experiments
    for g in graph_files:
        args.graph_file = g
        for r_id in range(0, int(args.repetitions)):
            args.r_id = r_id
            print("Running experiment topo={} r_id={}".format(
                    g,
                    args.r_id
                ))
            if not args.no_run:
                try:
                    result, osm_results = run_service_experiment(
                            args, OsmZooTopology)
                    result_dict_list.append(result)
                    osm_result_dict_list += osm_results
                except:
                    print("Error in experiment: {}".format(sys.exc_info()[1]))
                    print("Topology: {}".format(args.graph_file))
        args.config_id += 1
    # results to dataframe
    return pd.DataFrame(result_dict_list), pd.DataFrame(osm_result_dict_list)

def main():
    args = parse_args()
    args.r_id = 0
    args.config_id = 0
    print("Args: {}".format(args))

    if args.experiment is None or str(args.experiment).lower() == "none":
        # form manual tests and debugging
        args.graph_file = "examples/topology_zoo/Arpanet196912.graphml"
        #args.graph_file = "examples/topology_zoo/UsCarrier.graphml"
        t = OsmZooTopology(args)
        print("Keystone endpoints: {}".format(t.get_keystone_endpoints()))
        t.osm_create_vims()
        t.osm_show_vims()
        t.osm_list_vims()
        #t.osm_onboard_service()
        #t.osm_instantiate_service("myinst1", 6001)
        t.cli()
        #t.osm_terminate_service("myinst1")
        #t.osm_delete_service()
        t.osm_delete_vims()
        t.stop_topology()
        print(t.results)
        print(pd.DataFrame(t.osm_results))
    elif str(args.experiment).lower() == "setup":
        args.topology_list = ["Abilene.graphml",
            "Arpanet196912.graphml",
            "Arpanet19728.graphml",
            "AsnetAm.graphml",
            "Basnet.graphml",
            "Belnet2010.graphml",
            "BtNorthAmerica.graphml",
            "BtLatinAmerica.graphml",
            "BtEurope.graphml",
            "BtAsiaPac.graphml",
            "Chinanet.graphml",
            "DeutscheTelekom.graphml",
            "Dfn.graphml",
            "Geant2012.graphml",
            "Globenet.graphml",
            "Interoute.graphml",
            "Ion.graphml",
            "LambdaNet.graphml",
            "Oxford.graphml",
            "Telcove.graphml",
            "Telecomserbia.graphml",
            "UsCarrier.graphml"]
        #args.topology_list = ["UsCarrier.graphml"]
        args.zoo_path = "examples/topology_zoo/"
        df, osm_df = run_setup_experiments(args)
        print(df)
        print(osm_df)
        df.to_pickle(args.result_path)
        osm_df.to_pickle("osm_{}".format(args.result_path))
    elif str(args.experiment).lower() == "service":
        args.topology_list = [args.topology]
        #args.topology_list = ["Abilene.graphml", "DeutscheTelekom.graphml", "UsCarrier.graphml"]
        #args.topology_list = ["Abilene.graphml", "DeutscheTelekom.graphml"]
        #args.topology_list = ["UsCarrier.graphml"]
        #args.topology_list = ["Arpanet196912.graphml"]
        args.zoo_path = "examples/topology_zoo/"
        args.max_services = 64 # 128(?)
        df, osm_df = run_service_experiments(args)
        print(df)
        print(osm_df)
        df.to_pickle(args.result_path)
        osm_df.to_pickle("osm_{}".format(args.result_path))

if __name__ == '__main__':
    main()

"""
osm ns-create --nsd_name pingpong --ns_name inst6001 --vim_account pop6001
osm ns-delete inst6001

+------------------+--------------------------------------+--------------------+---------------+
| ns instance name | id                                   | operational status | config status |
+------------------+--------------------------------------+--------------------+---------------+
| inst6001         | 0d028818-e199-11e7-bef9-005056b887c5 | running            | configured    |
| inst6002         | 2536e1b8-e199-11e7-bef9-005056b887c5 | running            | configured    |
+------------------+--------------------------------------+--------------------+---------------+

Examples:

    * sudo python examples/evaluation_osm_zoo.py
    * sudo python examples/evaluation_osm_zoo.py --experiment setup -r 2
    * sudo python examples/evaluation_osm_zoo.py --experiment service -r 2
    * sudo python examples/evaluati-on_osm_zoo.py --experiment none
"""
