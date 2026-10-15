"""
Risk-Aware Dynamic Routing Engine for Self-Healing SDN.
Calculates multi-objective edge weights combining physical propagation latency,
bandwidth utilization, and AI-predicted failure probability via an asymptotic barrier function.
"""

import networkx as nx
from typing import Dict, Tuple, List, Optional

class RiskAwareRoutingEngine:
    """
    Computes optimal paths using dynamic risk costs:
    Cost(e) = alpha * (Latency / BaseLatency) + beta * Util + gamma * (1 / (1 - P_fail + eps))
    """
    def __init__(
        self,
        alpha: float = 1.0,     # Weight for latency
        beta: float = 0.5,      # Weight for utilization
        gamma: float = 2.0,     # Weight for failure risk barrier
        base_latency_ms: float = 2.0,
        eps: float = 1e-3
    ):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.base_latency_ms = base_latency_ms
        self.eps = eps

    def compute_edge_cost(self, latency_ms: float, utilization: float, p_fail: float) -> float:
        """Evaluates edge cost function."""
        # Latency normalized component
        norm_lat = max(0.1, latency_ms / self.base_latency_ms)
        # Utilization component
        util_cost = max(0.0, min(1.0, utilization))
        # Barrier function: diverges to infinity as P_fail -> 1
        p_clamped = min(0.999, max(0.0, p_fail))
        risk_barrier = 1.0 / (1.0 - p_clamped + self.eps)

        total_cost = (self.alpha * norm_lat) + (self.beta * util_cost) + (self.gamma * risk_barrier)
        return float(total_cost)

    def update_graph_costs(
        self,
        graph: nx.DiGraph,
        predictions: Dict[Tuple[int, int], float],
        telemetry: Dict[Tuple[int, int], Dict[str, float]]
    ):
        """Annotates all edges in the NetworkX graph with risk-aware costs."""
        for u, v in graph.edges():
            key = (u, v)
            p_fail = predictions.get(key, 0.0)
            metrics = telemetry.get(key, {})
            lat_ms = metrics.get("rtt_ms", graph[u][v].get("delay", self.base_latency_ms))
            util = metrics.get("utilization", 0.0)

            cost = self.compute_edge_cost(lat_ms, util, p_fail)
            graph[u][v]["risk_cost"] = cost
            graph[u][v]["p_fail"] = p_fail

    def find_best_path(self, graph: nx.DiGraph, src: int, dst: int) -> Optional[List[int]]:
        """Computes shortest path based on dynamic risk_cost attribute."""
        try:
            return nx.shortest_path(graph, source=src, target=dst, weight="risk_cost")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
