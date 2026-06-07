"""Tests for matrix computations."""

import numpy as np
import networkx as nx

from db.matrices import (
    adjacency_matrix,
    kirchhoff_laplacian,
    signless_laplacian,
    laplacian_matrix,
    nonbacktracking_matrix,
    nonbacktracking_laplacian,
    seidel_matrix,
    distance_matrix,
    distance_laplacian,
    distance_signless_laplacian,
)


def test_distance_laplacians_path():
    """D_L = Tr - Dist and D_Q = Tr + Dist on P3."""
    G = nx.path_graph(3)  # distances: 0-1=1, 0-2=2, 1-2=1
    Dist = distance_matrix(G)
    transmissions = Dist.sum(axis=1)  # [3, 2, 3]
    DL = distance_laplacian(G)
    DQ = distance_signless_laplacian(G)
    assert np.array_equal(np.diag(DL), transmissions)
    assert np.array_equal(DL + Dist, np.diag(transmissions))   # DL = Tr - Dist
    assert np.array_equal(DQ - Dist, np.diag(transmissions))   # DQ = Tr + Dist
    # Distance Laplacian is symmetric with zero row sums.
    assert np.array_equal(DL, DL.T)
    assert np.allclose(DL.sum(axis=1), 0)


def test_cycle_core_and_kblocking():
    from db.matrices import (
        cycle_core, kblocking_matrix, kblock3_matrix, kblock4_matrix,
    )
    K4 = nx.complete_graph(4)
    # Cycle core at k=3 is all of K4 (every vertex has degree 3 and lies on cycles).
    H3 = cycle_core(K4, 3)
    assert H3.number_of_nodes() == 4 and H3.number_of_edges() == 6
    # No vertex has degree >= 4, so the k=4 cycle core (and matrix) is empty.
    assert cycle_core(K4, 4).number_of_nodes() == 0
    assert kblock4_matrix(K4).size == 0
    assert kblock3_matrix(K4).size > 0
    # k=2 reduces to the ordinary non-backtracking matrix.
    assert np.allclose(kblocking_matrix(K4, 2), nonbacktracking_matrix(K4))


def test_kblocking_empty_for_tree():
    """A tree has no cycle core, so the k-blocking matrices are empty."""
    from db.matrices import kblock3_matrix, kblock4_matrix
    P5 = nx.path_graph(5)
    assert kblock3_matrix(P5).size == 0
    assert kblock4_matrix(P5).size == 0


def test_kblocking_size_distinguishes_same_spectrum():
    """Two triangle cores with the same D_kB_k spectrum but different M_k size
    must hash differently (the size folds into the k-blocking hash)."""
    from math import comb
    from db.matrices import nonbacktracking_matrix, _build_directed_edges
    from db.spectrum import compute_complex_eigenvalues, spectral_hash_complex

    tri = nx.cycle_graph(3)
    B = nonbacktracking_matrix(tri)
    edges = _build_directed_edges(tri)
    # Both profiles have product of C(d-2,2) = 90 -> identical D_4 B_4 spectrum,
    # but different |states| = sum C(d-1,2): (5,5,7)->54, (4,6,8)->68.
    out = {}
    for deg in [{0: 5, 1: 5, 2: 7}, {0: 4, 1: 6, 2: 8}]:
        w = np.array([comb(deg[v] - 2, 2) for (_, v) in edges], dtype=float)
        eigs = compute_complex_eigenvalues(w[:, None] * B)
        size = sum(comb(deg[v] - 1, 2) for (_, v) in edges)
        out[tuple(sorted(deg.values()))] = (
            spectral_hash_complex(eigs),
            spectral_hash_complex(eigs, extra=f"|states={size}"),
        )
    a, b = out[(5, 5, 7)], out[(4, 6, 8)]
    assert a[0] == b[0]   # same D_kB_k spectrum
    assert a[1] != b[1]   # different once M_k size is folded in


def test_distance_laplacians_disconnected_none():
    """Distance-based matrices are None for disconnected graphs."""
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2])  # no edges
    assert distance_laplacian(G) is None
    assert distance_signless_laplacian(G) is None


def test_seidel_matrix_path():
    """Seidel S = J - I - 2A: 0 on diagonal, -1 if adjacent, +1 if not."""
    G = nx.path_graph(3)  # 0-1-2
    S = seidel_matrix(G)
    expected = np.array([
        [0.0, -1.0, 1.0],
        [-1.0, 0.0, -1.0],
        [1.0, -1.0, 0.0],
    ])
    assert np.array_equal(S, expected)
    # Symmetric, zero diagonal, entries in {-1, 0, 1}.
    assert np.array_equal(S, S.T)
    assert np.all(np.diag(S) == 0)
    assert set(np.unique(S)).issubset({-1.0, 0.0, 1.0})


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


def test_kirchhoff_laplacian_path():
    """Test Kirchhoff Laplacian (D - A) for P3."""
    G = nx.path_graph(3)
    L = kirchhoff_laplacian(G)

    # For P3: degrees are [1, 2, 1]
    # L = D - A
    expected = np.array(
        [
            [1, -1, 0],
            [-1, 2, -1],
            [0, -1, 1],
        ],
        dtype=np.float64,
    )

    np.testing.assert_array_equal(L, expected)


def test_kirchhoff_laplacian_properties():
    """Test Kirchhoff Laplacian properties."""
    G = nx.complete_graph(5)
    L = kirchhoff_laplacian(G)

    # Should be symmetric
    np.testing.assert_array_almost_equal(L, L.T)

    # Smallest eigenvalue should be 0 (always has 0 eigenvalue)
    eigs = np.linalg.eigvalsh(L)
    assert abs(eigs[0]) < 1e-10

    # Sum of each row should be 0
    row_sums = L.sum(axis=1)
    np.testing.assert_array_almost_equal(row_sums, np.zeros(5))


def test_signless_laplacian_path():
    """Test Signless Laplacian (D + A) for P3."""
    G = nx.path_graph(3)
    Q = signless_laplacian(G)

    # For P3: degrees are [1, 2, 1]
    # Q = D + A
    expected = np.array(
        [
            [1, 1, 0],
            [1, 2, 1],
            [0, 1, 1],
        ],
        dtype=np.float64,
    )

    np.testing.assert_array_equal(Q, expected)


def test_signless_laplacian_properties():
    """Test Signless Laplacian properties."""
    G = nx.complete_graph(5)
    Q = signless_laplacian(G)

    # Should be symmetric
    np.testing.assert_array_almost_equal(Q, Q.T)

    # All eigenvalues should be non-negative
    eigs = np.linalg.eigvalsh(Q)
    assert np.all(eigs >= -1e-10)

    # Largest eigenvalue should be at most 2*max_degree
    max_degree = max(dict(G.degree()).values())
    assert eigs[-1] <= 2 * max_degree + 1e-10


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


class TestNonbacktrackingCycleGraphs:
    """
    Tests for non-backtracking matrix eigenvalues on cycle graphs.

    For a cycle graph C_n, the NB matrix B is a permutation matrix because each
    directed edge has exactly one non-backtracking continuation. Therefore B^(2n) = I,
    and all eigenvalues are (2n)-th roots of unity with magnitude exactly 1.
    """

    def test_nb_eigenvalues_cycle_3(self):
        """C_3 (triangle): NB eigenvalues are 6th roots of unity."""
        G = nx.cycle_graph(3)
        B = nonbacktracking_matrix(G)
        eigs = np.linalg.eigvals(B)

        # All eigenvalues should have magnitude 1
        magnitudes = np.abs(eigs)
        np.testing.assert_allclose(magnitudes, 1.0, rtol=1e-10)

    def test_nb_eigenvalues_cycle_4(self):
        """C_4 (square): NB eigenvalues are 8th roots of unity."""
        G = nx.cycle_graph(4)
        B = nonbacktracking_matrix(G)
        eigs = np.linalg.eigvals(B)

        magnitudes = np.abs(eigs)
        np.testing.assert_allclose(magnitudes, 1.0, rtol=1e-10)

    def test_nb_eigenvalues_cycle_5(self):
        """C_5 (pentagon): NB eigenvalues are 10th roots of unity."""
        G = nx.cycle_graph(5)
        B = nonbacktracking_matrix(G)
        eigs = np.linalg.eigvals(B)

        magnitudes = np.abs(eigs)
        np.testing.assert_allclose(magnitudes, 1.0, rtol=1e-10)

    def test_nb_eigenvalues_cycle_6(self):
        """C_6 (hexagon): NB eigenvalues are 12th roots of unity."""
        G = nx.cycle_graph(6)
        B = nonbacktracking_matrix(G)
        eigs = np.linalg.eigvals(B)

        magnitudes = np.abs(eigs)
        np.testing.assert_allclose(magnitudes, 1.0, rtol=1e-10)

    def test_nb_eigenvalues_all_cycles(self):
        """NB eigenvalues of all cycle graphs C_3 to C_10 should be on unit circle."""
        for n in range(3, 11):
            G = nx.cycle_graph(n)
            B = nonbacktracking_matrix(G)
            eigs = np.linalg.eigvals(B)

            magnitudes = np.abs(eigs)
            np.testing.assert_allclose(
                magnitudes, 1.0, rtol=1e-10,
                err_msg=f"C_{n}: NB eigenvalues not on unit circle"
            )
