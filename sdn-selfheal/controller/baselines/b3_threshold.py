"""
Baseline B3: Static Threshold Heuristic Controller.
Monitors instantaneous link drop ratio and RTT. If metrics exceed hard thresholds
(e.g., Loss > 3% or Latency > 25ms), reroutes traffic reactively without predictive forecasting.
"""

from controller.common.ryu_compat import (
    app_manager, ofp_event, CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls,
    ofproto_v1_3, hub, packet, ethernet, ether_types
)

import networkx as nx
import time
from typing import Dict, Tuple, List, Optional

from controller.common.flow_manager import add_flow, delete_flow
from controller.common.topo_discovery import TopologyManager
from controller.common.stats_poller import StatsPoller

class ThresholdHeuristicController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(
        self,
        *args,
        loss_threshold: float = 0.03,      # 3% drop ratio
        latency_threshold_ms: float = 25.0, # 25ms RTT
        util_threshold: float = 0.85,       # 85% bandwidth utilization
        **kwargs
    ):
        super(ThresholdHeuristicController, self).__init__(*args, **kwargs)
        self.topo_mgr = TopologyManager(self.logger)
        self.stats_poller = StatsPoller(self.logger)
        self.host_locations: Dict[str, Tuple[int, int]] = {}

        self.loss_threshold = loss_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.util_threshold = util_threshold

        self.degraded_links: set = set()
        self.reroute_events: List[Dict[str, Any]] = []

        # Start 1Hz monitor thread
        self.monitor_thread = hub.spawn(self._monitor_loop)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.topo_mgr.register_datapath(datapath)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        add_flow(datapath, priority=0, match=match, actions=actions)

    def _monitor_loop(self):
        """Polls switch statistics and inspects thresholds every 1 second."""
        while True:
            for dp in list(self.topo_mgr.datapaths.values()):
                self.stats_poller.request_stats(dp)
            hub.sleep(1.0)
            self._evaluate_thresholds()

    def _evaluate_thresholds(self):
        """Checks if any active link exceeds static threshold."""
        for u, v, data in list(self.topo_mgr.graph.edges(data=True)):
            src_port = data.get("src_port")
            metrics = self.stats_poller.get_port_metrics(u, src_port)
            if not metrics:
                continue

            drop_ratio = metrics.get("drop_ratio", 0.0)
            # Estimate latency from delay or metric
            rtt_ms = metrics.get("rtt_ms", data.get("delay", 1.0))
            util = metrics.get("tx_bps", 0.0) / 100e6

            is_degraded = (drop_ratio >= self.loss_threshold) or (rtt_ms >= self.latency_threshold_ms) or (util >= self.util_threshold)
            link_key = (u, v)

            if is_degraded and link_key not in self.degraded_links:
                self.logger.warning(
                    f"[B3-THRESHOLD] Threshold breached on link {u}->{v} (Loss: {drop_ratio*100:.1f}%, RTT: {rtt_ms:.1f}ms). Rerouting..."
                )
                self.degraded_links.add(link_key)
                # Penalize link weight heavily
                self.topo_mgr.graph[u][v]["weight"] = 1000.0
                self._recompute_and_flush()
                self.reroute_events.append({
                    "timestamp": time.time(),
                    "link": link_key,
                    "reason": "THRESHOLD_EXCEEDED",
                    "drop_ratio": drop_ratio,
                    "rtt_ms": rtt_ms
                })
            elif not is_degraded and link_key in self.degraded_links:
                # Recover link
                self.degraded_links.remove(link_key)
                self.topo_mgr.graph[u][v]["weight"] = data.get("delay", 1.0)
                self._recompute_and_flush()

    def _recompute_and_flush(self):
        for dp in self.topo_mgr.datapaths.values():
            parser = dp.ofproto_parser
            match = parser.OFPMatch()
            delete_flow(dp, match=match)
            actions = [parser.OFPActionOutput(dp.ofproto.OFPP_CONTROLLER, dp.ofproto.OFPCML_NO_BUFFER)]
            add_flow(dp, priority=0, match=match, actions=actions)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        self.stats_poller.handle_port_stats_reply(ev)

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
            self._install_shortest_path(src_mac, dst_mac, dpid, dst_dpid, dst_port, msg)
        else:
            actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                actions=actions, data=msg.data
            )
            datapath.send_msg(out)

    def _install_shortest_path(self, src_mac: str, dst_mac: str, src_dpid: int, dst_dpid: int, dst_port: int, msg):
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

        try:
            path = nx.shortest_path(self.topo_mgr.graph, source=src_dpid, target=dst_dpid, weight="weight")
            for i in range(len(path) - 1):
                cur_node = path[i]
                nxt_node = path[i + 1]
                egress = self.topo_mgr.get_egress_port(cur_node, nxt_node)
                if egress and cur_node in self.topo_mgr.datapaths:
                    dp = self.topo_mgr.datapaths[cur_node]
                    m = dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                    a = [dp.ofproto_parser.OFPActionOutput(egress)]
                    add_flow(dp, priority=1, match=m, actions=a, idle_timeout=60)

            first_egress = self.topo_mgr.get_egress_port(src_dpid, path[1])
            if first_egress:
                actions = [parser.OFPActionOutput(first_egress)]
                out = parser.OFPPacketOut(
                    datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.match['in_port'],
                    actions=actions, data=msg.data
                )
                datapath.send_msg(out)
        except nx.NetworkXNoPath:
            self.logger.error(f"[B3] No path between {src_dpid} and {dst_dpid}")
