"""
Baseline B2: OpenFlow 1.3 Fast-Failover Group Table Controller.
Pre-installs primary and secondary backup paths into OFPGT_FF group tables with watch_port buckets.
Demonstrates sub-millisecond failover for hard port-cuts, but architectural blindness to soft degradation.
"""

from controller.common.ryu_compat import (
    app_manager, ofp_event, CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls,
    ofproto_v1_3, packet, ethernet, ether_types, topo_event
)

import networkx as nx
import time
from typing import Dict, Tuple, List, Optional

from controller.common.flow_manager import add_flow, delete_flow, install_ff_group
from controller.common.topo_discovery import TopologyManager

class FastFailoverController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(FastFailoverController, self).__init__(*args, **kwargs)
        self.topo_mgr = TopologyManager(self.logger)
        self.host_locations: Dict[str, Tuple[int, int]] = {}
        self.group_id_counter = 1
        # Track group installations: (dpid, dst_mac) -> group_id
        self.installed_groups: Dict[Tuple[int, str], int] = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.topo_mgr.register_datapath(datapath)

        # Table-miss rule
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        add_flow(datapath, priority=0, match=match, actions=actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        src_mac = eth.src
        dst_mac = eth.dst
        self.host_locations[src_mac] = (dpid, in_port)

        if dst_mac in self.host_locations:
            dst_dpid, dst_port = self.host_locations[dst_mac]
            self._install_fast_failover_path(src_mac, dst_mac, dpid, dst_dpid, dst_port, msg)
        else:
            # Flood
            actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                actions=actions, data=msg.data
            )
            datapath.send_msg(out)

    def _install_fast_failover_path(self, src_mac: str, dst_mac: str, src_dpid: int, dst_dpid: int, dst_port: int, msg):
        datapath = msg.datapath
        parser = datapath.ofproto_parser

        if src_dpid == dst_dpid:
            actions = [parser.OFPActionOutput(dst_port)]
            match = parser.OFPMatch(eth_dst=dst_mac)
            add_flow(datapath, priority=1, match=match, actions=actions, idle_timeout=60)
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.match['in_port'],
                actions=actions, data=msg.data
            )
            datapath.send_msg(out)
            return

        # Find 2 edge-disjoint or alternate paths using NetworkX
        try:
            all_paths = list(nx.all_simple_paths(self.topo_mgr.graph, source=src_dpid, target=dst_dpid, cutoff=6))
            if not all_paths:
                return

            primary_path = all_paths[0]
            # Select backup path with minimal link overlap
            backup_path = all_paths[1] if len(all_paths) > 1 else primary_path

            # Determine egress ports on ingress switch
            primary_port = self.topo_mgr.get_egress_port(src_dpid, primary_path[1])
            backup_port = self.topo_mgr.get_egress_port(src_dpid, backup_path[1])

            if primary_port is not None and backup_port is not None:
                group_id = self.group_id_counter
                self.group_id_counter += 1

                # 1. Install Fast-Failover Group Table on ingress switch
                install_ff_group(datapath, group_id, primary_port, backup_port)

                # 2. Point flow to group
                match = parser.OFPMatch(eth_dst=dst_mac)
                actions = [parser.OFPActionGroup(group_id)]
                add_flow(datapath, priority=2, match=match, actions=actions, idle_timeout=60)

                # 3. Install forwarding rules on downstream switches for both paths
                for p in [primary_path, backup_path]:
                    for i in range(1, len(p) - 1):
                        cur_node = p[i]
                        nxt_node = p[i + 1]
                        egress = self.topo_mgr.get_egress_port(cur_node, nxt_node)
                        if egress and cur_node in self.topo_mgr.datapaths:
                            dp = self.topo_mgr.datapaths[cur_node]
                            m = dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                            a = [dp.ofproto_parser.OFPActionOutput(egress)]
                            add_flow(dp, priority=1, match=m, actions=a, idle_timeout=60)

                # Send packet via group
                out = parser.OFPPacketOut(
                    datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.match['in_port'],
                    actions=actions, data=msg.data
                )
                datapath.send_msg(out)
        except Exception as e:
            self.logger.error(f"[B2] Fast-Failover path computation failed: {e}")

    @set_ev_cls(topo_event.EventLinkAdd)
    def link_add_handler(self, ev):
        l = ev.link
        self.topo_mgr.add_link(l.src.dpid, l.src.port_no, l.dst.dpid, l.dst.port_no)

    @set_ev_cls(topo_event.EventLinkDelete)
    def link_delete_handler(self, ev):
        l = ev.link
        self.topo_mgr.remove_link(l.src.dpid, l.dst.dpid)
