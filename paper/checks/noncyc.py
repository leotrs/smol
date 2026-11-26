"""Characteristic polynomial of the non-k-cycling matrices (k = 3, 4) through a smaller determinant.

P_k acts on directed paths with k vertices (u_1, ..., u_k). From alpha = (u_1, ..., u_k) it
steps to (u_2, ..., u_k, y) for every neighbour y of u_k outside {u_1, ..., u_k}. Write
    P_k = F G - C,
where G maps a path with k-1 vertices to each of its allowed one-vertex extensions, F maps a
path with k vertices to its last k-1 vertices, and C rotates (u_1, ..., u_k) to
(u_2, ..., u_k, u_1) when u_k ~ u_1, i.e. when the path closes a k-cycle. Then G F = P_{k-1}
(P_2 = B), C^k = I on the paths that lie on k-cycles, and C = 0 elsewhere. The determinant
lemma gives
    det(xI - P_k) = det(xI + C) det(I - G (xI + C)^{-1} F),
    det(xI + C) = x^(N_k - k c) (x^k - (-1)^k)^c,   c = number of C-orbits,
    (xI + C)^{-1} = sum_{j<k} (-1)^j x^(k-1-j) C^j / (x^k - (-1)^k) on cycle paths, I/x elsewhere.
The second determinant has the size of the path space one level down: 2m for k = 3, and the
number of paths with 3 vertices for k = 4.
"""

import numpy as np


def paths(adj, k):
    """Directed paths with k distinct vertices, as tuples, in a fixed order."""
    n = len(adj)
    out = [(v,) for v in range(n)]
    for _ in range(k - 1):
        out = [p + (y,) for p in out for y in adj[p[-1]] if y not in p]
    return out


def det_parts(adj, k, x, field):
    """(N_k, c, scalar factor, reduced matrix) at the point x, over `field` (float or mod p)."""
    Pk = paths(adj, k)
    low = paths(adj, k - 1)
    idx = {p: i for i, p in enumerate(low)}
    on_cycle = [p[0] in adj[p[-1]] for p in Pk]
    c = sum(on_cycle) // k
    sign = (-1) ** k
    inv_x = field.inv(x)
    inv_q = field.inv(field.sub(field.pow(x, k), sign))
    Q = field.zeros(len(low))
    for p, cyc in zip(Pk, on_cycle):
        a = idx[p[:-1]]
        if not cyc:
            field.add_to(Q, a, idx[p[1:]], inv_x)
            continue
        q = p
        for j in range(k):
            coef = field.mul(field.pow(x, k - 1 - j), inv_q)
            if j % 2:
                coef = field.neg(coef)
            field.add_to(Q, a, idx[q[1:]], coef)
            q = q[1:] + q[:1]
    scal = field.mul(field.pow(x, len(Pk) - k * c), field.pow(field.sub(field.pow(x, k), sign), c))
    return len(Pk), c, scal, Q


class Float:
    inv = staticmethod(lambda a: 1.0 / a)
    sub = staticmethod(lambda a, b: a - b)
    mul = staticmethod(lambda a, b: a * b)
    neg = staticmethod(lambda a: -a)
    pow = staticmethod(lambda a, e: a ** e)
    zeros = staticmethod(lambda n: np.zeros((n, n)))

    @staticmethod
    def add_to(Q, i, j, v):
        Q[i, j] += v

    @staticmethod
    def det_I_minus(Q):
        return np.linalg.det(np.eye(len(Q)) - Q) if len(Q) else 1.0


def charpoly_at(adj, k, x):
    N, c, scal, Q = det_parts(adj, k, x, Float)
    return scal * Float.det_I_minus(Q)


def test():
    import sys
    import subprocess
    import networkx as nx
    sys.path.insert(0, "/Users/leo.torres/research/smol")
    from db import matrices as Mx
    worst = 0.0
    count = 0
    for n in range(3, 8):
        for s in subprocess.run(["geng", "-q", str(n)], capture_output=True, text=True).stdout.split():
            G = nx.from_graph6_bytes(s.encode())
            adj = [sorted(G[v]) for v in range(n)]
            for k, build in ((3, Mx.non3cyc_matrix), (4, Mx.non4cyc_matrix)):
                P = build(G)
                for x in (1.3, -0.7):
                    ref = np.linalg.det(x * np.eye(len(P)) - P) if len(P) else 1.0
                    got = charpoly_at(adj, k, x)
                    worst = max(worst, abs(got - ref) / max(1.0, abs(ref)))
                if len(P) != len(paths(adj, k)):
                    print("dimension mismatch", s, k, len(P), len(paths(adj, k)))
            count += 1
    print(f"{count} graphs, n = 3..7, k = 3 and 4: worst relative difference {worst:.2e}")


if __name__ == "__main__":
    test()
