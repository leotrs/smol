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

print(f"Analyzing {len(slides)} edge slides")
print("="*70)
print()

# Look for invariants
print("Looking for patterns that hold across ALL slides:")
print()

# Check various properties
all_pass = {
    'deg_u_eq_deg_v_plus_1': True,
    'u_v_not_adjacent': True,
    'same_cn_with_w': True,
    'same_triangles': True,
    'same_deg_seq_neighbors': True,
}

for s in slides:
    G1, u, v, w = s['G1'], s['u'], s['v'], s['w']
    
    # deg(u) = deg(v) + 1
    if G1.degree(u) != G1.degree(v) + 1:
        all_pass['deg_u_eq_deg_v_plus_1'] = False
    
    # u-v not adjacent
    if G1.has_edge(u, v):
        all_pass['u_v_not_adjacent'] = False
    
    # Same number of common neighbors with w
    N_u = set(G1.neighbors(u))
    N_v = set(G1.neighbors(v))
    N_w = set(G1.neighbors(w))
    
    cn_uw = len(N_u & N_w)
    cn_vw = len(N_v & N_w)
    if cn_uw != cn_vw:
        all_pass['same_cn_with_w'] = False
    
    # Same triangle count
    tri_u = sum(1 for x in N_u for y in N_u if x < y and G1.has_edge(x, y))
    tri_v = sum(1 for x in N_v for y in N_v if x < y and G1.has_edge(x, y))
    if tri_u != tri_v:
        all_pass['same_triangles'] = False
    
    # Same degree sequence of neighbors
    deg_seq_u = sorted([G1.degree(x) for x in N_u])
    deg_seq_v = sorted([G1.degree(x) for x in N_v])
    if deg_seq_u != deg_seq_v:
        all_pass['same_deg_seq_neighbors'] = False

for prop, passed in all_pass.items():
    status = "ALL PASS" if passed else "FAILS"
    print(f"  {prop}: {status}")

print()
print("="*70)
print()

# Let's count the patterns
print("Pattern frequencies:")

uv_adj_count = 0
same_cn_count = 0

for s in slides:
    G1, u, v, w = s['G1'], s['u'], s['v'], s['w']
    
    if G1.has_edge(u, v):
        uv_adj_count += 1
    
    N_u = set(G1.neighbors(u))
    N_v = set(G1.neighbors(v))
    N_w = set(G1.neighbors(w))
    
    if len(N_u & N_w) == len(N_v & N_w):
        same_cn_count += 1

print(f"  u-v adjacent: {uv_adj_count}/{len(slides)}")
print(f"  |CN(u,w)| = |CN(v,w)|: {same_cn_count}/{len(slides)}")
print()

# Now let's look at what differs between u-v adjacent and not
print("="*70)
print("Comparing u-v adjacent vs not:")
print()

adj_slides = [s for s in slides if s['G1'].has_edge(s['u'], s['v'])]
nonadj_slides = [s for s in slides if not s['G1'].has_edge(s['u'], s['v'])]

print(f"u-v adjacent: {len(adj_slides)}")
print(f"u-v not adjacent: {len(nonadj_slides)}")
print()

# For non-adjacent, check if |CN(u,w)| = |CN(v,w)|
print("For u-v NOT adjacent:")
for s in nonadj_slides[:5]:
    G1, u, v, w = s['G1'], s['u'], s['v'], s['w']
    N_u = set(G1.neighbors(u))
    N_v = set(G1.neighbors(v))
    N_w = set(G1.neighbors(w))
    cn_uw = N_u & N_w
    cn_vw = N_v & N_w
    print(f"  {s['g1']}: |CN(u,w)|={len(cn_uw)}, |CN(v,w)|={len(cn_vw)}, equal={len(cn_uw)==len(cn_vw)}")

print()
print("For u-v ADJACENT:")
for s in adj_slides[:5]:
    G1, u, v, w = s['G1'], s['u'], s['v'], s['w']
    N_u = set(G1.neighbors(u))
    N_v = set(G1.neighbors(v))
    N_w = set(G1.neighbors(w))
    cn_uw = N_u & N_w
    cn_vw = N_v & N_w
    print(f"  {s['g1']}: |CN(u,w)|={len(cn_uw)}, |CN(v,w)|={len(cn_vw)}, diff={len(cn_uw)-len(cn_vw)}")
