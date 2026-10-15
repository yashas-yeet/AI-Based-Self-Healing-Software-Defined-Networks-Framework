"""
Topology utilities for sdn-selfheal.
Provides helpers for Mininet topologies, MAC/IP assignments, graph extraction, and link tagging.
"""

import networkx as nx
from typing import Dict, Any, List, Tuple

def assign_host_config(index: int) -> Dict[str, str]:
    """Generates standardized IP and MAC address for host index (1-based)."""
    ip = f"10.0.0.{index}/24"
    mac = f"00:00:00:00:00:{index:02x}"
    return {"ip": ip, "mac": mac}

def mininet_to_networkx(topo) -> nx.DiGraph:
    """
    Converts a Mininet Topo object into a directed NetworkX graph.
    Annotates nodes with type ('switch' or 'host') and edges with latency, bandwidth, and ports.
    """
    G = nx.DiGraph()
    
    # Add switches
    for sw in topo.switches():
        G.add_node(sw, node_type="switch")
        
    # Add hosts
    for h in topo.hosts():
        G.add_node(h, node_type="host")
        
    # Add links with bidirectional edge attributes
    for src, dst in topo.links():
        link_opts = topo.linkInfo(src, dst)
        delay = link_opts.get("delay", "1ms")
        # Parse delay to float in milliseconds
        delay_ms = float(delay.replace("ms", "").replace("s", "000")) if isinstance(delay, str) else 1.0
        bw = float(link_opts.get("bw", 10.0))
        loss = float(link_opts.get("loss", 0.0))
        
        # Link ports
        port1, port2 = topo.port(src, dst)
        
        # Add forward edge
        G.add_edge(
            src, dst,
            src_port=port1,
            dst_port=port2,
            delay=delay_ms,
            bw=bw,
            loss=loss,
            weight=delay_ms
        )
        
        # Add reverse edge
        G.add_edge(
            dst, src,
            src_port=port2,
            dst_port=port1,
            delay=delay_ms,
            bw=bw,
            loss=loss,
            weight=delay_ms
        )
        
    return G

def get_switch_dpid(switch_name: str) -> int:
    """Extracts integer datapath ID (DPID) from switch name (e.g., 's1' -> 1)."""
    if switch_name.startswith("s"):
        return int(switch_name[1:])
    return int(switch_name)
