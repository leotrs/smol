"""Job 3: exact non-3-cycling and non-4-cycling keys for every graph (see noncyc.py and
noncyc_fast.py). For each k, the key is (N_k, det(X1 I - P_k) mod P1, det(X2 I - P_k) mod P2).
Equal characteristic polynomials always give equal keys. Different polynomials of degree N
give equal keys with probability at most (N/2^31)^2 per pair; every family found is rechecked
afterwards at further points. A graph whose matrix is nilpotent (characteristic polynomial
x^N, checked at both points) is flagged, matching SMOL's NULL convention.

Usage: WID=0 NW=2 uv run --no-project --with numba --with numpy --with duckdb --with pyarrow python noncyc_job.py N [N ...]
"""
import sys

import numpy as np

import noncyc_fast as nf

X1, X2 = 1_000_003, 999_983


def keys(g6s, n):
    out = {}
    for k in (3, 4):
        N = np.zeros(len(g6s), dtype=np.int64)
        v1 = np.zeros(len(g6s), dtype=np.int64)
        v2 = np.zeros(len(g6s), dtype=np.int64)
        nil = np.zeros(len(g6s), dtype=bool)
        for i, s in enumerate(g6s):
            A = nf.decode(s, n)
            v1[i], N[i] = nf.charval(A, n, k, X1, nf.P1)
            v2[i], _ = nf.charval(A, n, k, X2, nf.P2)
            nil[i] = v1[i] == nf.powmod(X1, N[i], nf.P1) and v2[i] == nf.powmod(X2, N[i], nf.P2)
        out.update({f"non{k}cyc_N": N, f"non{k}cyc_v1": v1, f"non{k}cyc_v2": v2, f"non{k}cyc_nilpotent": nil})
    return out


if __name__ == "__main__":
    from chunks import run
    run("noncyc", [int(x) for x in sys.argv[1:]], 20_000, keys)
