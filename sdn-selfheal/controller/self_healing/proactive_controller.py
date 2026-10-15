"""
Proposed Method M: Proactive AI-Driven Self-Healing SDN Controller.
Integrates online telemetry, ML failure forecasting, risk-aware dynamic Dijkstra,
and Make-Before-Break (MBB) flow staging with hysteresis dampening.
"""

from controller.common.ryu_compat import (
    app_manager, ofp_event, CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls,
    ofproto_v1_3, hub, packet, ethernet, ether_types, topo_event
)

import networkx as nx
import time
from typing import Dict, Tuple, List, Optional, Any

from controller.common.flow_manager import add_flow, delete_flow
from controller.common.topo_discovery import TopologyManager
from controller.common.stats_poller import StatsPoller
from controller.self_healing.predictor_agent import PredictorAgent
from controller.self_healing.risk_routing import RiskAwareRoutingEngine
from controller.self_healing.mbb_orchestrator import MBBOrchestrator

class ProactiveSelfHealingController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(
        self,
        *args,
        model=None,
        scaler=None,
        alarm_threshold: float = 0.70,
        cooldown_sec: float = 15.0,
        **kwargs
    ):
        super(ProactiveSelfHealingController, self).__init__(*args, **kwargs)
        self.topo_mgr = TopologyManager(self.logger)
        self.stats_poller = StatsPoller(self.logger)
        self.predictor = PredictorAgent(
            model=model,
            scaler=scaler,
            alarm_threshold=alarm_threshold,
            cooldown_sec=cooldown_sec
        )
        self.risk_engine = RiskAwareRoutingEngine()
        self.mbb = MBBOrchestrator(self.logger)

        self.host_locations: Dict[str, Tuple[int, int]] = {}
        # Track active paths per dst_mac: dst_mac -> List[int]
        self.active_paths: Dict[str, List[int]] = {}
        self.proactive_events: List[Dict[str, Any]] = []

        # Start 1Hz monitor and inference thread
        self.monitor_thread = hub.spawn(self._monitor_and_heal_loop)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.topo_mgr.register_datapath(datapath)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        add_flow(datapath, priority=0, match=match, actions=actions)

    def _monitor_and_heal_loop(self):
        """Periodic 1Hz telemetry polling, ML inference, and proactive self-healing."""
        while True:
            # 1. Request port stats
            for dp in list(self.topo_mgr.datapaths.values()):
                self.stats_poller.request_stats(dp)
            hub.sleep(1.0)

            # 2. Update telemetry in predictor and risk engine
            telemetry_snapshot = {}
            alarms_triggered = []

            for u, v, data in list(self.topo_mgr.graph.edges(data=True)):
                src_port = data.get("src_port")
                metrics = self.stats_poller.get_port_metrics(u, src_port)
                if not metrics:
                    continue
                telemetry_snapshot[(u, v)] = metrics
                p_fail, should_alarm = self.predictor.update_telemetry(u, v, metrics)
                if should_alarm:
                    alarms_triggered.append(((u, v), p_fail))

            # 3. Update risk weights on the graph
            self.risk_engine.update_graph_costs(
                self.topo_mgr.graph,
                self.predictor.latest_predictions,
                telemetry_snapshot
            )

            # 4. If any alarm was raised, check if any active path traverses the at-risk link
            for (at_risk_edge, p_fail) in alarms_triggered:
                u_risk, v_risk = at_risk_edge
                self.logger.warning(
                    f"[PROACTIVE-M] High failure risk predicted on link {u_risk}->{v_risk} "
                    f"(P={p_fail:.2f}). Checking active traffic paths..."
                )
                self._proactively_heal_edge(u_risk, v_risk, p_fail)

    def _proactively_heal_edge(self, u_risk: int, v_risk: int, p_fail: float):
        """Finds any active flows using the at-risk link and reroutes them via MBB."""
        for dst_mac, cur_path in list(self.active_paths.items()):
            # Check if (u_risk, v_risk) is part of cur_path
            path_traverses = False
            for i in range(len(cur_path) - 1):
                if cur_path[i] == u_risk and cur_path[i + 1] == v_risk:
                    path_traverses = True
                    break

            if path_traverses:
                src_dpid = cur_path[0]
                dst_dpid = cur_path[-1]

                # Compute minimal risk alternative path
                alt_path = self.risk_engine.find_best_path(self.topo_mgr.graph, src_dpid, dst_dpid)
                if alt_path and alt_path != cur_path:
                    self.logger.warning(
                        f"[PROACTIVE-M] Rerouting dst {dst_mac} from old path {cur_path} -> new path {alt_path}"
                    )
                    # Execute zero-loss Make-Before-Break migration
                    self.mbb.execute_mbb_migration(
                        datapaths=self.topo_mgr.datapaths,
                        topo_mgr=self.topo_mgr,
                        alt_path=alt_path,
                        dst_mac=dst_mac,
                        priority=3,
                        cookie=0xAA02
                    )
                    self.active_paths[dst_mac] = alt_path
                    self.proactive_events.append({
                        "timestamp": time.time(),
                        "at_risk_edge": (u_risk, v_risk),
                        "p_fail": p_fail,
                        "old_path": cur_path,
                        "new_path": alt_path,
                        "dst_mac": dst_mac
                    })

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
            self._install_initial_path(src_mac, dst_mac, dpid, dst_dpid, dst_port, msg)
        else:
            actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_FLOOD)]
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                actions=actions, data=msg.data
            )
            datapath.send_msg(out)

    def _install_initial_path(self, src_mac: str, dst_mac: str, src_dpid: int, dst_dpid: int, dst_port: int, msg):
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

        best_path = self.risk_engine.find_best_path(self.topo_mgr.graph, src_dpid, dst_dpid)
        if not best_path:
            return

        self.active_paths[dst_mac] = best_path

        for i in range(len(best_path) - 1):
            cur_sw = best_path[i]
            nxt_sw = best_path[i + 1]
            egress = self.topo_mgr.get_egress_port(cur_sw, nxt_sw)
            if egress and cur_sw in self.topo_mgr.datapaths:
                dp = self.topo_mgr.datapaths[cur_sw]
                m = dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                a = [dp.ofproto_parser.OFPActionOutput(egress)]
                add_flow(dp, priority=1, match=m, actions=a, idle_timeout=60)

        first_egress = self.topo_mgr.get_egress_port(src_dpid, best_path[1])
        if first_egress:
            actions = [parser.OFPActionOutput(first_egress)]
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.match['in_port'],
                actions=actions, data=msg.data
            )
            datapath.send_msg(out)

    @set_ev_cls(topo_event.EventLinkAdd)
    def link_add_handler(self, ev):
        l = ev.link
        self.topo_mgr.add_link(l.src.dpid, l.src.port_no, l.dst.dpid, l.dst.port_no)

    @set_ev_cls(topo_event.EventLinkDelete)
    def link_delete_handler(self, ev):
        l = ev.link
        self.topo_mgr.remove_link(l.src.dpid, l.dst.dpid)
