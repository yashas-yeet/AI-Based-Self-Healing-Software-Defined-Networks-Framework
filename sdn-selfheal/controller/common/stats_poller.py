"""
Asynchronous OpenFlow 1.3 Port and Flow Statistics Poller for Ryu.
Polls switches at 1Hz, computes instantaneous byte/packet rates, drop ratios, and maintains telemetry cache.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple, List, Optional
from controller.common.ryu_compat import ofproto_v1_3

class PortStatRecord:
    def __init__(self, tx_bytes: int, rx_bytes: int, tx_packets: int, rx_packets: int,
                 tx_dropped: int, rx_dropped: int, tx_errors: int, rx_errors: int, timestamp: float):
        self.tx_bytes = tx_bytes
        self.rx_bytes = rx_bytes
        self.tx_packets = tx_packets
        self.rx_packets = rx_packets
        self.tx_dropped = tx_dropped
        self.rx_dropped = rx_dropped
        self.tx_errors = tx_errors
        self.rx_errors = rx_errors
        self.timestamp = timestamp

class StatsPoller:
    """
    Maintains rate-based telemetry for all switch ports.
    """
    def __init__(self, logger):
        self.logger = logger
        # (dpid, port_no) -> PortStatRecord
        self.prev_stats: Dict[Tuple[int, int], PortStatRecord] = {}
        # (dpid, port_no) -> latest computed metrics dict
        self.latest_metrics: Dict[Tuple[int, int], Dict[str, float]] = {}

    def request_stats(self, datapath):
        """Dispatches an OFPPortStatsRequest to a datapath."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    def handle_port_stats_reply(self, ev):
        """Processes OFPPortStatsReply and computes delta rates."""
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        now = time.time()

        for stat in body:
            port_no = stat.port_no
            # Ignore local virtual port
            if port_no > ofproto_v1_3.OFPP_MAX:
                continue

            current = PortStatRecord(
                tx_bytes=stat.tx_bytes,
                rx_bytes=stat.rx_bytes,
                tx_packets=stat.tx_packets,
                rx_packets=stat.rx_packets,
                tx_dropped=stat.tx_dropped,
                rx_dropped=stat.rx_dropped,
                tx_errors=stat.tx_errors,
                rx_errors=stat.rx_errors,
                timestamp=now
            )

            key = (dpid, port_no)
            if key in self.prev_stats:
                prev = self.prev_stats[key]
                dt = current.timestamp - prev.timestamp
                if dt > 0.05:  # Avoid division by zero
                    tx_bps = (current.tx_bytes - prev.tx_bytes) * 8.0 / dt
                    rx_bps = (current.rx_bytes - prev.rx_bytes) * 8.0 / dt
                    tx_pps = (current.tx_packets - prev.tx_packets) / dt
                    rx_pps = (current.rx_packets - prev.rx_packets) / dt
                    tx_drops_sec = (current.tx_dropped - prev.tx_dropped) / dt
                    rx_drops_sec = (current.rx_dropped - prev.rx_dropped) / dt
                    tx_errors_sec = (current.tx_errors - prev.tx_errors) / dt

                    total_tx_pkts = (current.tx_packets - prev.tx_packets)
                    drop_ratio = (current.tx_dropped - prev.tx_dropped) / max(1, total_tx_pkts + (current.tx_dropped - prev.tx_dropped))

                    self.latest_metrics[key] = {
                        "dpid": dpid,
                        "port_no": port_no,
                        "timestamp": now,
                        "tx_bps": max(0.0, tx_bps),
                        "rx_bps": max(0.0, rx_bps),
                        "tx_pps": max(0.0, tx_pps),
                        "rx_pps": max(0.0, rx_pps),
                        "tx_drops_sec": max(0.0, tx_drops_sec),
                        "rx_drops_sec": max(0.0, rx_drops_sec),
                        "tx_errors_sec": max(0.0, tx_errors_sec),
                        "drop_ratio": min(1.0, max(0.0, drop_ratio))
                    }

            self.prev_stats[key] = current

    def get_port_metrics(self, dpid: int, port_no: int) -> Optional[Dict[str, float]]:
        return self.latest_metrics.get((dpid, port_no), None)
