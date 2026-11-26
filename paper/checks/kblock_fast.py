"""Exact k-blocking family hash with fixed evaluation points (no random numbers).

For each k = 2, 3, ... until the cycle core H_k is empty, the member is
(m_k, |states(M_k)|, det(X1 I - D_k B_k) mod P1, det(X2 I - D_k B_k) mod P2), where B_k is
the Hashimoto matrix of H_k and D_k scales the row of u->v by z(v) = C(d_G(v) - 2, k - 2).
The determinant uses the n x n reduction for T = Z B (see charkeys.py):
    det(xI - T) = prod_{uv in E(H_k)} (x^2 - z_u z_v) * det(I - diag(z) Atil(x)).
Hash = first 16 hex digits of sha256('kblock_family-exact|' + members joined by '|').
"""
import hashlib
from math import comb

import numba as nb
import numpy as np

from noncyc_fast import P1, P2, det_mod, powmod

X1, X2 = 1_000_003, 999_983


@nb.njit(cache=True)
def zb_charval(A, z, x, p):
    n = A.shape[0]
    M = np.zeros((n, n), dtype=np.int64)
    prod = 1
    for u in range(n):
        M[u, u] = 1
    for u in range(n):
        diag = 0
        for v in range(n):
            if A[u, v]:
                delta = (x * x - z[u] * z[v]) % p
                dinv = powmod(delta, p - 2, p)
                if u < v:
                    prod = prod * delta % p
                M[u, v] = (M[u, v] - z[u] * (x * dinv % p)) % p
                diag = (diag + z[v] * dinv) % p
        M[u, u] = (M[u, u] + z[u] * diag) % p
    return prod * det_mod(M, p) % p


def two_core(A, keep):
    keep = keep.copy()
    while True:
        Ak = A * np.outer(keep, keep)
        drop = keep & (Ak.sum(axis=1) < 2)
        if not drop.any():
            return keep
        keep &= ~drop


def kblock_hash(A):
    d = A.sum(axis=1)
    parts = []
    k = 2
    while True:
        core = two_core(A, d >= k)
        Ak = A * np.outer(core, core)
        mk = int(Ak.sum()) // 2
        if mk == 0:
            break
        z = np.array([comb(int(dv) - 2, k - 2) if c else 0 for dv, c in zip(d, core)], dtype=np.int64)
        size = int(sum(comb(int(d[v]) - 1, k - 2) for u in range(len(A)) for v in range(len(A)) if Ak[u, v]))
        parts.append(f"k{k}:{mk}:{size}:{zb_charval(Ak, z, X1, P1)}:{zb_charval(Ak, z, X2, P2)}")
        k += 1
    if not parts:
        return None
    return hashlib.sha256(("kblock_family-exact|" + "|".join(parts)).encode()).hexdigest()[:16]
