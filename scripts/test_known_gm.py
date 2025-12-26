#!/usr/bin/env python3
"""Test expanded detector on known GM pairs."""

import networkx as nx
from gm_switching_proper import is_gm_switching_pair as gm_original
from gm_switching_expanded import is_gm_switching_pair as gm_expanded

# Known GM pairs from docs/adj_n8_gm_correct.txt
known_gm_pairs = [
    ("GCQvBk", "GCQvD["),
    ("G?qbF?", "GCOfF?"),
    ("GCpvfW", "GCZbno"),
    ("GCrRV_", "GCrJf_"),
    ("GCpvv{", "GCfvV{"),
]

print("Testing known GM pairs:")
print("=" * 70)

for g6_1, g6_2 in known_gm_pairs:
    G = nx.from_graph6_bytes(g6_1.encode())
    H = nx.from_graph6_bytes(g6_2.encode())

    orig_result, orig_ss, orig_part = gm_original(G, H)
    exp_result, exp_ss, exp_part = gm_expanded(G, H)

    print(f"\nPair: {g6_1},{g6_2}")
    print(f"  Original: {orig_result}")
    if orig_result:
        print(f"    Switch set: {orig_ss}, Partition: {orig_part}")
    print(f"  Expanded: {exp_result}")
    if exp_result:
        print(f"    Switch set: {exp_ss}, Partition: {exp_part}")

    if orig_result != exp_result:
        print("  *** MISMATCH ***")
