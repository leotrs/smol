"""
Test if (C3-path) is equivalent to cycle preservation.
C3-path: path counts from w1->v1 (avoiding v1-w1) = path counts from w2->v2 (avoiding v2-w2)
"""

import networkx as nx
from itertools import combinations
import subprocess

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def count_paths_avoiding_edge(G, start, end, avoid_u, avoid_v, max_len=8):
    """Count paths from start to end of each length, avoiding edge (avoid_u, avoid_v)."""
    counts = {}
    for k in range(1, max_len + 1):
        count = 0
        # Use DFS to find all paths of exactly length k
        stack = [(start, [start])]
        while stack:
            node, path = stack.pop()
            if len(path) - 1 == k:
                if node == end:
                    count += 1
                continue
            if len(path) - 1 >= k:
                continue
            for nbr in G.neighbors(node):
                if nbr in path:
                    continue
                # Check if this edge is the avoided one
                if (node == avoid_u and nbr == avoid_v) or (node == avoid_v and nbr == avoid_u):
                    continue
                stack.append((nbr, path + [nbr]))
        counts[k] = count
    return counts

def check_c3_path(G, v1, w1, v2, w2, max_len=8):
    """Check if path counts match."""
    paths1 = count_paths_avoiding_edge(G, w1, v1, v1, w1, max_len)
    paths2 = count_paths_avoiding_edge(G, w2, v2, v2, w2, max_len)
    return paths1 == paths2, paths1, paths2

def count_cycles(H, max_k=8):
    counts = {}
    for k in range(3, max_k + 1):
        count = 0
        for start in H.nodes():
            stack = [(start, [start])]
            while stack:
                node, path = stack.pop()
                if len(path) == k:
                    if H.has_edge(node, start):
                        count += 1
                    continue
                for nbr in H.neighbors(node):
                    if nbr not in path:
                        stack.append((nbr, path + [nbr]))
        counts[k] = count // (2 * k)
    return counts

def generate_graphs(n):
    result = subprocess.run(['geng', '-c', str(n)], capture_output=True, text=True)
    return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

# Test: does C3-path <=> cycle preservation?
print("Testing if C3-path <=> cycle preservation\n")

c3_implies_cycles = True
cycles_implies_c3 = True

for n in range(4, 8):
    graphs = generate_graphs(n)
    
    for g6 in graphs:
        G = to_graph(g6)
        if min(dict(G.degree()).values()) < 2:
            continue
        
        cycles_G = count_cycles(G)
        
        for e1, e2 in combinations(G.edges(), 2):
            for v1, w1 in [e1, e1[::-1]]:
                for v2, w2 in [e2, e2[::-1]]:
                    if G.has_edge(v1, w2) or G.has_edge(v2, w1):
                        continue
                    S = {v1, v2, w1, w2}
                    if len(S) != 4:
                        continue
                    if G.degree(v1) != G.degree(v2):
                        continue
                    if G.degree(w1) != G.degree(w2):
                        continue
                    ext = {x: set(G.neighbors(x)) - S for x in S}
                    if len(ext[v1] & ext[w1]) != len(ext[v2] & ext[w1]):
                        continue
                    if len(ext[v1] & ext[w2]) != len(ext[v2] & ext[w2]):
                        continue
                    
                    # Check C3-path
                    c3_ok, p1, p2 = check_c3_path(G, v1, w1, v2, w2)
                    
                    # Check cycle preservation
                    Gp = G.copy()
                    Gp.remove_edge(v1, w1)
                    Gp.remove_edge(v2, w2)
                    Gp.add_edge(v1, w2)
                    Gp.add_edge(v2, w1)
                    cycles_Gp = count_cycles(Gp)
                    cycles_ok = (cycles_G == cycles_Gp)
                    
                    if c3_ok and not cycles_ok:
                        c3_implies_cycles = False
                        print(f"C3-path but NOT cycle-preserving: {g6} {(v1,w1,v2,w2)}")
                        print(f"  paths: {p1} vs {p2}")
                    if cycles_ok and not c3_ok:
                        cycles_implies_c3 = False
                        print(f"Cycle-preserving but NOT C3-path: {g6} {(v1,w1,v2,w2)}")
                        print(f"  paths: {p1} vs {p2}")

print(f"\nC3-path => cycle preservation: {c3_implies_cycles}")
print(f"Cycle preservation => C3-path: {cycles_implies_c3}")
