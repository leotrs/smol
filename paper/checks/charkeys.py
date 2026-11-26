"""Independent recomputation of SMOL's exact cospectral classes.

For each graph (from its graph6 string) and each matrix M, the characteristic polynomial
det(xI - M) is evaluated at fixed integer points x, modulo two primes near 1e9. Two graphs
of the same order are cospectral for M exactly when these values agree (up to a collision
probability of order 1e-18 per pair). Rational matrices are reduced mod p with modular
inverses. None of SMOL's code is used, except as the definition of each matrix in test().

The non-backtracking matrices are 2m x 2m. For T = Z B, where B is the Hashimoto matrix and
Z scales the row of the directed edge u->v by z(v), the determinant lemma gives
    det(xI - T) = prod_{uv in E} (x^2 - z_u z_v) * det(I - diag(z) Atil(x)),
    Atil[u,v] = x / (x^2 - z_u z_v) for uv in E,   Atil[u,u] = -sum_{v~u} z_v / (x^2 - z_u z_v),
an n x n determinant. z = 1 gives B (Ihara-Bass), z(v) = 1/(d(v)-1) (0 if d(v) = 1) gives
the transition matrix of the NB Laplacian, z(v) = C(d(v)-2, k-2) on the cycle core H_k gives
the k-blocking matrix D_k B_k.

Usage: WID=0 NW=4 uv run --no-project --with duckdb --with numpy --with pyarrow python charkeys.py N [N ...]
"""

import sys
from math import comb

import numpy as np

P1, P2 = 1_000_000_007, 998_244_353
X0 = 10_007  # evaluation points X0, X0+1, ...; large enough that x^2 != z_u z_v
NB_POINTS = 91  # 2m <= 90
rng = np.random.default_rng(12345)
R1 = rng.integers(1, P1, size=NB_POINTS)
R2 = rng.integers(1, P2, size=NB_POINTS)


def decode(g6s, n):
    """graph6 strings of order n -> (B, n, n) int64 adjacency."""
    B = len(g6s)
    A = np.zeros((B, n, n), dtype=np.int64)
    if n < 2:
        return A
    nbits = n * (n - 1) // 2
    nch = (nbits + 5) // 6
    raw = np.frombuffer("".join(s[1:1 + nch] for s in g6s).encode(), dtype=np.uint8).reshape(B, nch) - 63
    bits = ((raw[:, :, None] >> np.arange(5, -1, -1)) & 1).reshape(B, nch * 6)[:, :nbits]
    k = 0
    for j in range(1, n):
        for i in range(j):
            A[:, i, j] = A[:, j, i] = bits[:, k]
            k += 1
    return A


def modpow(a, e, p):
    a = a % p
    r = np.ones_like(a)
    while e:
        if e & 1:
            r = r * a % p
        a = a * a % p
        e >>= 1
    return r


def inv(a, p):
    return modpow(a, p - 2, p)


def det_mod(X, p):
    """Batched determinant mod p of (B, N, N) int64 arrays. Fraction-free elimination:
    each step scales the rows below the pivot by the pivot, which is divided out once."""
    X = X.copy() % p
    Bn, N, _ = X.shape
    det = np.ones(Bn, dtype=np.int64)
    den = np.ones(Bn, dtype=np.int64)
    idx = np.arange(Bn)
    for c in range(N):
        nz = X[:, c:, c] != 0
        has = nz.any(axis=1)
        r = nz.argmax(axis=1) + c
        det[~has] = 0
        swap = has & (r != c)
        if swap.any():
            rows_c = X[idx[swap], c].copy()
            X[idx[swap], c] = X[idx[swap], r[swap]]
            X[idx[swap], r[swap]] = rows_c
            det[swap] = (p - det[swap]) % p
        piv = np.where(has, X[:, c, c], 1)
        det = det * piv % p
        if c + 1 < N:
            f = X[:, c + 1:, c].copy()
            X[:, c + 1:, c:] = (X[:, c + 1:, c:] * piv[:, None, None] % p - f[:, :, None] * X[:, c, None, c:] % p) % p
            for _ in range(N - c - 1):
                den = den * piv % p
    return det * inv(den, p) % p


def charvals(M, p, npts):
    """Values of det(xI - M) mod p at x = X0, ..., X0+npts-1, for (B, n, n) M mod p."""
    Bn, n, _ = M.shape
    I = np.eye(n, dtype=np.int64)
    out = np.empty((Bn, npts), dtype=np.int64)
    for t in range(npts):
        out[:, t] = det_mod(((X0 + t) * I - M) % p, p) if n else 1
    return out


def nb_charvals(A, z, zz_of, zcode, p, npts):
    """Values of det(xI - Z B) mod p via the n x n reduction in the module docstring, at the
    first 2m+1 points (zero-padded to npts; graphs with different m are never compared).
    A: (B, n, n) 0/1 adjacency of the graph that carries B. z: (B, n) weights mod p.
    zcode: (B, n, n) small nonnegative ints with z_u z_v = zz_of(zcode) mod p, so that the
    inverses of x^2 - z_u z_v come from a lookup table."""
    Bn, n, _ = A.shape
    out = np.zeros((Bn, npts), dtype=np.int64)
    m = A.sum(axis=(1, 2)) // 2
    iu = np.triu_indices(n, 1)
    codes = np.arange(int(zcode.max()) + 1 if zcode.size else 1)
    zzt = zz_of(codes, p)
    for mm in np.unique(m):
        sel = m == mm
        As, zs, cs = A[sel], z[sel], zcode[sel]
        edge = As[:, iu[0], iu[1]] == 1
        for t in range(min(2 * int(mm) + 1, npts)):
            x = X0 + t
            dt = (x * x - zzt) % p
            delta, dinv = dt[cs], inv(dt, p)[cs]
            Atil = As * (x * dinv % p) % p
            diag = (As * (zs[:, None, :] * dinv % p) % p).sum(axis=2) % p
            Atil[:, np.arange(n), np.arange(n)] = (p - diag) % p
            M = (np.eye(n, dtype=np.int64) - zs[:, :, None] * Atil % p) % p
            d = det_mod(M, p)
            dl = np.where(edge, delta[:, iu[0], iu[1]], 1)
            prod = np.ones(dl.shape[0], dtype=np.int64)
            for col in range(dl.shape[1]):
                prod = prod * dl[:, col] % p
            out[sel, t] = prod * d % p
    return out


def compress(v, p, r):
    k = np.zeros(v.shape[0], dtype=np.int64)
    for t in range(v.shape[1]):
        k = (k + v[:, t] * r[t]) % p
    return k


def key(fn):
    """Run fn(p) for both primes and combine into one int64 key per graph."""
    v1, v2 = fn(P1), fn(P2)
    return compress(v1, P1, R1) * P2 + compress(v2, P2, R2)


def distances(A):
    Bn, n, _ = A.shape
    D = np.full((Bn, n, n), -1, dtype=np.int64)
    D[:, np.arange(n), np.arange(n)] = 0
    reach = np.broadcast_to(np.eye(n, dtype=np.int64), (Bn, n, n)).copy()
    for k in range(1, n):
        reach = ((reach @ A) > 0).astype(np.int64) | reach
        D[(reach == 1) & (D < 0)] = k
    return D


def rat(num, den, p):
    """num/den mod p, elementwise (den != 0 mod p)."""
    return np.asarray(num, dtype=np.int64) % p * inv(np.asarray(den, dtype=np.int64) % p, p) % p


def yoon_W(A, m, p):
    """sum_k a_{k,m} P_k mod p, with a_{k,m} = (-1)^(k+1) 2 C(2m, m-k) / (k^2 C(2m, m))."""
    n = A.shape[1]
    d = A.sum(axis=2)
    A2 = A @ A
    P = {1: A, 2: A2 * (1 - np.eye(n, dtype=np.int64))}
    if m >= 3:
        P3 = A2 @ A - (d[:, :, None] + d[:, None, :] - 1) * A
        P[3] = P3 * (1 - np.eye(n, dtype=np.int64))
    W = np.zeros_like(A)
    for k in range(1, m + 1):
        a = rat((-1) ** (k + 1) * 2 * comb(2 * m, m - k), k * k * comb(2 * m, m), p)
        W = (W + int(a) * (P[k] % p)) % p
    return W


def two_core_mask(A, keep):
    """Iteratively drop vertices of degree < 2 inside the induced subgraph on `keep`."""
    keep = keep.copy()
    while True:
        Ak = A * keep[:, :, None] * keep[:, None, :]
        drop = keep & (Ak.sum(axis=2) < 2)
        if not drop.any():
            return keep
        keep &= ~drop


def all_keys(g6s, n):
    A = decode(g6s, n)
    Bn = len(g6s)
    I = np.eye(n, dtype=np.int64)
    d = A.sum(axis=2)
    m = d.sum(axis=1) // 2
    D = distances(A)
    conn = (D >= 0).all(axis=(1, 2))
    Dc = np.where(D < 0, 0, D)
    tr = Dc.sum(axis=2)
    keys = {"n": np.full(Bn, n), "m": m}
    np1 = n + 1

    keys["adj"] = key(lambda p: charvals(A % p, p, np1))
    keys["kirchhoff"] = key(lambda p: charvals((d[:, :, None] * I - A) % p, p, np1))
    keys["signless"] = key(lambda p: charvals((d[:, :, None] * I + A) % p, p, np1))

    def lap(p):
        dinv = np.where(d > 0, inv(np.where(d > 0, d, 1), p), 0)
        return charvals((I - dinv[:, :, None] * A % p) % p, p, np1)
    keys["lap"] = key(lap)

    keys["dist"] = key(lambda p: charvals(Dc % p, p, np1))
    keys["distlap"] = key(lambda p: charvals((tr[:, :, None] * I - Dc) % p, p, np1))
    keys["distsign"] = key(lambda p: charvals((tr[:, :, None] * I + Dc) % p, p, np1))

    def distnorm(p):
        tinv = inv(np.where(tr > 0, tr, 1), p)
        return charvals((I - tinv[:, :, None] * Dc % p) % p, p, np1)
    keys["distnorm"] = key(distnorm)

    ecc = Dc.max(axis=2)
    E = np.where(Dc == np.minimum(ecc[:, :, None], ecc[:, None, :]), Dc, 0) * (1 - I)
    keys["ecc"] = key(lambda p: charvals(E % p, p, np1))

    for mm in (2, 3):
        def yoon(p, mm=mm):
            W = yoon_W(A, mm, p)
            return charvals((W.sum(axis=2)[:, :, None] % p * I - W) % p, p, np1)
        keys[f"yoon{mm}"] = key(yoon) if n > mm else np.zeros(Bn, dtype=np.int64)

    ones = np.ones((Bn, n), dtype=np.int64)
    keys["nb"] = key(lambda p: nb_charvals(A, ones, lambda c, p: np.ones_like(c), np.zeros((Bn, n, n), dtype=np.int64), p, NB_POINTS))

    dm1 = np.where(d >= 2, d - 1, 0)
    nbl_code = dm1[:, :, None] * dm1[:, None, :]  # (d_u-1)(d_v-1); z_u z_v = 1/code, 0 if code = 0

    def nbl(p):
        z = np.where(d >= 2, inv(np.where(d >= 2, d - 1, 1), p), 0)
        zz_of = lambda c, p: np.where(c > 0, inv(np.where(c > 0, c, 1), p), 0)
        return nb_charvals(A, z, zz_of, nbl_code, p, NB_POINTS)
    keys["nbl"] = key(nbl)

    # k-blocking matrices D_k B_k for k = 2..9 (zero matrix when H_k is empty)
    for k in range(2, 10):
        core = two_core_mask(A, d >= k)
        Ak = A * core[:, :, None] * core[:, None, :]
        mk = Ak.sum(axis=(1, 2)) // 2
        zk = np.where(core & (d >= 2), np.vectorize(lambda dv: comb(int(dv) - 2, k - 2) if dv >= 2 else 0)(d), 0)
        kk = np.zeros(Bn, dtype=np.int64)
        live = mk > 0
        if live.any():
            zl = zk[live]
            code = zl[:, :, None] * zl[:, None, :]
            kk[live] = key(lambda p: nb_charvals(Ak[live], zl % p, lambda c, p: c % p, code, p, NB_POINTS))
        keys[f"kb{k}"] = kk
        keys[f"kb{k}_m"] = mk
        keys[f"kb{k}_size"] = (Ak * np.vectorize(lambda dv: comb(int(dv) - 1, k - 2) if dv >= 1 else 0)(d)[:, None, :]).sum(axis=(1, 2))

    keys["connected"] = conn
    keys["maxdeg"] = d.max(axis=1)
    keys["mindeg"] = d.min(axis=1)
    return keys


def kb_family(K):
    """Tuple signature of the k-blocking family per graph (None for a forest), from the keys."""
    out = []
    for i in range(len(K["n"])):
        parts = []
        k = 2
        while k <= 9 and K[f"kb{k}_m"][i] > 0:
            parts.append((int(K[f"kb{k}"][i]), int(K[f"kb{k}_m"][i]), int(K[f"kb{k}_size"][i])))
            k += 1
        out.append(tuple(parts) if parts else None)
    return out


def test(nmax=7):
    """Compare the keys with float eigenvalues of SMOL's matrix builders (exact enough at small n)."""
    import networkx as nx
    sys.path.insert(0, "/Users/leo.torres/research/smol")
    from db import matrices as Mx
    builders = {"adj": Mx.adjacency_matrix, "kirchhoff": Mx.kirchhoff_laplacian,
                "signless": Mx.signless_laplacian, "lap": Mx.laplacian_matrix,
                "nb": Mx.nonbacktracking_matrix, "nbl": Mx.nonbacktracking_laplacian,
                "dist": Mx.distance_matrix, "distlap": Mx.distance_laplacian,
                "distsign": Mx.distance_signless_laplacian,
                "distnorm": Mx.normalized_distance_laplacian, "ecc": Mx.eccentricity_matrix,
                "yoon2": Mx.yoon2_matrix, "yoon3": Mx.yoon3_matrix}
    import subprocess
    from db.spectrum import kblock_family_signature
    for n in range(1, nmax + 1):
        g6s = subprocess.run(["geng", "-q", str(n)], capture_output=True, text=True).stdout.split()
        K = all_keys(g6s, n)
        for name, b in builders.items():
            fl = []
            for s in g6s:
                M = b(nx.from_graph6_bytes(s.encode()))
                if M is None or M.size == 0:
                    fl.append(None if M is None else ())
                    continue
                ev = np.linalg.eigvals(M)
                fl.append(tuple(sorted(np.round(ev.real, 6) + 1j * np.round(np.abs(ev.imag), 6), key=lambda c: (c.real, c.imag))))
            ok = [i for i, f in enumerate(fl) if f is not None]
            part_f = {}
            part_k = {}
            for i in ok:
                kk = (K[name][i], K["m"][i]) if name in ("nb", "nbl") else K[name][i]
                part_f.setdefault(fl[i], set()).add(i)
                part_k.setdefault(kk, set()).add(i)
            same = sorted(map(sorted, part_f.values())) == sorted(map(sorted, part_k.values()))
            if not same:
                print(f"n={n} {name}: MISMATCH")
        sig = [kblock_family_signature(nx.from_graph6_bytes(x.encode())) for x in g6s]
        mine = kb_family(K)
        pf, pk = {}, {}
        for i in range(len(g6s)):
            if sig[i] is not None:
                pf.setdefault(sig[i], set()).add(i)
            if mine[i] is not None:
                pk.setdefault(mine[i], set()).add(i)
        if sorted(map(sorted, pf.values())) != sorted(map(sorted, pk.values())):
            print(f"n={n} kblock_family: MISMATCH")
        print(f"n={n} tested ({len(g6s)} graphs)")


if __name__ == "__main__":
    if sys.argv[1] == "test":
        test(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
        sys.exit()
    from chunks import run
    run("keys", [int(x) for x in sys.argv[1:]], 50_000,
        lambda g6, n: {k: np.asarray(v) for k, v in all_keys(g6, n).items()})
