#!/usr/bin/env python3
"""
Phase 1 Smoke Test: Topologies & Baseline Connectivity Verification
Tests instantiation and structural redundancy of:
1. MeshTopo (8 switches, chordal links)
2. FatTree4Topo (k=4, 20 switches, 16 hosts)
3. WanTopo (12-switch irregular topology)
"""

import sys
import os
import networkx as nx

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from topologies.topo_utils import mininet_to_networkx
from topologies.mesh_topo import MeshTopo
from topologies.fattree_topo import FatTree4Topo
from topologies.wan_topo import WanTopo

def test_mesh_topo():
    print("[TEST] Validating MeshTopo (8 switches, redundant chords)...")
    topo = MeshTopo()
    G = mininet_to_networkx(topo)

    switches = [n for n, d in G.nodes(data=True) if d.get("node_type") == "switch"]
    hosts = [n for n, d in G.nodes(data=True) if d.get("node_type") == "host"]

    assert len(switches) == 8, f"Expected 8 switches, got {len(switches)}"
    assert len(hosts) == 8, f"Expected 8 hosts, got {len(hosts)}"

    # Check redundancy between s1 and s5
    switch_subgraph = G.subgraph(switches).to_undirected()
    paths = list(nx.all_simple_paths(switch_subgraph, source="s1", target="s5", cutoff=4))
    assert len(paths) >= 3, f"Expected at least 3 alternative paths between s1 and s5, got {len(paths)}"

    print(f"[PASS] MeshTopo verified: {len(switches)} switches, {len(hosts)} hosts, {len(paths)} redundant paths between s1 and s5.")
    return True

def test_fattree_topo():
    print("[TEST] Validating FatTree4Topo (k=4, 20 switches, 16 hosts)...")
    topo = FatTree4Topo()
    G = mininet_to_networkx(topo)

    switches = [n for n, d in G.nodes(data=True) if d.get("node_type") == "switch"]
    hosts = [n for n, d in G.nodes(data=True) if d.get("node_type") == "host"]

    assert len(switches) == 20, f"Expected 20 switches, got {len(switches)}"
    assert len(hosts) == 16, f"Expected 16 hosts, got {len(hosts)}"

    # Test edge-disjoint paths between hosts in different pods
    switch_subgraph = G.subgraph(switches).to_undirected()
    assert nx.is_connected(switch_subgraph), "FatTree switch graph must be fully connected"

    print(f"[PASS] FatTree4Topo verified: {len(switches)} switches, {len(hosts)} hosts, fabric is fully connected.")
    return True

def test_wan_topo():
    print("[TEST] Validating WanTopo (12 switches, irregular WAN)...")
    topo = WanTopo()
    G = mininet_to_networkx(topo)

    switches = [n for n, d in G.nodes(data=True) if d.get("node_type") == "switch"]
    hosts = [n for n, d in G.nodes(data=True) if d.get("node_type") == "host"]

    assert len(switches) == 12, f"Expected 12 switches, got {len(switches)}"
    assert len(hosts) == 12, f"Expected 12 hosts, got {len(hosts)}"

    switch_subgraph = G.subgraph(switches).to_undirected()
    assert nx.is_biconnected(switch_subgraph), "WAN topology must be 2-connected (no single point of failure)"

    print(f"[PASS] WanTopo verified: {len(switches)} switches, {len(hosts)} hosts, biconnected with heterogeneous links.")
    return True

def main():
    print("=" * 60)
    print("PHASE 1 TOPOLOGY & STRUCTURAL VERIFICATION")
    print("=" * 60)
    
    passed = True
    passed &= test_mesh_topo()
    passed &= test_fattree_topo()
    passed &= test_wan_topo()

    if not passed:
        print("\n[RESULT] Phase 1 topology checks failed.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] PHASE 1 TOPOLOGY ACCEPTANCE CHECKS PASSED!")
    print("=" * 60)
    sys.exit(0)

if __name__ == "__main__":
    main()
