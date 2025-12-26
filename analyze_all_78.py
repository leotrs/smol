"""
Analyze ALL 78 NBL-cospectral pairs.
For non-switch pairs: how do they differ structurally?
"""

import networkx as nx
from collections import Counter

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def edge_diff(G1, G2):
    """Return edges only in G1, only in G2."""
    e1 = set(frozenset(e) for e in G1.edges())
    e2 = set(frozenset(e) for e in G2.edges())
    return e1 - e2, e2 - e1

def graph_invariants(G):
    """Basic invariants."""
    return {
        'n': G.number_of_nodes(),
        'm': G.number_of_edges(),
        'deg_seq': tuple(sorted(dict(G.degree()).values())),
        'triangles': sum(nx.triangles(G).values()) // 3,
    }

# Load pairs
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

print(f"Analyzing {len(pairs)} NBL-cospectral pairs\n")

# Categorize by edge difference
diff_counts = Counter()
categories = {}

for g1, g2 in pairs:
    G1 = to_graph(g1)
    G2 = to_graph(g2)
    
    only1, only2 = edge_diff(G1, G2)
    diff = len(only1)  # = len(only2) since same edge count
    diff_counts[diff] += 1
    
    if diff not in categories:
        categories[diff] = []
    categories[diff].append((g1, g2, only1, only2))

print("Edge difference distribution:")
for d in sorted(diff_counts.keys()):
    print(f"  {d} edges differ: {diff_counts[d]} pairs")

print("\n" + "="*60)
print("Examples from each category:")
print("="*60)

for d in sorted(categories.keys()):
    print(f"\n--- {d} edges differ ---")
    for g1, g2, only1, only2 in categories[d][:2]:  # show 2 examples
        G1 = to_graph(g1)
        G2 = to_graph(g2)
        print(f"\n{g1} <-> {g2}")
        print(f"  Only in G1: {[tuple(e) for e in only1]}")
        print(f"  Only in G2: {[tuple(e) for e in only2]}")
        
        # Check if isomorphic
        if nx.is_isomorphic(G1, G2):
            print("  ISOMORPHIC!")
        else:
            print("  Not isomorphic")
