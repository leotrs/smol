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

# Load pairs and get the first graph
pairs = []
with open('nb_cospectral_pairs.txt') as f:
    for line in f:
        g1, g2 = line.strip().split(',')
        pairs.append((g1, g2))

# Find first edge slide pair
for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    
    u1 = set(frozenset(e) for e in G1.edges())
    u2 = set(frozenset(e) for e in G2.edges())
    u_rem = u1 - u2
    u_add = u2 - u1
    
    if len(u_rem) == 1:
        print(f'Graph: {g1}')
        print(f'n={G1.number_of_nodes()}, m={G1.number_of_edges()}')
        print()
        break

# Find all potential edge slides with deg(u) = deg(v) + 1
potential_slides = []
for u, w in G1.edges():
    for v in G1.nodes():
        if v == u or v == w:
            continue
        if G1.has_edge(v, w):
            continue
        if G1.degree(u) == G1.degree(v) + 1:
            # Create the slid graph
            G2_test = G1.copy()
            G2_test.remove_edge(u, w)
            G2_test.add_edge(v, w)
            
            is_cosp = nb_cospectral(G1, G2_test)
            potential_slides.append((u, v, w, is_cosp))

print(f'Potential slides with deg(u)=deg(v)+1: {len(potential_slides)}')
print()

cosp_count = sum(1 for s in potential_slides if s[3])
print(f'NB-cospectral: {cosp_count}')
print()

print('Details:')
for u, v, w, is_cosp in potential_slides:
    status = 'COSPECTRAL' if is_cosp else 'not cosp'
    
    # Check additional properties
    N_u = set(G1.neighbors(u))
    N_v = set(G1.neighbors(v))
    
    # Common neighbors of u and w
    cn_uw = N_u & set(G1.neighbors(w))
    # Common neighbors of v and w  
    cn_vw = N_v & set(G1.neighbors(w))
    
    # Is v adjacent to u?
    uv_adj = G1.has_edge(u, v)
    
    print(f'  {u}-{w} -> {v}-{w}: {status}')
    print(f'    u-v adj: {uv_adj}, |CN(u,w)|={len(cn_uw)}, |CN(v,w)|={len(cn_vw)}')
