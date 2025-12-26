import networkx as nx

def load_pairs(path):
    pairs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if ',' in line:
                g1, g2 = line.split(',')
                pairs.append((g1, g2))
    return pairs

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def find_switch(G1, G2):
    """Find the 2-edge switch between G1 and G2, if one exists."""
    e1 = set(G1.edges())
    e2 = set(G2.edges())
    
    only1 = e1 - e2
    only2 = e2 - e1
    
    if len(only1) != 2 or len(only2) != 2:
        return None, only1, only2
    
    verts1 = set()
    for u, v in only1:
        verts1.add(u)
        verts1.add(v)
    
    verts2 = set()
    for u, v in only2:
        verts2.add(u)
        verts2.add(v)
    
    if verts1 != verts2 or len(verts1) != 4:
        return None, only1, only2
    
    edges1 = list(only1)
    e_a, e_b = edges1
    
    for v1 in [e_a[0], e_a[1]]:
        w1 = e_a[0] if e_a[1] == v1 else e_a[1]
        for v2 in [e_b[0], e_b[1]]:
            w2 = e_b[0] if e_b[1] == v2 else e_b[1]
            if {v1, v2, w1, w2} == verts1:
                if (v1, w2) in e2 or (w2, v1) in e2:
                    if (v2, w1) in e2 or (w1, v2) in e2:
                        return (v1, w1, v2, w2), only1, only2
    
    return None, only1, only2

def check_c1c2(G, switch):
    """Check (C1) and (C2) conditions."""
    v1, w1, v2, w2 = switch
    S = {v1, v2, w1, w2}
    
    # C1: degree equality
    c1_v = G.degree(v1) == G.degree(v2)
    c1_w = G.degree(w1) == G.degree(w2)
    
    # External neighborhoods
    ext_v1 = set(G.neighbors(v1)) - S
    ext_v2 = set(G.neighbors(v2)) - S
    ext_w1 = set(G.neighbors(w1)) - S
    ext_w2 = set(G.neighbors(w2)) - S
    
    # C2: pairwise intersection counts
    c2_w1 = len(ext_v1 & ext_w1) == len(ext_v2 & ext_w1)
    c2_w2 = len(ext_v1 & ext_w2) == len(ext_v2 & ext_w2)
    
    return {
        'c1_v': c1_v, 'c1_w': c1_w,
        'c2_w1': c2_w1, 'c2_w2': c2_w2,
        'c1': c1_v and c1_w,
        'c2': c2_w1 and c2_w2,
        'c1c2': c1_v and c1_w and c2_w1 and c2_w2,
        'deg_v1': G.degree(v1), 'deg_v2': G.degree(v2),
        'deg_w1': G.degree(w1), 'deg_w2': G.degree(w2),
        'ext_v1': ext_v1, 'ext_v2': ext_v2,
        'ext_w1': ext_w1, 'ext_w2': ext_w2,
    }

pairs = load_pairs('docs/78_pairs.txt')

print("Direct 2-edge switches - checking (C1)+(C2):\n")
for g1_str, g2_str in pairs:
    G1 = to_graph(g1_str)
    G2 = to_graph(g2_str)
    switch, only1, only2 = find_switch(G1, G2)
    
    if switch is not None:
        res = check_c1c2(G1, switch)
        v1, w1, v2, w2 = switch
        print(f"{g1_str},{g2_str}")
        print(f"  switch: v1={v1}, w1={w1}, v2={v2}, w2={w2}")
        print(f"  degrees: v1={res['deg_v1']}, v2={res['deg_v2']}, w1={res['deg_w1']}, w2={res['deg_w2']}")
        print(f"  C1 (deg match): {res['c1']} (v: {res['c1_v']}, w: {res['c1_w']})")
        print(f"  C2 (intersection match): {res['c2']} (w1: {res['c2_w1']}, w2: {res['c2_w2']})")
        print(f"  ext(v1)={res['ext_v1']}, ext(v2)={res['ext_v2']}")
        print(f"  ext(w1)={res['ext_w1']}, ext(w2)={res['ext_w2']}")
        print(f"  (C1)+(C2): {res['c1c2']}")
        print()
