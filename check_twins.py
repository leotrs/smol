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

def check_twin_condition(G, switch):
    """Check if ext(v1) = ext(v2) and ext(w1) = ext(w2)"""
    v1, w1, v2, w2 = switch
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(G.neighbors(v1)) - S
    ext_v2 = set(G.neighbors(v2)) - S
    ext_w1 = set(G.neighbors(w1)) - S
    ext_w2 = set(G.neighbors(w2)) - S
    
    return ext_v1 == ext_v2, ext_w1 == ext_w2

pairs = load_pairs('docs/78_pairs.txt')
print(f"Loaded {len(pairs)} pairs")

switches = []
not_switches = []

for g1_str, g2_str in pairs:
    G1 = to_graph(g1_str)
    G2 = to_graph(g2_str)
    switch, only1, only2 = find_switch(G1, G2)
    
    if switch is None:
        not_switches.append((g1_str, g2_str, len(only1)))
    else:
        v_twins, w_twins = check_twin_condition(G1, switch)
        switches.append((g1_str, g2_str, switch, v_twins, w_twins))

print(f"\n2-edge switches: {len(switches)}")
print(f"Not 2-edge switches: {len(not_switches)}")

# Edge difference distribution
edge_diffs = {}
for g1, g2, diff in not_switches:
    edge_diffs[diff] = edge_diffs.get(diff, 0) + 1
print(f"\nEdge difference distribution for non-switches: {dict(sorted(edge_diffs.items()))}")

# Twin condition results for switches
print("\n2-edge switches and twin condition:")
both_twins = 0
v_only = 0
w_only = 0
neither = 0
for g1, g2, switch, v_twins, w_twins in switches:
    status = f"v_twins={v_twins}, w_twins={w_twins}"
    print(f"  {g1},{g2}: {status}")
    if v_twins and w_twins:
        both_twins += 1
    elif v_twins:
        v_only += 1
    elif w_twins:
        w_only += 1
    else:
        neither += 1

print(f"\nSummary: both={both_twins}, v_only={v_only}, w_only={w_only}, neither={neither}")
