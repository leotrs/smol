import networkx as nx

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def undirected_edges(G):
    return set(frozenset(e) for e in G.edges())

# Load all pairs
pairs = []
with open('nb_cospectral_pairs.txt') as f:
    for line in f:
        g1, g2 = line.strip().split(',')
        pairs.append((g1, g2))

# Extract all edge slides
slides = []
for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    
    u1 = undirected_edges(G1)
    u2 = undirected_edges(G2)
    u_rem = u1 - u2
    u_add = u2 - u1
    
    if len(u_rem) != 1:
        continue
    
    e_rem = list(u_rem)[0]
    e_add = list(u_add)[0]
    
    common = e_rem & e_add
    if len(common) != 1:
        continue
    
    w = list(common)[0]
    u = list(e_rem - {w})[0]
    v = list(e_add - {w})[0]
    
    slides.append({
        'g1': g1, 'g2': g2,
        'G1': G1, 'G2': G2,
        'u': u, 'v': v, 'w': w
    })

print(f"Found {len(slides)} edge slides")
print("="*70)
print()

# Analyze each slide in detail
for i, s in enumerate(slides[:5]):
    G1, u, v, w = s['G1'], s['u'], s['v'], s['w']
    
    print(f"Slide {i+1}: {s['g1']}")
    print(f"  Remove {u}-{w}, Add {v}-{w}")
    print()
    
    # Basic degrees
    print(f"  Degrees: u={G1.degree(u)}, v={G1.degree(v)}, w={G1.degree(w)}")
    print()
    
    # Full neighborhoods
    N_u = set(G1.neighbors(u))
    N_v = set(G1.neighbors(v))
    N_w = set(G1.neighbors(w))
    
    print(f"  N(u) = {sorted(N_u)}")
    print(f"  N(v) = {sorted(N_v)}")
    print(f"  N(w) = {sorted(N_w)}")
    print()
    
    # Key relationships
    print(f"  u in N(v)? {u in N_v}")
    print(f"  v in N(u)? {v in N_u}")
    print(f"  v in N(w)? {v in N_w}")  # Should be False (we're adding v-w)
    print()
    
    # Triangles
    triangles_u = sum(1 for x in N_u for y in N_u if x < y and G1.has_edge(x, y))
    triangles_v = sum(1 for x in N_v for y in N_v if x < y and G1.has_edge(x, y))
    print(f"  Triangles through u: {triangles_u}")
    print(f"  Triangles through v: {triangles_v}")
    print()
    
    # Common neighbors
    cn_uv = N_u & N_v
    cn_uw = N_u & N_w
    cn_vw = N_v & N_w
    print(f"  CN(u,v) = {sorted(cn_uv)}")
    print(f"  CN(u,w) = {sorted(cn_uw)}")
    print(f"  CN(v,w) = {sorted(cn_vw)}")
    print()
    
    print("-"*70)
