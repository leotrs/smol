import networkx as nx
import numpy as np

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def nb_matrix(G):
    edges = [(u,v) for u,v in G.edges()] + [(v,u) for u,v in G.edges()]
    if len(edges) == 0:
        return np.array([]), {}
    idx = {e:i for i,e in enumerate(edges)}
    n = len(edges)
    B = np.zeros((n, n))
    for (u,v), i in idx.items():
        for x in G.neighbors(v):
            if x != u:
                B[i, idx[(v,x)]] = 1
    return B, idx

def nb_cospectral(G1, G2, tol=1e-6):
    B1, _ = nb_matrix(G1)
    B2, _ = nb_matrix(G2)
    if B1.size == 0 or B2.size == 0:
        return B1.size == B2.size
    e1 = sorted(np.linalg.eigvals(B1), key=lambda x: (round(x.real, 6), round(x.imag, 6)))
    e2 = sorted(np.linalg.eigvals(B2), key=lambda x: (round(x.real, 6), round(x.imag, 6)))
    for a, b in zip(e1, e2):
        if not (np.isclose(a.real, b.real, atol=tol) and np.isclose(a.imag, b.imag, atol=tol)):
            return False
    return True

# Load pairs
pairs = []
with open('nb_cospectral_pairs.txt') as f:
    for line in f:
        g1, g2 = line.strip().split(',')
        pairs.append((g1, g2))

# Find first edge slide pair
for g1_str, g2_str in pairs:
    G1, G2 = to_graph(g1_str), to_graph(g2_str)
    
    u1 = set(frozenset(e) for e in G1.edges())
    u2 = set(frozenset(e) for e in G2.edges())
    u_rem = u1 - u2
    u_add = u2 - u1
    
    if len(u_rem) == 1:
        e_rem = list(u_rem)[0]
        e_add = list(u_add)[0]
        common = e_rem & e_add
        w = list(common)[0]
        u_actual = list(e_rem - {w})[0]
        v_actual = list(e_add - {w})[0]
        break

print(f'Actual cospectral slide: {u_actual}-{w} -> {v_actual}-{w}')
print()

# Compare the actual slide with other non-cospectral ones
print('Comparing neighborhood structure:')
print('='*70)

def neighborhood_signature(G, vertex):
    """Get detailed neighborhood info"""
    N = list(G.neighbors(vertex))
    degs = sorted([G.degree(x) for x in N])
    return degs

def two_hop_info(G, vertex):
    """Two-hop neighborhood info"""
    N1 = set(G.neighbors(vertex))
    N2 = set()
    for x in N1:
        N2 |= set(G.neighbors(x))
    N2 -= {vertex}
    N2 -= N1
    return len(N2), sorted([G.degree(x) for x in N2])

print(f'Actual slide: u={u_actual}, v={v_actual}, w={w}')
print(f'  N(u) deg seq: {neighborhood_signature(G1, u_actual)}')
print(f'  N(v) deg seq: {neighborhood_signature(G1, v_actual)}')
print(f'  N(w) deg seq: {neighborhood_signature(G1, w)}')
print(f'  2-hop from u: {two_hop_info(G1, u_actual)}')
print(f'  2-hop from v: {two_hop_info(G1, v_actual)}')
print()

# Compare with some non-cospectral slides
non_cosp_examples = [
    (3, 1, 9),  # 3-9 -> 1-9
    (5, 3, 7),  # 5-7 -> 3-7
    (0, 3, 4),  # 0-4 -> 3-4
]

for u, v, w_test in non_cosp_examples:
    if not G1.has_edge(u, w_test):
        continue
    if G1.has_edge(v, w_test):
        continue
        
    print(f'Non-cosp slide: u={u}, v={v}, w={w_test}')
    print(f'  N(u) deg seq: {neighborhood_signature(G1, u)}')
    print(f'  N(v) deg seq: {neighborhood_signature(G1, v)}')
    print(f'  N(w) deg seq: {neighborhood_signature(G1, w_test)}')
    print(f'  2-hop from u: {two_hop_info(G1, u)}')
    print(f'  2-hop from v: {two_hop_info(G1, v)}')
    print()
