"""Exact characteristic-polynomial spectral hashes (cospectrality invariants).

The cospectral hash for every eigenvalue-based matrix is the SHA-256 (16 hex chars)
of its exact characteristic polynomial, rather than a hash of rounded floating-point
eigenvalues. This is bit-reproducible (no BLAS dependence) and exact (no rounding),
which matters most for the non-symmetric / complex-spectrum matrices whose float
eigenvalues are numerically unstable.

Per matrix the exact invariant is:
  - integer matrices (adj, kirchhoff, signless, dist, distlap, distsign, ecc):
    monic det(xI - M), integer Bareiss.
  - yoon2/yoon3: the matrix has graph-independent rational entries; clear the common
    denominator c(m) to an integer matrix (uniform scaling preserves cospectrality),
    then monic det(xI - cM).
  - normalized (lap, distnorm): eigenvalues are generalized eigenvalues of an integer
    pencil; hash the MONIC charpoly of det(xB - M). lap also multiplies in
    (x-1)^(#isolated vertices) for its isolated-vertex eigenvalue-1 convention.
  - nb: the Ihara-Bass charpoly (db.spectrum.nb_charpoly).

The hard tier (nbl, non3cyc, non4cyc) is not implemented here yet.
"""

from fractions import Fraction
from math import comb, gcd

import networkx as nx
import numpy as np

from .matrices import adjacency_matrix, open_path_matrix
from .matrix_types import MATRIX_TYPES
from .spectrum import bareiss_poly_det, charpoly_hash, nb_charpoly

# Matrices handled by this module (the "easy" tier).
INTEGER_MATRICES = ("adj", "kirchhoff", "signless", "dist", "distlap", "distsign", "ecc")
NORMALIZED_MATRICES = ("lap", "distnorm")
YOON_MATRICES = {"yoon2": 2, "yoon3": 3}
EASY_MATRICES = INTEGER_MATRICES + NORMALIZED_MATRICES + tuple(YOON_MATRICES) + ("nb",)


def _lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b if a and b else (a or b)


def _integer_charpoly_coeffs(M: np.ndarray) -> list[int]:
    """Coefficients of the monic det(xI - M) for an integer-valued matrix M."""
    n = M.shape[0]
    Mi = M if M.dtype == object else np.rint(M)
    M_polys = [
        [[-int(Mi[i][j]), (1 if i == j else 0)] for j in range(n)]
        for i in range(n)
    ]
    return bareiss_poly_det(M_polys, n)


def _monic_fraction_coeffs(int_coeffs: list[int]) -> list[Fraction]:
    """Divide an integer coefficient list by its leading coefficient -> monic rational."""
    coeffs = list(int_coeffs)
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    lead = coeffs[-1]
    return [Fraction(c, lead) for c in coeffs]


def _frac_poly_mul(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    return out


def _generalized_pencil_coeffs(M: np.ndarray, B_diag: np.ndarray) -> list[int]:
    """Integer coefficients of det(xB - M) where B = diag(B_diag), M, B integer.

    Roots are the generalized eigenvalues (M v = x B v), i.e. the eigenvalues of the
    normalized operator. Entry (i,j) = x*B_ii*[i==j] - M_ij.
    """
    n = M.shape[0]
    Mi = np.rint(M).astype(object)
    Bi = np.rint(B_diag).astype(object)
    M_polys = [
        [[-int(Mi[i][j]), (int(Bi[i]) if i == j else 0)] for j in range(n)]
        for i in range(n)
    ]
    return bareiss_poly_det(M_polys, n)


def _lap_charpoly_key(G: nx.Graph) -> str:
    """Normalized Laplacian: monic generalized charpoly of (L_comb, D), with isolated
    vertices contributing eigenvalue 1 (the matrix builder's convention)."""
    A = adjacency_matrix(G)
    n = A.shape[0]
    deg = np.rint(A.sum(axis=1)).astype(int)
    keep = [i for i in range(n) if deg[i] > 0]
    n_iso = n - len(keep)

    if keep:
        Asub = A[np.ix_(keep, keep)]
        dsub = deg[keep]
        L_comb = np.diag(dsub) - Asub  # combinatorial Laplacian of the non-isolated part
        coeffs = _monic_fraction_coeffs(_generalized_pencil_coeffs(L_comb, dsub))
    else:
        coeffs = [Fraction(1)]

    # Each isolated vertex contributes an eigenvalue 1 -> factor (x - 1).
    for _ in range(n_iso):
        coeffs = _frac_poly_mul(coeffs, [Fraction(-1), Fraction(1)])
    return charpoly_hash([str(c) for c in coeffs])


def _distnorm_charpoly_key(G: nx.Graph) -> str | None:
    """Normalized distance Laplacian: monic generalized charpoly of (Dist, T), where
    T = diag(transmissions). Connected graphs only (T positive definite)."""
    from .matrices import distance_matrix
    Dist = distance_matrix(G)
    if Dist is None or Dist.shape[0] < 2:
        return None
    t = np.rint(Dist.sum(axis=1)).astype(int)
    if np.any(t == 0):
        return None
    coeffs = _monic_fraction_coeffs(_generalized_pencil_coeffs(Dist, t))
    return charpoly_hash([str(c) for c in coeffs])


def _yoon_charpoly_key(G: nx.Graph, m: int) -> str | None:
    """Yoon m-Laplacian: clear the graph-independent rational denominator to an
    integer matrix, then monic det(xI - cM). Uniform scaling preserves cospectrality."""
    n = G.number_of_nodes()
    if n <= m:
        return None
    # Exact rational reweighted adjacency W = sum_k a_{k,m} P_{G,k}.
    W = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for k in range(1, m + 1):
        a = Fraction((-1) ** (k + 1) * 2 * comb(2 * m, m - k), k * k * comb(2 * m, m))
        Pk = np.rint(open_path_matrix(G, k)).astype(int)
        for i in range(n):
            for j in range(n):
                if Pk[i][j]:
                    W[i][j] += a * int(Pk[i][j])
    # m-Laplacian = diag(rowsum W) - W. Clear the common denominator.
    rowsum = [sum(W[i], Fraction(0)) for i in range(n)]
    denom = 1
    for i in range(n):
        denom = _lcm(denom, rowsum[i].denominator)
        for j in range(n):
            denom = _lcm(denom, W[i][j].denominator)
    M = np.zeros((n, n), dtype=object)
    for i in range(n):
        for j in range(n):
            val = (rowsum[i] if i == j else Fraction(0)) - W[i][j]
            M[i, j] = int(val * denom)
    return charpoly_hash(_integer_charpoly_coeffs(M))


def exact_spectral_hash(key: str, G: nx.Graph) -> str | None:
    """Exact charpoly cospectral hash for matrix `key` on graph G, or None if the
    matrix is undefined for G (e.g. distance matrices on disconnected graphs)."""
    if key == "nb":
        return charpoly_hash(nb_charpoly(adjacency_matrix(G)))
    if key == "lap":
        return _lap_charpoly_key(G)
    if key == "distnorm":
        return _distnorm_charpoly_key(G)
    if key in YOON_MATRICES:
        return _yoon_charpoly_key(G, YOON_MATRICES[key])
    if key in INTEGER_MATRICES:
        M = MATRIX_TYPES[key].builder(G)
        if M is None or M.size == 0:
            return None
        return charpoly_hash(_integer_charpoly_coeffs(M))
    raise ValueError(f"exact_spectral_hash not implemented for matrix '{key}'")
