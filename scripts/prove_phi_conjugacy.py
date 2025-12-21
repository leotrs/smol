#!/usr/bin/env python3
"""
Prove Φ-conjugacy from (C1) and (C2).

The S-internal transfer kernel Φ[τ, ρ] is the total weight of paths
that enter S at boundary type τ, traverse only S-internal edges, and
exit at boundary type ρ.

We need to show: Φ_G[τ, ρ] = Φ_{G'}[σ(τ), σ(ρ)]

where σ swaps w1 ↔ w2.
"""

import networkx as nx
import psycopg2
from itertools import permutations

def get_switches():
    conn = psycopg2.connect('dbname=smol')
    cur = conn.cursor()
    cur.execute('''
        SELECT g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
          AND g1.min_degree >= 2
          AND g2.min_degree >= 2
    ''')
    pairs = cur.fetchall()
    conn.close()
    
    switches = []
    for g6_1, g6_2 in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        E1 = set(frozenset(e) for e in G1.edges())
        E2 = set(frozenset(e) for e in G2.edges())
        only_in_G1 = E1 - E2
        only_in_G2 = E2 - E1
        
        if len(only_in_G1) != 2:
            continue
        
        verts = set()
        for e in only_in_G1 | only_in_G2:
            verts.update(e)
        
        if len(verts) != 4:
            continue
        
        for perm in permutations(verts):
            v1, v2, w1, w2 = perm
            e1 = frozenset([v1, w1])
            e2 = frozenset([v2, w2])
            new_e1 = frozenset([v1, w2])
            new_e2 = frozenset([v2, w1])
            
            if only_in_G1 == {e1, e2} and only_in_G2 == {new_e1, new_e2}:
                if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                    switches.append((g6_1, g6_2, G1, G2, v1, v2, w1, w2))
                    break
    
    return switches

print("=" * 80)
print("PROOF: Φ-CONJUGACY FROM (C1) AND (C2)")
print("=" * 80)
print()

print("""
SETUP:
------
S = {v1, v2, w1, w2}
G has edges: v1-w1, v2-w2 (plus possibly v1-v2, w1-w2)
G' has edges: v1-w2, v2-w1 (plus same v1-v2, w1-w2)

Define σ on vertices: σ(w1) = w2, σ(w2) = w1, σ(vi) = vi, σ(x) = x for x ∉ S

CLAIM: σ induces a bijection on S-internal directed edges such that
       if e is an S-internal edge in G, then σ(e) is an S-internal edge in G'.

PROOF OF CLAIM:
S-internal edges in G:
  - (v1, w1), (w1, v1): switch edges
  - (v2, w2), (w2, v2): switch edges
  - (v1, v2), (v2, v1): parallel edges (if v1-v2 ∈ E)
  - (w1, w2), (w2, w1): parallel edges (if w1-w2 ∈ E)

Apply σ:
  - σ(v1, w1) = (v1, w2): switch edge in G' ✓
  - σ(w1, v1) = (w2, v1): switch edge in G' ✓
  - σ(v2, w2) = (v2, w1): switch edge in G' ✓
  - σ(w2, v2) = (w1, v2): switch edge in G' ✓
  - σ(v1, v2) = (v1, v2): same parallel edge ✓
  - σ(w1, w2) = (w2, w1) = (w1, w2) as undirected: same parallel edge ✓

So σ maps S-internal edges of G bijectively to S-internal edges of G'. ∎

CLAIM: Transition weights are preserved under σ.

PROOF OF CLAIM:
For a transition (a,b) → (b,c), the weight is 1/(deg(b) - 1).

Case 1: b = v1 or b = v2
  σ doesn't change v1 or v2, and deg(v1) = deg(v2) by (C1).
  So weight at v1 in G = weight at v1 in G'.
  And weight at v2 in G = weight at v2 in G'.

Case 2: b = w1
  σ(w1) = w2, and deg(w1) = deg(w2) by (C1).
  So weight at w1 in G = 1/(deg(w1)-1) = 1/(deg(w2)-1) = weight at w2 in G'.

Case 3: b = w2
  Similar to Case 2.

In all cases, the weight of (a,b) → (b,c) in G equals the weight of
σ(a,b) → σ(b,c) in G'. ∎

CLAIM: Φ_G[τ, ρ] = Φ_{G'}[σ(τ), σ(ρ)]

PROOF:
Φ_G[τ, ρ] = sum over all S-internal paths P from entry type τ to exit type ρ
            of weight(P)

Define σ(P) by applying σ to each vertex in the path.

By the first claim, σ(P) is a valid S-internal path in G'.
By the second claim, weight(σ(P)) = weight(P).

The entry type of σ(P) is σ(τ) and the exit type is σ(ρ).

Since σ is a bijection on S-internal paths, we have:

Φ_G[τ, ρ] = Σ_{paths P: τ → ρ in G} weight(P)
          = Σ_{paths P: τ → ρ in G} weight(σ(P))
          = Σ_{paths Q: σ(τ) → σ(ρ) in G'} weight(Q)
          = Φ_{G'}[σ(τ), σ(ρ)]  ∎

SUBTLETY: What are the boundary types?
------------------------------------------
The boundary types are defined by EXTERNAL vertices entering/exiting S.
We partition external vertices into:
  - shared: adjacent to both w1 and w2
  - unique_1: adjacent to w1 only
  - unique_2: adjacent to w2 only
  - ext(v1), ext(v2): external neighbors of v1, v2

The boundary types are:
  - v1: entry/exit via (x, v1) or (v1, x) for x ∈ ext(v1)
  - v2: entry/exit via (x, v2) or (v2, x) for x ∈ ext(v2)
  - w1_s: entry/exit via (x, w1) or (w1, x) for x ∈ shared
  - w2_s: entry/exit via (x, w2) or (w2, x) for x ∈ shared
  - w1_u: entry/exit via (x, w1) or (w1, x) for x ∈ unique_1
  - w2_u: entry/exit via (x, w2) or (w2, x) for x ∈ unique_2

The σ permutation on types is:
  σ(v1) = v1, σ(v2) = v2
  σ(w1_s) = w2_s, σ(w2_s) = w1_s  (shared vertices are adjacent to BOTH)
  σ(w1_u) = w2_u, σ(w2_u) = w1_u  (unique_1 stays "unique to one w", becomes unique_2)

KEY POINT about unique types:
  In G, a path entering at type w1_u comes from some x ∈ unique_1.
  Under σ, this maps to a path entering at w2 from the same x.
  But x ∈ unique_1 means x is NOT adjacent to w2 in G!
  
  HOWEVER, we're not saying σ maps individual paths in G to paths in G'.
  We're saying σ maps S-INTERNAL paths correctly.
  
  The entry edge (x, w1) for x ∈ unique_1 is a BOUNDARY edge, not internal.
  The internal part starts AFTER we've entered S.
  
  So for Φ, we only track:
  - Entry happens at type w1_u (meaning we entered S at vertex w1 from external)
  - Internal path within S
  - Exit happens at some type ρ

  The σ map on INTERNAL paths works because:
  - Inside S, paths only use S-vertices: v1, v2, w1, w2
  - σ maps internal edges of G to internal edges of G'
  - Entry type w1_u in G → Entry type w2_u in G' (same starting vertex after σ)

  This is correct because:
  - Entering at w1 in G corresponds to entering at σ(w1) = w2 in G'
  - The "unique" label swaps because unique_1 neighbors of w1 correspond to
    unique_2 neighbors of w2 (both are the "non-shared" neighbors)

THEREFORE: Φ_G = P_σ Φ_{G'} P_σ^T is proven from the definitions and (C1). ∎

NOTE: Condition (C2) is used for the Pairing Invariant, not directly for Φ-conjugacy.
""")

# Verify this understanding is correct
switches = get_switches()
idx = 0
g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]
S = {v1, v2, w1, w2}

print()
print("=" * 80)
print("VERIFICATION")
print("=" * 80)
print()

# Check that σ maps internal edges correctly
print(f"Switch {idx}: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
print()

def sigma(v, v1, v2, w1, w2):
    if v == w1: return w2
    if v == w2: return w1
    return v

def sigma_edge(e, v1, v2, w1, w2):
    u, v = e
    return (sigma(u, v1, v2, w1, w2), sigma(v, v1, v2, w1, w2))

# Internal edges in G1
int_edges_G1 = [(u, v) for u in S for v in S if G1.has_edge(u, v)]
int_edges_G1 = [(u, v) for u, v in G1.edges() if u in S and v in S]
int_edges_G1_directed = []
for u, v in int_edges_G1:
    int_edges_G1_directed.extend([(u, v), (v, u)])
int_edges_G1_directed = list(set(int_edges_G1_directed))

# Internal edges in G2
int_edges_G2 = [(u, v) for u, v in G2.edges() if u in S and v in S]
int_edges_G2_directed = []
for u, v in int_edges_G2:
    int_edges_G2_directed.extend([(u, v), (v, u)])
int_edges_G2_directed = list(set(int_edges_G2_directed))

print("Internal directed edges in G1:", sorted(int_edges_G1_directed))
print("Internal directed edges in G2:", sorted(int_edges_G2_directed))
print()

# Apply σ to G1 internal edges
sigma_G1_edges = [sigma_edge(e, v1, v2, w1, w2) for e in int_edges_G1_directed]
print("σ(G1 internal edges):", sorted(sigma_G1_edges))
print()

# Check if they match G2
match = set(sigma_G1_edges) == set(int_edges_G2_directed)
print(f"σ(G1 internal edges) = G2 internal edges: {match}")
