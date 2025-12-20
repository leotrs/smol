"""Research script: Load 4 NBL-cospectral graphs and compute their matrices."""

import networkx as nx

import sys
sys.path.insert(0, "/Users/leo.torres/research/smol")

from db.matrices import nonbacktracking_laplacian

GRAPH6_STRINGS = [
    "I?qa`hidg",
    "I?qa`iYXg",
    "I?qa`ngk_",
    "I?qadhik_",
]


def main():
    graphs = [nx.from_graph6_bytes(g6.encode()) for g6 in GRAPH6_STRINGS]

    for i, (g6, G) in enumerate(zip(GRAPH6_STRINGS, graphs)):
        print(f"\n{'='*60}")
        print(f"Graph {i+1}: {g6}")
        print(f"  n = {G.number_of_nodes()}, m = {G.number_of_edges()}")
        print(f"  Degree sequence: {sorted([d for _, d in G.degree()], reverse=True)}")

        nonbacktracking_laplacian(G)



if __name__ == "__main__":
    main()
