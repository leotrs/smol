"""
NB Cospectral Count Investigation

Compares our non-backtracking (Hashimoto) matrix cospectral counts against
Table 1 from the paper "Characterizing cospectral vertices via isospectral
reduction" (Torres et al.).

STATUS: UNRESOLVED DISCREPANCY
Our counts are consistently ~3% lower than the paper's for all n values.

Results with this script (2m×2m Hashimoto, group by n,m, precision=6):
    n=5:    8 vs   11 expected (diff -3)
    n=6:   49 vs   57 expected (diff -8)
    n=7:  341 vs  363 expected (diff -22)
    n=8: 3674 vs 3760 expected (diff -86)
    Total difference: 119

Note: adj, lap, and nbl matrices all match the paper's counts exactly.
Only nb has this discrepancy.

APPROACHES TRIED (all gave same or worse results):
- 2m×2m Hashimoto matrix (this script) - best results
- 2n×2n pseudo-Hashimoto (Ihara-Bass) matrix
- Line graph adjacency matrix
- Precision from 1 to 8 decimals
- Rounding vs truncation
- Grouping by (n) only vs (n,m)
- Filtering eigenvalues by |λ|=1 or |λ|>1
- Tolerance-based comparison instead of hashing
- 2-core reduction before computing spectrum

The paper's exact counting methodology is not documented in their repository.
Our Hashimoto matrix computation matches their `fast_hashimoto` function.

Run: uv run python scripts/nb_conjugate_test.py
"""
import numpy as np
import networkx as nx
import psycopg2
from collections import defaultdict
import hashlib

def hashimoto_2m(G):
    """2m×2m Hashimoto matrix."""
    if G.number_of_edges() == 0:
        return np.array([]).reshape(0, 0)
    directed_edges = []
    for u, v in G.edges():
        directed_edges.append((u, v))
        directed_edges.append((v, u))
    directed_edges.sort()
    edge_to_idx = {e: i for i, e in enumerate(directed_edges)}
    num_edges = len(directed_edges)
    B = np.zeros((num_edges, num_edges), dtype=np.float64)
    for e_idx, (u, v) in enumerate(directed_edges):
        for neighbor in G.neighbors(v):
            if neighbor != u:
                f_idx = edge_to_idx[(v, neighbor)]
                B[e_idx, f_idx] = 1.0
    return B

def process_eigenvalues(eigs, precision=6):
    """Round and keep only non-negative imaginary part."""
    if len(eigs) == 0:
        return np.array([])

    # Round first
    re = np.round(eigs.real, decimals=precision)
    im = np.round(eigs.imag, decimals=precision)

    # Clean up -0.0
    re = np.where(re == 0, 0.0, re)
    im = np.where(im == 0, 0.0, im)

    # Keep only im >= 0
    mask = im >= 0
    return re[mask] + 1j * im[mask]

def hash_eigs(eigs, precision=6):
    """Hash eigenvalues sorted by (real, imag)."""
    if len(eigs) == 0:
        return "empty"

    # Sort by real part, then imaginary part
    sort_idx = np.lexsort((eigs.imag, eigs.real))
    eigs = eigs[sort_idx]

    canonical = ",".join(f"({e.real:.{precision}f},{e.imag:.{precision}f})" for e in eigs)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]

conn = psycopg2.connect(dbname="smol")
cur = conn.cursor()
cur.execute("SELECT n, m, graph6 FROM graphs WHERE n <= 8 AND diameter IS NOT NULL")
rows = cur.fetchall()
conn.close()
print(f"Loaded {len(rows)} connected graphs")

expected = {5: 11, 6: 57, 7: 363, 8: 3760}

# Precompute eigenvalues
print("Computing eigenvalues...")
graph_data = []
for i, (n, m, g6) in enumerate(rows):
    G = nx.from_graph6_bytes(g6.encode())
    B = hashimoto_2m(G)
    raw_eigs = np.linalg.eigvals(B) if B.size > 0 else np.array([])
    graph_data.append((n, m, g6, raw_eigs))
    if (i + 1) % 2000 == 0:
        print(f"  {i+1}/{len(rows)}")

# Test grouping by (n, m) vs (n) only
print("\nTesting group by (n,m):")
for prec in [6]:
    groups = defaultdict(list)
    for n, m, g6, raw_eigs in graph_data:
        eigs = process_eigenvalues(raw_eigs, precision=prec)
        h = hash_eigs(eigs, precision=prec)
        groups[(n, m, h)].append(g6)

    counts = defaultdict(int)
    for key, graphs in groups.items():
        if len(graphs) > 1:
            counts[key[0]] += len(graphs)

    total_diff = sum(abs(counts[n] - expected[n]) for n in [5,6,7,8])
    print(f"prec={prec}: total_diff={total_diff}")
    for n in [5, 6, 7, 8]:
        diff = counts[n] - expected[n]
        print(f"  n={n}: {counts[n]:>4} vs {expected[n]:>4} (diff {diff:+d})")

print("\nTesting group by (n) only:")
for prec in [6]:
    groups = defaultdict(list)
    for n, m, g6, raw_eigs in graph_data:
        eigs = process_eigenvalues(raw_eigs, precision=prec)
        h = hash_eigs(eigs, precision=prec)
        groups[(n, h)].append(g6)

    counts = defaultdict(int)
    for key, graphs in groups.items():
        if len(graphs) > 1:
            counts[key[0]] += len(graphs)

    total_diff = sum(abs(counts[n] - expected[n]) for n in [5,6,7,8])
    print(f"prec={prec}: total_diff={total_diff}")
    for n in [5, 6, 7, 8]:
        diff = counts[n] - expected[n]
        print(f"  n={n}: {counts[n]:>4} vs {expected[n]:>4} (diff {diff:+d})")
