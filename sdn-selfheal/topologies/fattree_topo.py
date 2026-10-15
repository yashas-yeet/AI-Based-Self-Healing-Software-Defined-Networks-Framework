"""
Fat-Tree k=4 Topology (20 switches, 16 hosts).
Standard 3-tier data center architecture (Core, Aggregation, Edge).
"""

from mininet.topo import Topo
from topologies.topo_utils import assign_host_config

class FatTree4Topo(Topo):
    """
    Fat-Tree topology with k=4.
    - 4 Core switches (c1..c4)
    - 4 Pods, each containing:
        - 2 Aggregation switches (a_pod_1, a_pod_2)
        - 2 Edge switches (e_pod_1, e_pod_2)
        - 4 Hosts (2 per edge switch)
    Total: 20 switches (c1..c4, a1..a8, e1..e8) and 16 hosts (h1..h16).
    """
    def build(self, bw: float = 100.0, delay: str = "1ms", loss: float = 0.0):
        k = 4
        num_core = (k // 2) ** 2  # 4
        num_pods = k             # 4
        
        # 1. Add Core Switches (c1..c4)
        core_switches = []
        dpid_counter = 1
        for i in range(1, num_core + 1):
            name = f"c{i}"
            sw = self.addSwitch(name, dpid=f"{dpid_counter:016x}")
            core_switches.append(sw)
            dpid_counter += 1
            
        agg_switches = {}
        edge_switches = {}
        host_counter = 1
        
        # 2. Add Pods
        for pod in range(num_pods):
            agg_switches[pod] = []
            edge_switches[pod] = []
            
            # Aggregation switches
            for a in range(k // 2):
                name = f"a{pod}_{a}"
                sw = self.addSwitch(name, dpid=f"{dpid_counter:016x}")
                agg_switches[pod].append(sw)
                dpid_counter += 1
                
            # Edge switches
            for e in range(k // 2):
                name = f"e{pod}_{e}"
                sw = self.addSwitch(name, dpid=f"{dpid_counter:016x}")
                edge_switches[pod].append(sw)
                dpid_counter += 1
                
                # Connect 2 hosts per edge switch
                for h in range(k // 2):
                    h_name = f"h{host_counter}"
                    cfg = assign_host_config(host_counter)
                    host = self.addHost(h_name, ip=cfg["ip"], mac=cfg["mac"])
                    self.addLink(host, sw, bw=bw, delay=delay, loss=0.0)
                    host_counter += 1
                    
            # Connect edge to aggregation within pod (complete bipartite)
            for e_sw in edge_switches[pod]:
                for a_sw in agg_switches[pod]:
                    self.addLink(e_sw, a_sw, bw=bw, delay=delay, loss=loss)
                    
        # 3. Connect Aggregation to Core switches
        # In k-ary fat-tree, core switches are grouped into (k/2) groups of (k/2) switches.
        for pod in range(num_pods):
            for a_idx, a_sw in enumerate(agg_switches[pod]):
                # Connect a_idx-th agg switch to core switches: a_idx * (k/2) to (a_idx + 1) * (k/2)
                for c_offset in range(k // 2):
                    c_idx = a_idx * (k // 2) + c_offset
                    self.addLink(a_sw, core_switches[c_idx], bw=bw, delay=delay, loss=loss)

topos = {"fattree4": (lambda: FatTree4Topo())}
