"""Check, independently of the job code, whether two graphs are non-3-cycling cospectral.

The matrix is built from Definition 5.2 of Arrigo, Higham, Noferini (2020): rows and columns
are the open paths (i1, i2, i3) of the graph, and P[i, j] = 1 when j = (i2, i3, j3) with
j3 != i1 (an open path from i1 to j3). It is compared with SMOL's builder
(db.matrices.non3cyc_matrix) up to a permutation, through exact integer characteristic
polynomials (sympy) and exact traces of powers. The published hashes are read from the
Zenodo graphs CSV.

Run: uv run --project ~/research/smol --with sympy python verify_pairs.py EEhW EEio ECvo EEro
"""
import gzip
import subprocess
import sys

import networkx as nx
import numpy as np
import sympy

sys.path.insert(0, "/Users/leo.torres/research/smol")
from db.matrices import non3cyc_matrix  # noqa: E402


def paper_P3(G):
    paths = [(a, b, c) for a in G for b in G[a] for c in G[b] if c != a]
    idx = {p: i for i, p in enumerate(paths)}
    P = np.zeros((len(paths), len(paths)), dtype=np.int64)
    for (a, b, c), i in idx.items():
        for d in G[c]:
            if d not in (a, b, c):
                P[i, idx[(b, c, d)]] = 1
    return P


x = sympy.symbols("x")
graphs = sys.argv[1:]
published = {}
zen = "/Users/leo.torres/research/smol_zenodo/graphs.csv.gz.part_aa"
cmd = f"cat {zen.replace('_aa', '_*')} | gunzip | grep -E '^({'|'.join(graphs)}),'"
for line in subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.splitlines():
    f = line.split(",")
    published[f[0]] = f[17]  # non3cyc_spectral_hash column
for g in graphs:
    G = nx.from_graph6_bytes(g.encode())
    P, S = paper_P3(G), non3cyc_matrix(G).astype(np.int64)
    cp = sympy.Matrix(P).charpoly(x).as_expr()
    same_as_smol = sympy.expand(cp - sympy.Matrix(S).charpoly(x).as_expr()) == 0
    traces = []
    M = np.eye(len(P), dtype=object)
    Po = P.astype(object)
    for _ in range(len(P)):
        M = M.dot(Po)
        traces.append(int(np.trace(M)))
    print(f"{g}: dimension {len(P)}; charpoly {sympy.factor(cp)}; equals SMOL's matrix charpoly: {same_as_smol}")
    print(f"   traces tr(P^1..P^{len(P)}): {traces}")
    print(f"   published Zenodo non3cyc hash: {published.get(g)}")
for a in range(0, len(graphs), 2):
    print(graphs[a], graphs[a + 1], "isomorphic:", nx.is_isomorphic(nx.from_graph6_bytes(graphs[a].encode()), nx.from_graph6_bytes(graphs[a + 1].encode())))
