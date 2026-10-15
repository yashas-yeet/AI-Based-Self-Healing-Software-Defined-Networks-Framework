"""
Partial Mesh Topology (8 switches, redundant chordal paths).
Provides multiple disjoint paths between ingress and egress switches for failover testing.
"""

from mininet.topo import Topo
from topologies.topo_utils import assign_host_config

class MeshTopo(Topo):
    """
    8-Switch Partial Mesh Topology with redundant chordal paths.
    
    Structure:
        Outer ring: s1 - s2 - s3 - s4 - s5 - s6 - s7 - s8 - s1
        Cross links: (s1, s4), (s2, s6), (s3, s7), (s5, s8)
        Each switch has an attached host (h1..h8).
    """
    def build(self, bw: float = 100.0, delay: str = "2ms", loss: float = 0.0):
        switches = {}
        hosts = {}
        
        # Create 8 switches
        for i in range(1, 9):
            sw_name = f"s{i}"
            switches[sw_name] = self.addSwitch(sw_name, dpid=f"{i:016x}")
            
            # Add host attached to this switch
            h_name = f"h{i}"
            cfg = assign_host_config(i)
            hosts[h_name] = self.addHost(h_name, ip=cfg["ip"], mac=cfg["mac"])
            self.addLink(hosts[h_name], switches[sw_name], bw=bw, delay="1ms", loss=0.0)
            
        # Outer ring links
        ring_edges = [
            ("s1", "s2"), ("s2", "s3"), ("s3", "s4"), ("s4", "s5"),
            ("s5", "s6"), ("s6", "s7"), ("s7", "s8"), ("s8", "s1")
        ]
        for u, v in ring_edges:
            self.addLink(switches[u], switches[v], bw=bw, delay=delay, loss=loss)
            
        # Chordal cross links (ensuring >= 3 disjoint paths between opposite nodes)
        chord_edges = [
            ("s1", "s5"),  # Long chord across the ring
            ("s2", "s6"),
            ("s3", "s7"),
            ("s4", "s8"),
            ("s1", "s4"),  # Medium chord
            ("s5", "s8")
        ]
        for u, v in chord_edges:
            self.addLink(switches[u], switches[v], bw=bw, delay=delay, loss=loss)

topos = {"meshtopo": (lambda: MeshTopo())}
