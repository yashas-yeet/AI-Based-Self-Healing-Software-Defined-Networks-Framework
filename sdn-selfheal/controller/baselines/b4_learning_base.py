"""
Baseline B4: Non-Temporal Learning Baseline Controller.
Evaluates a static instantaneous classifier without temporal window history or trend slopes.
Demonstrates the limitations of non-sequential ML (elevated false alarms on transient bursts and poor lead time).
"""

from controller.common.ryu_compat import (
    app_manager, ofp_event, CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls,
    ofproto_v1_3, hub, packet, ethernet, ether_types
)

import networkx as nx
import numpy as np
import time
from typing import Dict, Tuple, List, Optional

from controller.common.flow_manager import add_flow, delete_flow
from controller.common.topo_discovery import TopologyManager
from controller.common.stats_poller import StatsPoller

class NonTemporalLearningController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, model=None, threshold: float = 0.5, **kwargs):
        super(NonTemporalLearningController, self).__init__(*args, **kwargs)
        self.topo_mgr = TopologyManager(self.logger)
        self.stats_poller = StatsPoller(self.logger)
        self.host_locations: Dict[str, Tuple[int, int]] = {}
        self.model = model
        self.threshold = threshold
        self.degraded_links: set = set()
        self.reroute_events: List[Dict[str, Any]] = []

        self.monitor_thread = hub.spawn(self._inference_loop)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.topo_mgr.register_datapath(datapath)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        add_flow(datapath, priority=0, match=match, actions=actions)

    def _inference_loop(self):
        while True:
            for dp in list(self.topo_mgr.datapaths.values()):
                self.stats_poller.request_stats(dp)
            hub.sleep(1.0)
            self._run_instantaneous_inference()

    def _run_instantaneous_inference(self):
        for u, v, data in list(self.topo_mgr.graph.edges(data=True)):
            src_port = data.get("src_port")
            metrics = self.stats_poller.get_port_metrics(u, src_port)
            if not metrics:
                continue

            # Instantaneous vector: [tx_bps, rx_bps, drop_ratio, tx_drops_sec, rtt_ms] (no slopes, no history)
            instant_vec = np.array([[
                metrics.get("tx_bps", 0.0),
                metrics.get("rx_bps", 0.0),
                metrics.get("drop_ratio", 0.0),
                metrics.get("tx_drops_sec", 0.0),
                metrics.get("rtt_ms", 1.0)
            ]], dtype=np.float32)

            if self.model is not None:
                try:
                    p_fail = float(self.model.predict_proba(instant_vec)[0, 1])
                except Exception:
                    p_fail = 0.0
            else:
                # Default heuristic proxy if model weights not preloaded
                p_fail = min(1.0, metrics.get("drop_ratio", 0.0) * 10.0)

            link_key = (u, v)
            if p_fail >= self.threshold and link_key not in self.degraded_links:
                self.logger.warning(f"[B4-STATIC-ML] Failure predicted by static model on {u}->{v} (P={p_fail:.2f})")
                self.degraded_links.add(link_key)
                self.topo_mgr.graph[u][v]["weight"] = 1000.0
                self._recompute_and_flush()
                self.reroute_events.append({
                    "timestamp": time.time(),
                    "link": link_key,
                    "p_fail": p_fail,
                    "type": "B4_STATIC_ML"
                })
            elif p_fail < self.threshold and link_key in self.degraded_links:
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
            try:
                path = nx.shortest_path(self.topo_mgr.graph, source=dpid, target=dst_dpid, weight="weight")
                for i in range(len(path) - 1):
                    c_node = path[i]
                    n_node = path[i + 1]
                    egress = self.topo_mgr.get_egress_port(c_node, n_node)
                    if egress and c_node in self.topo_mgr.datapaths:
                        dp = self.topo_mgr.datapaths[c_node]
                        m = dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                        a = [dp.ofproto_parser.OFPActionOutput(egress)]
                        add_flow(dp, priority=1, match=m, actions=a, idle_timeout=60)

                first_egress = self.topo_mgr.get_egress_port(dpid, path[1]) if len(path) > 1 else dst_port
                actions = [parser.OFPActionOutput(first_egress)]
                out = parser.OFPPacketOut(
                    datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                    actions=actions, data=msg.data
                )
                datapath.send_msg(out)
            except nx.NetworkXNoPath:
                pass
        else:
            actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                actions=actions, data=msg.data
            )
            datapath.send_msg(out)
