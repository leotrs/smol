"""Check the reduced determinants against the full matrices, graph by graph.

For each graph, det(X3 I - M) mod P1 is computed twice at a point X3 that no hash uses:
from the full matrix M, built here directly from its definition, and from the reduction
used for the hashes (noncyc_fast.charval, kblock_fast.zb_charval). If the reduction were
wrong for a graph, the two values would differ except with probability at most dim/P1.

  kblock : M = D_k B_k on the cycle core H_k, for every k with H_k non-empty
  non3   : M = P_3 (Arrigo, Higham, Noferini 2020, Definition 5.2)
  non4   : M = P_4

Usage:
  WID=0 NW=4 uv run --no-project --with numba --with numpy --with duckdb --with pyarrow \
      python fullcheck.py kblock|non3 N [N ...]       every graph of order N
  WID=0 NW=4 ... python fullcheck.py non4sample          graphs listed in out/non4_sample.txt
"""
import os
import sys
import time
from math import comb

import numba as nb
import numpy as np

import kblock_fast as kf
import noncyc_fast as nf

X3 = 1_234_577
P = nf.P1


@nb.njit(cache=True)
def full_noncyc(A, n, k, x, p):
    """det(xI - P_k) mod p from the full matrix: rows and columns are the paths with k
    vertices, and P_k[i, j] = 1 when j = (i_2, ..., i_k, y) with y ~ i_k outside i."""
    paths = nf.enum_paths(A, n, k)
    N = paths.shape[0]
    if N == 0:
        return 1, 0
    table = -np.ones(n ** k, dtype=np.int64)
    for i in range(N):
        table[nf.code(paths[i], 0, k, n)] = i
    M = np.zeros((N, N), dtype=np.int64)
    nxt = np.empty(k, dtype=np.int64)
    for i in range(N):
        M[i, i] = x % p
        last = paths[i, k - 1]
        for y in range(n):
            if A[last, y] == 0:
                continue
            inside = False
            for t in range(k):
                if paths[i, t] == y:
                    inside = True
            if inside:
                continue
            for t in range(k - 1):
                nxt[t] = paths[i, t + 1]
            nxt[k - 1] = y
            j = table[nf.code(nxt, 0, k, n)]
            M[i, j] = (M[i, j] - 1) % p
    return nf.det_mod(M, p), N


@nb.njit(cache=True)
def full_zb(A, z, x, p):
    """det(xI - Z B) mod p from the full 2m x 2m matrix: B is the Hashimoto matrix of the
    graph A, and Z scales the row of u->v by z[v]."""
    n = A.shape[0]
    eid = -np.ones((n, n), dtype=np.int64)
    E = 0
    for u in range(n):
        for v in range(n):
            if A[u, v]:
                eid[u, v] = E
                E += 1
    if E == 0:
        return 1
    M = np.zeros((E, E), dtype=np.int64)
    for u in range(n):
        for v in range(n):
            if A[u, v] == 0:
                continue
            e = eid[u, v]
            M[e, e] = x % p
            for w in range(n):
                if A[v, w] and w != u:
                    M[e, eid[v, w]] = (M[e, eid[v, w]] - z[v]) % p
    return nf.det_mod(M, p)


def check_kblock(A):
    d = A.sum(axis=1)
    k, ok, dims = 2, True, 0
    while True:
        core = kf.two_core(A, d >= k)
        Ak = A * np.outer(core, core)
        if Ak.sum() == 0:
            break
        z = np.array([comb(int(dv) - 2, k - 2) if c else 0 for dv, c in zip(d, core)], dtype=np.int64)
        ok &= bool(full_zb(Ak, z, X3, P) == kf.zb_charval(Ak, z, X3, P))
        dims = max(dims, int(Ak.sum()))
        k += 1
    return ok, dims


def check_noncyc(A, n, k):
    full, N = full_noncyc(A, n, k, X3, P)
    red, N2 = nf.charval(A, n, k, X3, P)
    return bool(full == red and N == N2), N


def compute(kind, g6s, n):
    ok, dim = [], []
    for s in g6s:
        A = nf.decode(s, n)
        if kind == "kblock":
            a, b = check_kblock(A)
        else:
            a, b = check_noncyc(A, n, 3 if kind == "non3" else 4)
        ok.append(a)
        dim.append(b)
    return {"ok": np.array(ok), "dim": np.array(dim)}


if __name__ == "__main__":
    kind = sys.argv[1]
    if kind == "non4sample":
        import pyarrow as pa
        import pyarrow.parquet as pq
        rows = [l.split() for l in open(os.path.join(os.path.dirname(__file__), "out", "non4_sample.txt"))]
        wid, nw = int(os.environ.get("WID", 0)), int(os.environ.get("NW", 1))
        out = os.path.join(os.path.dirname(__file__), "out", "full_non4sample")
        os.makedirs(out, exist_ok=True)
        step = 500
        for c in range(0, len(rows), step):
            path = os.path.join(out, f"c{c // step:04d}.parquet")
            if (c // step) % nw != wid or os.path.exists(path):
                continue
            t0 = time.time()
            chunk = rows[c:c + step]
            res = {"ok": [], "dim": []}
            for g, n in chunk:
                a, b = check_noncyc(nf.decode(g, int(n)), int(n), 4)
                res["ok"].append(a)
                res["dim"].append(b)
            pq.write_table(pa.table({"graph6": [g for g, _ in chunk], **res}), path + ".tmp")
            os.rename(path + ".tmp", path)
            with open(os.path.join(os.path.dirname(__file__), "progress_full_non4sample.log"), "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} worker {wid} chunk {c // step + 1}/{-(-len(rows) // step)} graphs {len(chunk)} secs {time.time() - t0:.1f}\n")
    else:
        from chunks import run
        run(f"full_{kind}", [int(x) for x in sys.argv[2:]], 20_000, lambda g6s, n: compute(kind, g6s, n))
