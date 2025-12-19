"""Matrix computation for graphs."""

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
