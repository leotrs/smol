"""Tests for matrix computations."""

import numpy as np
import networkx as nx

from db.matrices import (
    adjacency_matrix,
    laplacian_matrix,
    nonbacktracking_matrix,
    nonbacktracking_laplacian,
)


def test_adjacency_matrix_path():
    """Test adjacency matrix for P3 (path on 3 vertices)."""
    G = nx.path_graph(3)
    A = adjacency_matrix(G)

    expected = np.array(
        [
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
        ],
        dtype=np.float64,
    )

    np.testing.assert_array_equal(A, expected)


def test_adjacency_matrix_complete():
    """Test adjacency matrix for K4."""
    G = nx.complete_graph(4)
    A = adjacency_matrix(G)

    assert A.shape == (4, 4)
    assert np.all(np.diag(A) == 0)
    assert A.sum() == 4 * 3  # 4 vertices, each connected to 3 others


def test_laplacian_matrix_path():
    """Test symmetric normalized Laplacian for P3."""
    G = nx.path_graph(3)
    L = laplacian_matrix(G)

    # Symmetric normalized Laplacian: L = I - D^{-1/2}AD^{-1/2}
    # For P3: degrees are [1, 2, 1]
    sqrt2 = np.sqrt(2)
    expected = np.array(
        [
            [1, -1/sqrt2, 0],
            [-1/sqrt2, 1, -1/sqrt2],
            [0, -1/sqrt2, 1],
        ],
        dtype=np.float64,
    )

    np.testing.assert_array_almost_equal(L, expected)


def test_laplacian_eigenvalue_bounds():
    """Symmetric normalized Laplacian eigenvalues should be in [0, 2]."""
    G = nx.complete_graph(5)
    L = laplacian_matrix(G)
    eigs = np.linalg.eigvalsh(L)

    assert np.all(eigs >= -1e-10)
    assert np.all(eigs <= 2 + 1e-10)


def test_nonbacktracking_matrix_path():
    """Test NB matrix for P3 (path on 3 vertices)."""
    G = nx.path_graph(3)
    B = nonbacktracking_matrix(G)

    # P3 has 2 edges -> 4 directed edges
    # Directed edges: (0,1), (1,0), (1,2), (2,1)
    # NB transitions: (0,1)->(1,2), (2,1)->(1,0)
    assert B.shape == (4, 4)
    assert B.sum() == 2  # Only two non-backtracking transitions


def test_nonbacktracking_matrix_cycle():
    """Test NB matrix for C4 (cycle on 4 vertices)."""
    G = nx.cycle_graph(4)
    B = nonbacktracking_matrix(G)

    # C4 has 4 edges -> 8 directed edges
    # Each directed edge has exactly 1 non-backtracking continuation
    assert B.shape == (8, 8)
    assert B.sum() == 8


def test_nonbacktracking_matrix_empty():
    """Test NB matrix for graph with no edges."""
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2])
    B = nonbacktracking_matrix(G)

    assert B.shape == (0, 0)


def test_nonbacktracking_laplacian_shape():
    """Test NB Laplacian has correct shape."""
    G = nx.complete_graph(4)
    L_NB = nonbacktracking_laplacian(G)

    # K4 has 6 edges -> 12 directed edges
    assert L_NB.shape == (12, 12)


def test_nonbacktracking_laplacian_eigenvalue_bounds():
    """NB Laplacian eigenvalues should be in reasonable range for normalized Laplacian."""
    G = nx.cycle_graph(6)
    L_NB = nonbacktracking_laplacian(G)

    eigs = np.linalg.eigvals(L_NB)
    # Eigenvalues of normalized Laplacian are typically in [0, 2]
    # but NB Laplacian can have complex eigenvalues
    magnitudes = np.abs(eigs)
    assert np.all(magnitudes <= 3)  # Generous bound


def test_nonbacktracking_matrix_k3():
    """Test NB matrix for K3 (triangle)."""
    G = nx.complete_graph(3)
    B = nonbacktracking_matrix(G)

    # K3 has 3 edges -> 6 directed edges
    # Each directed edge (u,v) can continue to 1 other edge (v,w) where w != u
    assert B.shape == (6, 6)
    assert B.sum() == 6  # Each directed edge has 1 continuation
