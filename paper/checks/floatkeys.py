"""8-decimal floating-point spectral hashes for the 13 exactly-classified matrices,
computed with SMOL's own builders and hashing (db/matrices.py, db/spectrum.py), as in its
original float pipeline (db/graph_data.py). Used to check the paper's float-versus-exact
comparison (Technical Validation).

Usage: WID=0 NW=4 uv run --project ~/research/smol --with duckdb --with pyarrow python floatkeys.py N [N ...]
"""
import sys

import networkx as nx

sys.path.insert(0, "/Users/leo.torres/research/smol")
from db import matrices as Mx  # noqa: E402
from db.spectrum import (compute_complex_eigenvalues, compute_real_eigenvalues,  # noqa: E402
                         spectral_hash_complex, spectral_hash_real)

REAL = {"adj": Mx.adjacency_matrix, "kirchhoff": Mx.kirchhoff_laplacian,
        "signless": Mx.signless_laplacian, "lap": Mx.laplacian_matrix,
        "dist": Mx.distance_matrix, "distlap": Mx.distance_laplacian,
        "distsign": Mx.distance_signless_laplacian, "distnorm": Mx.normalized_distance_laplacian,
        "ecc": Mx.eccentricity_matrix, "yoon2": Mx.yoon2_matrix, "yoon3": Mx.yoon3_matrix}
COMPLEX = {"nb": Mx.nonbacktracking_matrix, "nbl": Mx.nonbacktracking_laplacian}


def hashes(g6s, n):
    out = {k: [] for k in (*REAL, *COMPLEX)}
    for s in g6s:
        G = nx.from_graph6_bytes(s.encode())
        for k, b in REAL.items():
            M = b(G)
            out[k].append(None if M is None else spectral_hash_real(compute_real_eigenvalues(M)))
        for k, b in COMPLEX.items():
            out[k].append(spectral_hash_complex(compute_complex_eigenvalues(b(G))))
    return out


if __name__ == "__main__":
    from chunks import run
    run("float", [int(x) for x in sys.argv[1:]], 5_000, hashes)
