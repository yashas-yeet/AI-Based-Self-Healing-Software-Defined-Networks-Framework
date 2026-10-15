"""
WAN Topology (12-switch irregular topology modeled after NSFNET / Abilene).
Features heterogeneous geographical propagation delays and redundant core backbones.
"""

from mininet.topo import Topo
from topologies.topo_utils import assign_host_config

class WanTopo(Topo):
    """
    12-Node Irregular WAN Topology.
    Nodes represent metropolitan SDN points-of-presence (PoPs) connected by WAN trunks
    with heterogeneous delays (3ms - 18ms) and capacities.
    """
    def build(self, loss: float = 0.0):
        switches = {}
        hosts = {}
        
        # 12 Regional Switches
        for i in range(1, 13):
            sw_name = f"s{i}"
            switches[sw_name] = self.addSwitch(sw_name, dpid=f"{i:016x}")
            
            # Local access host
            h_name = f"h{i}"
            cfg = assign_host_config(i)
            hosts[h_name] = self.addHost(h_name, ip=cfg["ip"], mac=cfg["mac"])
            self.addLink(hosts[h_name], switches[sw_name], bw=100.0, delay="1ms", loss=0.0)
            
        # Heterogeneous WAN links: (src, dst, bw_mbps, delay_str)
        wan_edges = [
            ("s1", "s2", 100.0, "5ms"),
            ("s1", "s3", 100.0, "8ms"),
            ("s2", "s3", 150.0, "4ms"),
            ("s2", "s4", 100.0, "12ms"),
            ("s3", "s6", 200.0, "15ms"),
            ("s4", "s5", 100.0, "6ms"),
            ("s4", "s7", 100.0, "10ms"),
            ("s5", "s6", 150.0, "7ms"),
            ("s5", "s8", 100.0, "9ms"),
            ("s6", "s9", 200.0, "14ms"),
            ("s7", "s8", 100.0, "5ms"),
            ("s7", "s10", 150.0, "11ms"),
            ("s8", "s9", 150.0, "8ms"),
            ("s8", "s11", 100.0, "16ms"),
            ("s9", "s12", 200.0, "18ms"),
            ("s10", "s11", 100.0, "7ms"),
            ("s11", "s12", 150.0, "9ms"),
            ("s1", "s10", 100.0, "15ms"),  # Cross-continent chord
            ("s3", "s12", 200.0, "17ms"),  # Core express trunk
        ]
        
        for u, v, bw, delay in wan_edges:
            self.addLink(switches[u], switches[v], bw=bw, delay=delay, loss=loss)

topos = {"wantopo": (lambda: WanTopo())}
