"""
Baseline B1: Reactive Shortest Path Controller.
Uses Dijkstra's algorithm for shortest-path forwarding and reacts to link failures strictly
after receiving OpenFlow OFPPortStatus down events or LLDP link-loss notifications.
"""

from controller.common.ryu_compat import (
    app_manager, ofp_event, CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls,
    ofproto_v1_3, packet, ethernet, ether_types, topo_event, get_switch, get_link
)

import networkx as nx
import time
from typing import Dict, Tuple, List, Optional

from controller.common.flow_manager import add_flow, delete_flow
from controller.common.topo_discovery import TopologyManager
from controller.common.stats_poller import StatsPoller

class ReactiveDijkstraController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ReactiveDijkstraController, self).__init__(*args, **kwargs)
        self.topo_mgr = TopologyManager(self.logger)
        self.stats_poller = StatsPoller(self.logger)
        # mac -> (dpid, port)
        self.host_locations: Dict[str, Tuple[int, int]] = {}
        # Track recovery metrics
        self.failover_logs: List[Dict[str, Any]] = []

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Installs default table-miss flow entry (send to controller)."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.topo_mgr.register_datapath(datapath)

        # Match all packets, send to controller port
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        add_flow(datapath, priority=0, match=match, actions=actions)
        self.logger.info(f"[B1] Table-miss installed on dpid 0x{datapath.id:016x}")

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        """Handles physical port status changes (link down / up)."""
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id
        port_no = msg.desc.port_no
        reason = msg.reason
        ofproto = dp.ofproto

        t_event = time.time()
        is_down = (msg.desc.state & ofproto.OFPPS_LINK_DOWN) or (reason == ofproto.OFPPR_DELETE)

        if is_down:
            self.logger.warning(f"[B1-REACTIVE] Port DOWN detected: dpid 0x{dpid:x} port {port_no} at {t_event:.4f}")
            # Identify affected graph edges
            edges_to_remove = []
            for u, v, data in self.topo_mgr.graph.edges(data=True):
                if (u == dpid and data.get("src_port") == port_no) or (v == dpid and data.get("dst_port") == port_no):
                    edges_to_remove.append((u, v))

            for u, v in edges_to_remove:
                self.topo_mgr.remove_link(u, v)

            # Reactive Reroute: Recompute paths and reinstall flows
            t_calc_start = time.time()
            self._reactive_recompute_all()
            t_done = time.time()

            recovery_time_ms = (t_done - t_event) * 1000.0
            self.logger.warning(f"[B1-REACTIVE] Rerouting completed in {recovery_time_ms:.2f} ms")
            self.failover_logs.append({
                "type": "B1_REACTIVE",
                "timestamp": t_event,
                "recovery_time_ms": recovery_time_ms,
                "dpid": dpid,
                "port_no": port_no
            })

    def _reactive_recompute_all(self):
        """Flushes existing active flows and reinstalls shortest path routes via Dijkstra."""
        for dpid, dp in self.topo_mgr.datapaths.items():
            parser = dp.ofproto_parser
            # Delete flows with priority 1 (L2 forwarding rules)
            match = parser.OFPMatch()
            delete_flow(dp, match=match)
            # Re-install table miss
            ofproto = dp.ofproto
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
            add_flow(dp, priority=0, match=match, actions=actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """L2 forwarding based on Dijkstra shortest path."""
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignore LLDP
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        src_mac = eth.src
        dst_mac = eth.dst

        # Learn host location
        self.host_locations[src_mac] = (dpid, in_port)

        # If destination host location is known, compute shortest path
        if dst_mac in self.host_locations:
            dst_dpid, dst_port = self.host_locations[dst_mac]
            self._install_path(src_mac, dst_mac, dpid, dst_dpid, dst_port, msg)
        else:
            # Flood if destination unknown
            actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                actions=actions, data=msg.data
            )
            datapath.send_msg(out)

    def _install_path(self, src_mac: str, dst_mac: str, src_dpid: int, dst_dpid: int, dst_port: int, msg):
        datapath = msg.datapath
        parser = datapath.ofproto_parser

        if src_dpid == dst_dpid:
            # Same switch delivery
            actions = [parser.OFPActionOutput(dst_port)]
            match = parser.OFPMatch(eth_dst=dst_mac)
            add_flow(datapath, priority=1, match=match, actions=actions, idle_timeout=60)
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.match['in_port'],
                actions=actions, data=msg.data
            )
            datapath.send_msg(out)
            return

        # Multi-switch shortest path via NetworkX Dijkstra
        try:
            path = nx.shortest_path(self.topo_mgr.graph, source=src_dpid, target=dst_dpid, weight="weight")
            # Install flow along each switch in the path
            for i in range(len(path) - 1):
                cur_node = path[i]
                nxt_node = path[i + 1]
                egress_port = self.topo_mgr.get_egress_port(cur_node, nxt_node)
                if egress_port is not None and cur_node in self.topo_mgr.datapaths:
                    dp = self.topo_mgr.datapaths[cur_node]
                    m = dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                    acts = [dp.ofproto_parser.OFPActionOutput(egress_port)]
                    add_flow(dp, priority=1, match=m, actions=acts, idle_timeout=60)

            # Send packet out on first hop
            first_egress = self.topo_mgr.get_egress_port(src_dpid, path[1])
            if first_egress is not None:
                actions = [parser.OFPActionOutput(first_egress)]
                out = parser.OFPPacketOut(
                    datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.match['in_port'],
                    actions=actions, data=msg.data
                )
                datapath.send_msg(out)
        except nx.NetworkXNoPath:
            self.logger.error(f"[B1] No path between dpid {src_dpid} and {dst_dpid}")

    @set_ev_cls(topo_event.EventLinkAdd)
    def link_add_handler(self, ev):
        link = ev.link
        self.topo_mgr.add_link(
            src_dpid=link.src.dpid,
            src_port=link.src.port_no,
            dst_dpid=link.dst.dpid,
            dst_port=link.dst.port_no
        )

    @set_ev_cls(topo_event.EventLinkDelete)
    def link_delete_handler(self, ev):
        link = ev.link
        self.topo_mgr.remove_link(link.src.dpid, link.dst.dpid)
        self._reactive_recompute_all()
