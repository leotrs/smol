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
  - nb: integer charpoly of the 2m x 2m Hashimoto matrix. nbl: monic rational charpoly
    of I - D^{-1}B, denominators cleared.
  - non3cyc, non4cyc, kblock_family: matrices too large for a charpoly in coefficients
    (non4cyc reaches 5040 x 5040 at n = 10). Their hash is built from exact values of
    det(xI - M) at two fixed points modulo two fixed primes, computed through a smaller
    determinant (see _noncyc_charvals and _zb_charval). Equal charpolys always give equal
    hashes; different charpolys of degree N agree at both points with probability at most
    (N / 2^31)^2. No floating point and no random numbers are involved.
"""

import hashlib
from fractions import Fraction
from math import comb, gcd

import networkx as nx
import numpy as np

from flint import fmpz_mat, fmpq_mat, fmpq

from .matrices import adjacency_matrix, nonbacktracking_matrix, open_path_matrix
from .matrix_types import MATRIX_TYPES
from .spectrum import bareiss_poly_det, charpoly_hash

INTEGER_MATRICES = ("adj", "kirchhoff", "signless", "dist", "distlap", "distsign", "ecc")
NORMALIZED_MATRICES = ("lap", "distnorm")
YOON_MATRICES = {"yoon2": 2, "yoon3": 3}
CHARPOLY_MATRICES = INTEGER_MATRICES + NORMALIZED_MATRICES + tuple(YOON_MATRICES)


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


def _nb_charpoly_key(G: nx.Graph) -> str | None:
    """Exact non-backtracking cospectral hash: the integer characteristic
    polynomial of the 2m x 2m Hashimoto matrix B (a 0/1 matrix), computed
    directly. This is NOT the Ihara-Bass reduction. None for edgeless graphs
    (empty spectrum), matching the float convention."""
    B = nonbacktracking_matrix(G)
    if B.shape[0] == 0:
        return None
    M = [[int(round(float(x))) for x in row] for row in B]
    coeffs = [int(c) for c in fmpz_mat(M).charpoly().coeffs()]
    return charpoly_hash(coeffs)


def _nbl_charpoly_key(G: nx.Graph) -> str | None:
    """Exact non-backtracking Laplacian cospectral hash. NBL = I - D^{-1}B is
    rational (B the Hashimoto matrix, D the diagonal of NB out-degrees, with
    zero-out-degree rows left as the identity row, matching the builder). We form
    it exactly over the rationals and hash its monic characteristic polynomial,
    with denominators cleared to a canonical integer tuple. None for edgeless
    graphs."""
    B = nonbacktracking_matrix(G)
    if B.shape[0] == 0:
        return None
    n = B.shape[0]
    Bi = [[int(round(float(B[i][j]))) for j in range(n)] for i in range(n)]
    deg = [sum(Bi[i]) for i in range(n)]
    rows = []
    for i in range(n):
        di = deg[i]
        if di > 0:
            rows.append([fmpq((1 if i == j else 0) * di - Bi[i][j], di) for j in range(n)])
        else:
            rows.append([fmpq(1 if i == j else 0, 1) for j in range(n)])
    coeffs = list(fmpq_mat(rows).charpoly().coeffs())  # monic rational charpoly
    den = 1
    for c in coeffs:
        den = den // gcd(den, int(c.q)) * int(c.q)
    ints = [int(c.p) * (den // int(c.q)) for c in coeffs]
    return charpoly_hash(ints)


# Fixed evaluation points and primes for the value-based exact hashes. Products of two
# residues stay below 2^62, so int64 arithmetic is exact.
_P1, _P2 = 2_147_483_647, 2_147_483_629
_X1, _X2 = 1_000_003, 999_983


def _det_mod(M: np.ndarray, p: int) -> int:
    """Determinant mod p of an integer matrix with entries in [0, p), by elimination."""
    M = M.copy()
    n = M.shape[0]
    det = 1
    for c in range(n):
        nz = np.nonzero(M[c:, c])[0]
        if nz.size == 0:
            return 0
        r = c + int(nz[0])
        if r != c:
            M[[c, r]] = M[[r, c]]
            det = (p - det) % p
        piv = int(M[c, c])
        det = det * piv % p
        f = M[c + 1:, c] * pow(piv, p - 2, p) % p
        M[c + 1:, c:] = (M[c + 1:, c:] - f[:, None] * M[c, c:] % p) % p
    return det


def _paths(G: nx.Graph, k: int) -> list[tuple]:
    """Directed paths with k distinct vertices."""
    out = [(v,) for v in G]
    for _ in range(k - 1):
        out = [q + (y,) for q in out for y in G[q[-1]] if y not in q]
    return out


def _noncyc_charvals(G: nx.Graph, k: int, x: int, p: int) -> tuple[int, int]:
    """(det(xI - P_k) mod p, dim P_k) for the non-k-cycling matrix P_k (k >= 3).

    Arrigo, Higham, Noferini (2020), Thm 5.3 and Prop. 2.3: P_k = W_k - Delta_k with
    W_k = R L^T and L^T R = P_{k-1}, where L, R map each path with k vertices to its first
    and last k-1 vertices. Delta_k sends a path that closes a k-cycle to its rotation, so
    Delta_k^k = I on those paths (c orbits of length k) and Delta_k = 0 elsewhere. By the
    determinant lemma
        det(xI - P_k) = x^(N - kc) (x^k - (-1)^k)^c det(I - L^T (xI + Delta_k)^{-1} R),
    a determinant of the size of the path space one level down.
    """
    Pk, low = _paths(G, k), _paths(G, k - 1)
    N = len(Pk)
    if N == 0:
        return 1, 0
    idx = {q: i for i, q in enumerate(low)}
    sign = 1 if k % 2 == 0 else p - 1
    q_inv = pow((pow(x, k, p) - sign) % p, p - 2, p)
    coef = []
    for j in range(k):
        cj = pow(x, k - 1 - j, p) * q_inv % p
        coef.append((p - cj) % p if j % 2 else cj)
    x_inv = pow(x, p - 2, p)
    Q = np.zeros((len(low), len(low)), dtype=np.int64)
    ncyc = 0
    for path in Pk:
        a = idx[path[:-1]]
        if path[0] not in G[path[-1]]:
            b = idx[path[1:]]
            Q[a, b] = (Q[a, b] + x_inv) % p
            continue
        ncyc += 1
        rot = path
        for j in range(k):
            b = idx[rot[1:]]
            Q[a, b] = (Q[a, b] + coef[j]) % p
            rot = rot[1:] + rot[:1]
    c = ncyc // k
    M = (np.eye(len(low), dtype=np.int64) - Q) % p
    val = pow(x, N - k * c, p) * pow((pow(x, k, p) - sign) % p, c, p) * _det_mod(M, p) % p
    return val, N


def _noncyc_charpoly_key(G: nx.Graph, k: int) -> str | None:
    """Exact non-k-cycling hash; None when P_k is nilpotent (all-zero spectrum)."""
    G = nx.convert_node_labels_to_integers(G)
    v1, N = _noncyc_charvals(G, k, _X1, _P1)
    v2, _ = _noncyc_charvals(G, k, _X2, _P2)
    if v1 == pow(_X1, N, _P1) and v2 == pow(_X2, N, _P2):
        return None
    return hashlib.sha256(f"non{k}cyc-exact|{N}|{v1}|{v2}".encode()).hexdigest()[:16]


def _zb_charval(G: nx.Graph, z: dict, x: int, p: int) -> int:
    """det(xI - ZB) mod p, where B is the Hashimoto matrix of G and Z scales the row of
    u->v by z[v]. With Delta_uv = x^2 - z_u z_v, the determinant lemma gives
        det(xI - ZB) = prod_{uv in E} Delta_uv * det(I - diag(z) Atil),
        Atil[u, v] = x / Delta_uv (uv in E),  Atil[u, u] = -sum_{v ~ u} z_v / Delta_uv."""
    nodes = list(G)
    pos = {v: i for i, v in enumerate(nodes)}
    M = np.eye(len(nodes), dtype=np.int64)
    prod = 1
    for u in nodes:
        diag = 0
        for v in G[u]:
            delta = (x * x - z[u] * z[v]) % p
            dinv = pow(delta, p - 2, p)
            if pos[u] < pos[v]:
                prod = prod * delta % p
            M[pos[u], pos[v]] = (M[pos[u], pos[v]] - z[u] * (x * dinv % p)) % p
            diag = (diag + z[v] * dinv) % p
        M[pos[u], pos[u]] = (M[pos[u], pos[u]] + z[u] * diag) % p
    return prod * _det_mod(M, p) % p


def _kblock_family_key(G: nx.Graph) -> str | None:
    """Exact hash of the k-blocking family {M_k : k = 2 .. }: for each k until the cycle
    core H_k is empty, (m_k, |states(M_k)|, det(xI - D_k B_k) at the two fixed points).
    None for a forest, as in kblock_family_signature."""
    from .matrices import cycle_core, kblocking_size

    parts = []
    k = 2
    while True:
        Hk = cycle_core(G, k)
        if Hk.number_of_edges() == 0:
            break
        z = {v: comb(G.degree(v) - 2, k - 2) for v in Hk}
        parts.append(f"k{k}:{Hk.number_of_edges()}:{kblocking_size(G, k)}:"
                     f"{_zb_charval(Hk, z, _X1, _P1)}:{_zb_charval(Hk, z, _X2, _P2)}")
        k += 1
    if not parts:
        return None
    return hashlib.sha256(("kblock_family-exact|" + "|".join(parts)).encode()).hexdigest()[:16]


def exact_spectral_hash(key: str, G: nx.Graph) -> str | None:
    """Exact charpoly cospectral hash for matrix `key` on graph G, or None if the
    matrix is undefined for G (e.g. distance matrices on disconnected graphs)."""
    if key == "lap":
        return _lap_charpoly_key(G)
    if key == "distnorm":
        return _distnorm_charpoly_key(G)
    if key in YOON_MATRICES:
        return _yoon_charpoly_key(G, YOON_MATRICES[key])
    if key == "nb":
        return _nb_charpoly_key(G)
    if key == "nbl":
        return _nbl_charpoly_key(G)
    if key == "non3cyc":
        return _noncyc_charpoly_key(G, 3)
    if key == "non4cyc":
        return _noncyc_charpoly_key(G, 4)
    if key == "kblock_family":
        return _kblock_family_key(G)
    if key in INTEGER_MATRICES:
        M = MATRIX_TYPES[key].builder(G)
        if M is None or M.size == 0:
            return None
        return charpoly_hash(_integer_charpoly_coeffs(M))
    raise ValueError(f"exact_spectral_hash not implemented for matrix '{key}'")
