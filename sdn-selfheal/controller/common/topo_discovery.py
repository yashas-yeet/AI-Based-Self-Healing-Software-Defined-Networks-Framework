"""
Topology Discovery and Dynamic Graph Synchronization for Ryu.
Synchronizes OpenFlow 1.3 switch connections and LLDP link events into a live NetworkX DiGraph.
"""

from controller.common.ryu_compat import (
    app_manager, ofp_event, CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls,
    ofproto_v1_3, topo_event, get_switch, get_link
)

import networkx as nx
from typing import Dict, Tuple, Optional, Set

class TopologyManager:
    """
    Manages live topology state, mapping DPIDs, ports, and NetworkX graph edges.
    """
    def __init__(self, logger):
        self.logger = logger
        self.graph = nx.DiGraph()
        self.datapaths: Dict[int, Any] = {}
        # (src_dpid, dst_dpid) -> (src_port, dst_port)
        self.link_ports: Dict[Tuple[int, int], Tuple[int, int]] = {}
        # mac -> (dpid, port)
        self.mac_to_port: Dict[str, Tuple[int, int]] = {}

    def register_datapath(self, datapath):
        dpid = datapath.id
        self.datapaths[dpid] = datapath
        if not self.graph.has_node(dpid):
            self.graph.add_node(dpid, type="switch")
        self.logger.info(f"[TopoManager] Datapath registered: dpid=0x{dpid:016x}")

    def unregister_datapath(self, datapath):
        dpid = datapath.id
        if dpid in self.datapaths:
            del self.datapaths[dpid]
        if self.graph.has_node(dpid):
            self.graph.remove_node(dpid)
        self.logger.info(f"[TopoManager] Datapath unregistered: dpid=0x{dpid:016x}")

    def add_link(self, src_dpid: int, src_port: int, dst_dpid: int, dst_port: int, weight: float = 1.0):
        self.link_ports[(src_dpid, dst_dpid)] = (src_port, dst_port)
        self.graph.add_edge(
            src_dpid, dst_dpid,
            src_port=src_port,
            dst_port=dst_port,
            weight=weight,
            status="UP"
        )
        self.logger.info(f"[TopoManager] Link UP: dpid 0x{src_dpid:x}:p{src_port} -> dpid 0x{dst_dpid:x}:p{dst_port}")

    def remove_link(self, src_dpid: int, dst_dpid: int):
        if (src_dpid, dst_dpid) in self.link_ports:
            del self.link_ports[(src_dpid, dst_dpid)]
        if self.graph.has_edge(src_dpid, dst_dpid):
            self.graph.remove_edge(src_dpid, dst_dpid)
        self.logger.warning(f"[TopoManager] Link DOWN: dpid 0x{src_dpid:x} -> dpid 0x{dst_dpid:x}")

    def learn_mac(self, mac: str, dpid: int, port: int):
        self.mac_to_port[mac] = (dpid, port)

    def get_egress_port(self, dpid: int, next_dpid: int) -> Optional[int]:
        if (dpid, next_dpid) in self.link_ports:
            return self.link_ports[(dpid, next_dpid)][0]
        return None
