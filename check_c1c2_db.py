"""
Check if (C1)+(C2) switches always produce NBL-cospectral pairs.
Query DB for cospectral families, then check switches.
"""

import networkx as nx
import psycopg2
from itertools import combinations

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def to_graph6(G):
    return nx.to_graph6_bytes(G, header=False).decode().strip()

def find_c1c2_switches(G):
    """Find all (C1)+(C2) switches in G."""
    results = []
    
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
                
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                
                results.append((v1, w1, v2, w2, Gp))
    
    return results

conn = psycopg2.connect("dbname=smol")
cur = conn.cursor()

# Load all NBL spectral hashes
print("Loading NBL spectral hashes...")
cur.execute("SELECT graph6, nbl_spectral_hash FROM graphs WHERE min_degree >= 2")
nbl_hashes = {row[0]: row[1] for row in cur.fetchall()}
print(f"Loaded {len(nbl_hashes)} graphs")

# Find (C1)+(C2) switches and check via hash
print("\nChecking (C1)+(C2) switches...")

counterexamples = []
cospectral_count = 0
skipped = 0

for i, (g6, hash_G) in enumerate(nbl_hashes.items()):
    if i % 50000 == 0:
        print(f"  Processed {i}/{len(nbl_hashes)}...")
    
    G = to_graph(g6)
    switches = find_c1c2_switches(G)
    
    for v1, w1, v2, w2, Gp in switches:
        g6_p = to_graph6(Gp)
        hash_Gp = nbl_hashes.get(g6_p)
        
        if hash_Gp is None:
            skipped += 1
            continue
        
        if hash_G == hash_Gp:
            cospectral_count += 1
        else:
            counterexamples.append((g6, g6_p, (v1, w1, v2, w2)))

print("\nResults:")
print(f"  Cospectral: {cospectral_count}")
print(f"  NOT cospectral: {len(counterexamples)}")
print(f"  Skipped (G' not in DB): {skipped}")

if counterexamples:
    print("\nFirst 5 counterexamples:")
    for g6, g6_p, sw in counterexamples[:5]:
        print(f"  {g6} --{sw}--> {g6_p}")

conn.close()
