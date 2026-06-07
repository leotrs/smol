"""Matrix computation for graphs."""

from math import comb

import numpy as np
import networkx as nx


def adjacency_matrix(G: nx.Graph) -> np.ndarray:
    """Return the adjacency matrix as a dense numpy array."""
    return nx.to_numpy_array(G, dtype=np.float64)


def kirchhoff_laplacian(G: nx.Graph) -> np.ndarray:
    """
    Return the Kirchhoff (combinatorial) Laplacian L = D - A.

    Also known as the combinatorial Laplacian or standard Laplacian.
    - Eigenvalues: 0 = λ₁ ≤ λ₂ ≤ ... ≤ λₙ
    - λ₂ is the algebraic connectivity (Fiedler value)
    - Related to spanning trees, cuts, and graph connectivity
    """
    A = adjacency_matrix(G)
    degrees = A.sum(axis=1)
    D = np.diag(degrees)
    return D - A


def signless_laplacian(G: nx.Graph) -> np.ndarray:
    """
    Return the signless Laplacian Q = D + A.

    The "positive" counterpart to the Kirchhoff Laplacian.
    - All eigenvalues are non-negative
    - Related to chromatic number and bipartiteness detection
    - Largest eigenvalue is related to maximum degree
    """
    A = adjacency_matrix(G)
    degrees = A.sum(axis=1)
    D = np.diag(degrees)
    return D + A


def seidel_matrix(G: nx.Graph) -> np.ndarray:
    """
    Return the Seidel matrix S = J - I - 2A.

    Entries are 0 on the diagonal, -1 between adjacent vertices, and +1
    between non-adjacent vertices. Real symmetric; defined for all graphs.
    The Seidel spectrum is invariant under Seidel switching.
    """
    A = adjacency_matrix(G)
    n = A.shape[0]
    return np.ones((n, n)) - np.eye(n) - 2.0 * A


def laplacian_matrix(G: nx.Graph) -> np.ndarray:
    """
    Return the symmetric normalized Laplacian L = I - D^{-1/2}AD^{-1/2}.

    This has the same eigenvalues as the random walk Laplacian I - D^{-1}A
    (they are similar matrices), but is symmetric so we can use eigvalsh.
    """
    A = adjacency_matrix(G)
    n = A.shape[0]
    degrees = A.sum(axis=1)

    if np.any(degrees == 0):
        degrees_safe = np.where(degrees == 0, 1.0, degrees)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(degrees_safe))
        zero_mask = degrees == 0
        D_inv_sqrt[zero_mask, :] = 0
        D_inv_sqrt[:, zero_mask] = 0
    else:
        D_inv_sqrt = np.diag(1.0 / np.sqrt(degrees))

    return np.eye(n) - D_inv_sqrt @ A @ D_inv_sqrt


def _build_directed_edges(G: nx.Graph) -> list[tuple[int, int]]:
    """
    Build list of directed edges for the non-backtracking operator.
    Each undirected edge {u, v} becomes two directed edges (u, v) and (v, u).
    Returns edges sorted for consistent ordering.
    """
    directed_edges = []
    for u, v in G.edges():
        directed_edges.append((u, v))
        directed_edges.append((v, u))
    directed_edges.sort()
    return directed_edges


def nonbacktracking_matrix(G: nx.Graph) -> np.ndarray:
    """
    Return the non-backtracking (Hashimoto) matrix.

    The NB matrix B is indexed by directed edges. For directed edges e = (u, v)
    and f = (w, x), we have B[e, f] = 1 if v = w and u != x (i.e., f follows e
    without backtracking), and 0 otherwise.

    Returns a 2m x 2m matrix where m is the number of edges.
    """
    if G.number_of_edges() == 0:
        return np.array([]).reshape(0, 0)

    directed_edges = _build_directed_edges(G)
    edge_to_idx = {e: i for i, e in enumerate(directed_edges)}
    num_edges = len(directed_edges)

    B = np.zeros((num_edges, num_edges), dtype=np.float64)

    for e_idx, (u, v) in enumerate(directed_edges):
        for neighbor in G.neighbors(v):
            if neighbor != u:
                f = (v, neighbor)
                f_idx = edge_to_idx[f]
                B[e_idx, f_idx] = 1.0

    return B


def nonbacktracking_laplacian(G: nx.Graph) -> np.ndarray:
    """
    Return the non-backtracking Laplacian matrix.

    L_NB = I - D^{-1} B

    where B is the non-backtracking (Hashimoto) matrix and D is the diagonal
    matrix of out-degrees in the NB graph.
    """
    B = nonbacktracking_matrix(G)

    if B.size == 0:
        return np.array([]).reshape(0, 0)

    out_degrees = B.sum(axis=1)

    if np.any(out_degrees == 0):
        out_degrees_safe = np.where(out_degrees == 0, 1.0, out_degrees)
        D_inv = np.diag(1.0 / out_degrees_safe)
        zero_mask = out_degrees == 0
        D_inv[zero_mask, :] = 0
    else:
        D_inv = np.diag(1.0 / out_degrees)

    return np.eye(B.shape[0]) - D_inv @ B


def distance_matrix(G: nx.Graph) -> np.ndarray | None:
    """
    Return the distance matrix D where D[i,j] is the shortest path length
    between vertices i and j.

    Only defined for connected graphs. Returns None for disconnected graphs.

    Note: This matrix is typically not stored directly; we only compute and
    store its spectrum for cospectral analysis.
    """
    if not nx.is_connected(G):
        return None

    n = G.number_of_nodes()
    if n == 0:
        return np.array([]).reshape(0, 0)

    D = np.zeros((n, n), dtype=np.float64)
    node_list = list(G.nodes())

    lengths = dict(nx.all_pairs_shortest_path_length(G))

    for i, u in enumerate(node_list):
        for j, v in enumerate(node_list):
            D[i, j] = lengths[u][v]

    return D


def cycle_core(G: nx.Graph, k: int) -> nx.Graph:
    """
    Return the cycle core H_k = 2-core(G_k), where G_k is the subgraph of G
    induced on vertices with (global) degree at least k.

    Torres (2026), "The rich are loopy". Strips to the high-degree vertices,
    then keeps only the cyclic part (iteratively remove degree < 2). May be
    empty.
    """
    Gk = G.subgraph([v for v in G.nodes() if G.degree(v) >= k]).copy()
    if Gk.number_of_nodes() == 0:
        return nx.Graph()
    return nx.k_core(Gk, k=2)


def kblocking_matrix(G: nx.Graph, k: int) -> np.ndarray:
    """
    Return the degree-weighted non-backtracking matrix D_k B_k whose spectrum
    equals that of the k-blocking operator M_k (Torres 2026, trace formula).

    B_k is the non-backtracking matrix of the cycle core H_k, indexed by its
    directed edges (u, v); D_k is diagonal with D_k[(u,v)] = C(d_G(v) - 2, k - 2)
    using the *global* degree of v in G. Returns a 0x0 array when H_k is empty.
    For k = 2 this reduces to the ordinary non-backtracking matrix.
    """
    Hk = cycle_core(G, k)
    if Hk.number_of_edges() == 0:
        return np.array([]).reshape(0, 0)
    B = nonbacktracking_matrix(Hk)
    edges = _build_directed_edges(Hk)
    weights = np.array(
        [comb(G.degree(v) - 2, k - 2) for (_, v) in edges], dtype=np.float64
    )
    return weights[:, None] * B  # diag(weights) @ B


def kblock3_matrix(G: nx.Graph) -> np.ndarray:
    """3-blocking operator companion matrix (blocks 2 directions per node)."""
    return kblocking_matrix(G, 3)


def kblock4_matrix(G: nx.Graph) -> np.ndarray:
    """4-blocking operator companion matrix (blocks 3 directions per node)."""
    return kblocking_matrix(G, 4)


def kblocking_size(G: nx.Graph, k: int) -> int:
    """
    Number of states of the k-blocking operator M_k, i.e. its dimension:
    |states(M_k)| = sum over directed edges (u,v) of H_k of C(d_G(v)-1, k-2).

    Two graphs can share the D_k B_k spectrum but differ here (M_k's kernel
    dimension), so this is folded into the k-blocking hash for exact M_k
    cospectrality.
    """
    Hk = cycle_core(G, k)
    if Hk.number_of_edges() == 0:
        return 0
    return sum(comb(G.degree(v) - 1, k - 2) for (_, v) in _build_directed_edges(Hk))


def kblock3_size(G: nx.Graph) -> int:
    return kblocking_size(G, 3)


def kblock4_size(G: nx.Graph) -> int:
    return kblocking_size(G, 4)


def open_path_matrix(G: nx.Graph, k: int) -> np.ndarray:
    """
    Yoon's length-k open path matrix P_{G,k}: (i,j) entry is the number of
    open (simple) paths of length k from v_i to v_j, with zero diagonal.

    P_{G,1} = A. For k=2,3 the validated closed forms are used (diag(A^2)=D):
      P_{G,2} = A^2 with zeroed diagonal (= common-neighbor counts),
      P_{G,3} = A^3 - (d_i + d_j - 1) A_{ij}, zeroed diagonal.
    """
    A = adjacency_matrix(G)
    if k == 1:
        return A
    if k == 2:
        P = A @ A
        np.fill_diagonal(P, 0.0)
        return P
    if k == 3:
        d = A.sum(axis=1)
        P = A @ A @ A - (d[:, None] + d[None, :] - 1.0) * A
        np.fill_diagonal(P, 0.0)
        return P
    raise ValueError("open_path_matrix is only implemented for k <= 3")


def _yoon_coefficient(k: int, m: int) -> float:
    """a_{k,m} = (-1)^{k+1} * 2 C(2m, m-k) / (k^2 C(2m, m))  (Yoon, Thm 2.2)."""
    return (-1) ** (k + 1) * 2 * comb(2 * m, m - k) / (k ** 2 * comb(2 * m, m))


def m_laplacian(G: nx.Graph, m: int) -> np.ndarray | None:
    """
    Yoon's m-Laplacian L^{(m)}_G: the Laplacian of the reweighted (signed)
    graph whose adjacency is sum_{k=1}^m a_{k,m} P_{G,k}. Real symmetric.

    Defined only for n > m (returns None otherwise); m=1 is the Kirchhoff
    Laplacian. Cross-checked against Remark 6.1 (m=2) and Prop 6.2.
    """
    n = G.number_of_nodes()
    if n <= m:
        return None
    W = np.zeros((n, n), dtype=np.float64)
    for k in range(1, m + 1):
        W += _yoon_coefficient(k, m) * open_path_matrix(G, k)
    return np.diag(W.sum(axis=1)) - W


def yoon2_matrix(G: nx.Graph) -> np.ndarray | None:
    """Yoon 2-Laplacian (2m=4th-order accuracy). None for n <= 2."""
    return m_laplacian(G, 2)


def yoon3_matrix(G: nx.Graph) -> np.ndarray | None:
    """Yoon 3-Laplacian (2m=6th-order accuracy). None for n <= 3."""
    return m_laplacian(G, 3)


def _source_target(M: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Source (L) and target (R) matrices of the directed graph with adjacency M
    (Arrigo-Noferini Def. 2.2): rows index the edges (nonzeros of M), columns
    index nodes. L[e, a] = 1 if a is the source of edge e, R[e, b] = 1 if b is
    its target.
    """
    E = np.argwhere(M != 0)
    m, N = len(E), M.shape[0]
    L = np.zeros((m, N))
    R = np.zeros((m, N))
    if m:
        L[np.arange(m), E[:, 0]] = 1.0
        R[np.arange(m), E[:, 1]] = 1.0
    return L, R


def non_k_cycling_matrix(G: nx.Graph, k: int) -> np.ndarray:
    """
    Arrigo-Noferini non-k-cycling matrix P_k (Def. 5.2 / Thm 5.3), built by the
    recursion P_1 = A and, at each level, W = R L^T, Delta = W o (W^T)^{level-1},
    P = W - Delta, where L,R are the source/target matrices of the previous P and
    'o' is the entrywise (Hadamard) product. k=2 is the Hashimoto matrix.

    Rows/columns are indexed by open paths of length k-1; the spectrum is complex
    (non-symmetric). Trees and graphs whose cycles are all shorter than k give a
    nilpotent (all-zero spectrum) matrix.
    """
    P = adjacency_matrix(G).astype(np.float64)
    for level in range(2, k + 1):
        if P.shape[0] == 0:
            break
        L, R = _source_target(P)
        W = R @ L.T
        P = W - W * np.linalg.matrix_power(W.T, level - 1)
    return P


def non3cyc_matrix(G: nx.Graph) -> np.ndarray:
    """Non-3-cycling matrix P_3 (removes backtracking and triangles)."""
    return non_k_cycling_matrix(G, 3)


def non4cyc_matrix(G: nx.Graph) -> np.ndarray:
    """Non-4-cycling matrix P_4 (removes backtracking, triangles, squares)."""
    return non_k_cycling_matrix(G, 4)


def distance_laplacian(G: nx.Graph) -> np.ndarray | None:
    """
    Return the distance Laplacian D_L = Tr - Dist.

    Tr is the diagonal matrix of vertex transmissions (row sums of the distance
    matrix) and Dist is the distance matrix. Real symmetric, positive
    semidefinite. Only defined for connected graphs (returns None otherwise).
    """
    Dist = distance_matrix(G)
    if Dist is None:
        return None
    Tr = np.diag(Dist.sum(axis=1))
    return Tr - Dist


def distance_signless_laplacian(G: nx.Graph) -> np.ndarray | None:
    """
    Return the distance signless Laplacian D_Q = Tr + Dist.

    The positive counterpart to the distance Laplacian. Real symmetric.
    Only defined for connected graphs (returns None otherwise).
    """
    Dist = distance_matrix(G)
    if Dist is None:
        return None
    Tr = np.diag(Dist.sum(axis=1))
    return Tr + Dist
