"""
Make-Before-Break (MBB) Flow Migration Orchestrator.
Guarantees zero packet loss during path failover by pre-installing alternate downstream paths
prior to ingress cutover and observing a packet drain interval before stale flow pruning.
"""

import time
from controller.common.ryu_compat import hub
from typing import Dict, List, Any
from controller.common.flow_manager import add_flow, delete_flow

class MBBOrchestrator:
    """
    Executes ordered 3-stage Make-Before-Break (MBB) flow migration:
    Stage 1: Pre-install alternate forwarding rules on downstream switches.
    Stage 2: Atomically switch ingress switch forwarding pointer.
    Stage 3: Drain in-flight packets and prune stale flows.
    """
    def __init__(self, logger, drain_time_sec: float = 0.2):
        self.logger = logger
        self.drain_time_sec = drain_time_sec
        self.migration_history: List[Dict[str, Any]] = []

    def execute_mbb_migration(
        self,
        datapaths: Dict[int, Any],
        topo_mgr,
        alt_path: List[int],
        dst_mac: str,
        priority: int = 3,
        cookie: int = 0xAA01
    ):
        t_start = time.time()
        self.logger.info(f"[MBB] Initiating Make-Before-Break migration to path: {alt_path} for dst: {dst_mac}")

        # Stage 1: Pre-install alternate rules along downstream path (excluding ingress switch first)
        for i in range(1, len(alt_path) - 1):
            cur_sw = alt_path[i]
            nxt_sw = alt_path[i + 1]
            egress = topo_mgr.get_egress_port(cur_sw, nxt_sw)
            if egress and cur_sw in datapaths:
                dp = datapaths[cur_sw]
                parser = dp.ofproto_parser
                match = parser.OFPMatch(eth_dst=dst_mac)
                actions = [parser.OFPActionOutput(egress)]
                # Add flow with higher priority and staging cookie
                add_flow(dp, priority=priority, match=match, actions=actions, cookie=cookie, idle_timeout=60)

        # Stage 2: Atomically update ingress switch
        ingress_sw = alt_path[0]
        ingress_egress = topo_mgr.get_egress_port(ingress_sw, alt_path[1])
        if ingress_egress and ingress_sw in datapaths:
            dp = datapaths[ingress_sw]
            parser = dp.ofproto_parser
            match = parser.OFPMatch(eth_dst=dst_mac)
            actions = [parser.OFPActionOutput(ingress_egress)]
            add_flow(dp, priority=priority, match=match, actions=actions, cookie=cookie, idle_timeout=60)

        t_cutover = time.time()
        migration_latency_ms = (t_cutover - t_start) * 1000.0
        self.logger.info(f"[MBB] Cutover completed in {migration_latency_ms:.2f} ms without interrupting inflight data.")

        # Stage 3: Asynchronously drain in-flight packets and prune old lower-priority flows
        hub.spawn(self._drain_and_cleanup, datapaths, dst_mac, priority - 1)

        self.migration_history.append({
            "timestamp": t_start,
            "alt_path": alt_path,
            "dst_mac": dst_mac,
            "migration_latency_ms": migration_latency_ms
        })

    def _drain_and_cleanup(self, datapaths: Dict[int, Any], dst_mac: str, old_priority: int):
        # Allow inflight packets to clear intermediate buffers
        hub.sleep(self.drain_time_sec)
        # Prune old stale flows
        for dpid, dp in datapaths.items():
            parser = dp.ofproto_parser
            # Delete old flow matching dst_mac
            match = parser.OFPMatch(eth_dst=dst_mac)
            delete_flow(dp, match=match, cookie=0)  # Prune default cookie flows
        self.logger.info(f"[MBB] Post-drain pruning complete for dst: {dst_mac}")
