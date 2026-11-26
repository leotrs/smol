"""Compiled, mod-p version of noncyc.py: values of det(x I - P_k) mod p for k = 3, 4.

Two graphs of the same order are non-k-cycling cospectral exactly when their characteristic
polynomials agree. A key built from the values at a few fixed points modulo primes near 2^31
agrees for two different polynomials of degree N with probability at most N/p per point.
"""
import numba as nb
import numpy as np

P1, P2 = 2_147_483_647, 2_147_483_629  # primes below 2^31; products fit in int64


@nb.njit(cache=True)
def powmod(a, e, p):
    r = 1
    a %= p
    while e:
        if e & 1:
            r = r * a % p
        a = a * a % p
        e >>= 1
    return r


@nb.njit(cache=True)
def det_mod(M, p):
    n = M.shape[0]
    det = 1
    for c in range(n):
        r = c
        while r < n and M[r, c] == 0:
            r += 1
        if r == n:
            return 0
        if r != c:
            for j in range(c, n):
                M[c, j], M[r, j] = M[r, j], M[c, j]
            det = p - det if det else 0
        piv = M[c, c]
        det = det * piv % p
        inv = powmod(piv, p - 2, p)
        for i in range(c + 1, n):
            f = M[i, c] * inv % p
            if f:
                for j in range(c, n):
                    M[i, j] = (M[i, j] - f * M[c, j]) % p
    return det


@nb.njit(cache=True)
def enum_paths(A, n, k):
    """All directed paths with k distinct vertices, as rows of a (count, k) array."""
    cap = 1
    for i in range(k):
        cap *= n - i
    out = np.empty((max(cap, 1), k), dtype=np.int64)
    cnt = 0
    stack = np.empty(k, dtype=np.int64)
    # iterative DFS over vertex sequences
    for v in range(n):
        stack[0] = v
        if k == 1:
            out[cnt, 0] = v
            cnt += 1
            continue
        nxt = np.zeros(k, dtype=np.int64)
        depth = 1
        nxt[1] = 0
        while depth > 0:
            if nxt[depth] >= n:
                depth -= 1
                if depth > 0:
                    nxt[depth] += 1
                continue
            y = nxt[depth]
            ok = A[stack[depth - 1], y] == 1
            if ok:
                for t in range(depth):
                    if stack[t] == y:
                        ok = False
                        break
            if not ok:
                nxt[depth] += 1
                continue
            stack[depth] = y
            if depth == k - 1:
                for t in range(k):
                    out[cnt, t] = stack[t]
                cnt += 1
                nxt[depth] += 1
            else:
                depth += 1
                nxt[depth] = 0
    return out[:cnt]


@nb.njit(cache=True)
def code(path, lo, hi, n):
    c = 0
    for t in range(lo, hi):
        c = c * n + path[t]
    return c


@nb.njit(cache=True)
def charval(A, n, k, x, p):
    """det(x I - P_k) mod p, and the dimension N_k."""
    Pk = enum_paths(A, n, k)
    low = enum_paths(A, n, k - 1)
    N, L = Pk.shape[0], low.shape[0]
    if N == 0:
        return 1, 0
    table = -np.ones(n ** (k - 1), dtype=np.int64)
    for i in range(L):
        table[code(low[i], 0, k - 1, n)] = i
    sign = 1 if k % 2 == 0 else p - 1  # (-1)^k mod p
    xk = powmod(x, k, p)
    q = (xk - sign) % p
    inv_x = powmod(x, p - 2, p)
    inv_q = powmod(q, p - 2, p)
    coef = np.empty(k, dtype=np.int64)
    for j in range(k):
        cj = powmod(x, k - 1 - j, p) * inv_q % p
        coef[j] = (p - cj) % p if j % 2 else cj
    Q = np.zeros((L, L), dtype=np.int64)
    rot = np.empty(k, dtype=np.int64)
    ncyc = 0
    for i in range(N):
        a = table[code(Pk[i], 0, k - 1, n)]
        if A[Pk[i, k - 1], Pk[i, 0]] == 0:
            b = table[code(Pk[i], 1, k, n)]
            Q[a, b] = (Q[a, b] + inv_x) % p
            continue
        ncyc += 1
        for t in range(k):
            rot[t] = Pk[i, t]
        for j in range(k):
            b = table[code(rot, 1, k, n)]
            Q[a, b] = (Q[a, b] + coef[j]) % p
            first = rot[0]
            for t in range(k - 1):
                rot[t] = rot[t + 1]
            rot[k - 1] = first
    c = ncyc // k
    for i in range(L):
        for j in range(L):
            Q[i, j] = (p - Q[i, j]) % p
        Q[i, i] = (Q[i, i] + 1) % p
    d = det_mod(Q, p)
    scal = powmod(x, N - k * c, p) * powmod(q, c, p) % p
    return scal * d % p, N


def decode(g6, n):
    A = np.zeros((n, n), dtype=np.int64)
    bits = []
    for ch in g6[1:]:
        v = ord(ch) - 63
        bits += [(v >> s) & 1 for s in range(5, -1, -1)]
    t = 0
    for j in range(1, n):
        for i in range(j):
            A[i, j] = A[j, i] = bits[t]
            t += 1
    return A


def test(nmax=7):
    """Compare with float determinants of SMOL's matrices, reduced mod p, on small graphs:
    a mod-p value must match the exact integer charpoly value, so use sympy-free integer check
    via numpy on small dimensions (exact for these sizes with object dtype)."""
    import subprocess
    import sys
    import networkx as nx
    sys.path.insert(0, "/Users/leo.torres/research/smol")
    from db import matrices as Mx
    import sympy
    bad = 0
    tot = 0
    for n in range(3, nmax + 1):
        for s in subprocess.run(["geng", "-q", str(n)], capture_output=True, text=True).stdout.split():
            G = nx.from_graph6_bytes(s.encode())
            A = decode(s, n)
            for k, build in ((3, Mx.non3cyc_matrix), (4, Mx.non4cyc_matrix)):
                P = build(G)
                if len(P) == 0 or len(P) > 60:
                    continue
                x = 7
                ref = int(sympy.Matrix(x * np.eye(len(P), dtype=int) - P.astype(int)).det(method="bareiss"))
                got, N = charval(A, n, k, x, P1)
                tot += 1
                bad += (ref % P1) != got or N != len(P)
    print(f"{tot} exact checks (dimension <= 60), mismatches: {bad}")
