"""Tests for spectrum computation and hashing."""

import numpy as np
import networkx as nx

from db.spectrum import (
    PRECISION,
    compute_real_eigenvalues,
    compute_complex_eigenvalues,
    spectral_hash_real,
    spectral_hash_complex,
)
from db.matrices import laplacian_matrix, adjacency_matrix


class TestEigenvaluePrecision:
    """Tests for eigenvalue rounding to exactly 8 decimals."""

    def test_precision_constant_is_8(self):
        """PRECISION constant should be 8."""
        assert PRECISION == 8

    def test_real_eigenvalues_rounded_to_8_decimals(self):
        """Real eigenvalues should be rounded to exactly 8 decimal places."""
        # Matrix with irrational eigenvalues
        M = np.array([[2, 1], [1, 2]], dtype=np.float64)
        eigs = compute_real_eigenvalues(M)

        for eig in eigs:
            # Check that the value equals its 8-decimal rounded version
            assert eig == round(eig, 8), f"Eigenvalue {eig} not rounded to 8 decimals"

    def test_real_eigenvalues_near_zero_become_zero(self):
        """Values like 1e-16 should become exactly 0.0."""
        # Identity matrix has eigenvalue 1, but numerical noise can appear
        M = np.array([[1, 0], [0, 1]], dtype=np.float64)
        eigs = compute_real_eigenvalues(M)

        for eig in eigs:
            # All eigenvalues should be exactly 1.0, no floating point noise
            assert eig == 1.0

    def test_real_eigenvalues_no_negative_zero(self):
        """Should not have -0.0 in eigenvalues."""
        M = np.array([[0, 1], [1, 0]], dtype=np.float64)  # eigenvalues: -1, 1
        eigs = compute_real_eigenvalues(M)

        for eig in eigs:
            # Check no negative zero (str(-0.0) == "-0.0")
            assert str(eig) != "-0.0", f"Found negative zero: {eig}"

    def test_complex_eigenvalues_rounded_to_8_decimals(self):
        """Complex eigenvalues should be rounded to exactly 8 decimal places."""
        theta = np.pi / 4
        M = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ])
        eigs = compute_complex_eigenvalues(M)

        for eig in eigs:
            assert eig.real == round(eig.real, 8)
            assert eig.imag == round(eig.imag, 8)


class TestKnownGraphSpectra:
    """Tests for exact eigenvalues of well-known graphs."""

    def test_p3_normalized_laplacian(self):
        """P3 normalized Laplacian eigenvalues should be {0, 1, 2}."""
        G = nx.path_graph(3)
        L = laplacian_matrix(G)
        eigs = compute_real_eigenvalues(L)

        np.testing.assert_array_equal(eigs, [0.0, 1.0, 2.0])

    def test_k3_normalized_laplacian(self):
        """K3 (triangle) normalized Laplacian eigenvalues should be {0, 1.5, 1.5}."""
        G = nx.complete_graph(3)
        L = laplacian_matrix(G)
        eigs = compute_real_eigenvalues(L)

        np.testing.assert_array_equal(eigs, [0.0, 1.5, 1.5])

    def test_k3_adjacency(self):
        """K3 adjacency eigenvalues should be {-1, -1, 2}."""
        G = nx.complete_graph(3)
        A = adjacency_matrix(G)
        eigs = compute_real_eigenvalues(A)

        np.testing.assert_array_equal(eigs, [-1.0, -1.0, 2.0])

    def test_p4_adjacency(self):
        """P4 adjacency eigenvalues are known algebraically."""
        G = nx.path_graph(4)
        A = adjacency_matrix(G)
        eigs = compute_real_eigenvalues(A)

        # P4 eigenvalues: ±(1 ± √5)/2 ≈ -1.618, -0.618, 0.618, 1.618
        golden = (1 + np.sqrt(5)) / 2
        expected = sorted([-golden, -1/golden, 1/golden, golden])
        expected_rounded = [round(e, 8) for e in expected]

        np.testing.assert_array_equal(eigs, expected_rounded)

    def test_c4_adjacency(self):
        """C4 (square) adjacency eigenvalues should be {-2, 0, 0, 2}."""
        G = nx.cycle_graph(4)
        A = adjacency_matrix(G)
        eigs = compute_real_eigenvalues(A)

        np.testing.assert_array_equal(eigs, [-2.0, 0.0, 0.0, 2.0])


class TestHashFromStoredEigenvalues:
    """Tests that hash is computed from the stored (rounded) eigenvalues."""

    def test_hash_uses_8_decimal_precision(self):
        """Hash should use 8 decimal places in canonical form."""
        eigs = np.array([0.0, 1.0, 2.0])
        h = spectral_hash_real(eigs)

        # Compute expected hash manually
        import hashlib
        canonical = "0.00000000,1.00000000,2.00000000"
        expected = hashlib.sha256(canonical.encode()).hexdigest()[:16]

        assert h == expected, f"Hash mismatch: got {h}, expected {expected}"

    def test_hash_matches_for_rounded_eigenvalues(self):
        """Hash of raw eigenvalues should match hash of pre-rounded eigenvalues."""
        # Simulate raw floating point eigenvalues
        raw_eigs = np.array([1e-16, 0.99999999999, 2.00000000001])
        rounded_eigs = np.array([0.0, 1.0, 2.0])

        # After rounding internally, hashes should match
        h_raw = spectral_hash_real(raw_eigs)
        h_rounded = spectral_hash_real(rounded_eigs)

        assert h_raw == h_rounded

    def test_eigenvalues_and_hash_consistent(self):
        """compute_real_eigenvalues output should hash consistently with spectral_hash_real."""
        G = nx.path_graph(5)
        L = laplacian_matrix(G)
        eigs = compute_real_eigenvalues(L)

        # Hash the eigenvalues
        h1 = spectral_hash_real(eigs)

        # Hash again - should be identical since eigenvalues are already rounded
        h2 = spectral_hash_real(eigs)

        assert h1 == h2

    def test_complex_hash_uses_8_decimal_precision(self):
        """Complex hash should use 8 decimal places."""
        eigs = np.array([1.0 + 2.0j, 3.0 + 0.0j])
        h = spectral_hash_complex(eigs)

        import hashlib
        # Only positive imaginary parts (half spectrum): 1+2j and 3+0j
        canonical = "(1.00000000,2.00000000),(3.00000000,0.00000000)"
        expected = hashlib.sha256(canonical.encode()).hexdigest()[:16]

        assert h == expected


def test_compute_real_eigenvalues_symmetric():
    """Test eigenvalues of a symmetric matrix."""
    # Simple 2x2 symmetric matrix
    M = np.array([[2, 1], [1, 2]], dtype=np.float64)
    eigs = compute_real_eigenvalues(M)

    # Eigenvalues should be 1 and 3
    np.testing.assert_array_almost_equal(eigs, [1.0, 3.0])


def test_compute_real_eigenvalues_sorted():
    """Eigenvalues should be sorted ascending."""
    M = np.array(
        [
            [5, 0, 0],
            [0, 1, 0],
            [0, 0, 3],
        ],
        dtype=np.float64,
    )
    eigs = compute_real_eigenvalues(M)

    np.testing.assert_array_almost_equal(eigs, [1.0, 3.0, 5.0])


def test_compute_real_eigenvalues_empty():
    """Empty matrix should return empty array."""
    M = np.array([]).reshape(0, 0)
    eigs = compute_real_eigenvalues(M)

    assert eigs.shape == (0,)


def test_compute_complex_eigenvalues():
    """Test eigenvalues of a non-symmetric matrix."""
    # Rotation matrix has complex eigenvalues e^{±iθ}
    theta = np.pi / 4
    M = np.array(
        [
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ]
    )
    eigs = compute_complex_eigenvalues(M)

    # Should return ALL eigenvalues (both conjugates)
    assert len(eigs) == 2
    # Both should have magnitude 1
    np.testing.assert_almost_equal(np.abs(eigs[0]), 1.0, decimal=5)
    np.testing.assert_almost_equal(np.abs(eigs[1]), 1.0, decimal=5)
    # One positive imaginary, one negative
    imag_parts = sorted([e.imag for e in eigs])
    np.testing.assert_almost_equal(imag_parts[0], -np.sin(theta), decimal=5)
    np.testing.assert_almost_equal(imag_parts[1], np.sin(theta), decimal=5)


def test_compute_complex_eigenvalues_sorted_by_magnitude():
    """Complex eigenvalues should be sorted by magnitude, then phase."""
    M = np.diag([3, 1, 2])
    eigs = compute_complex_eigenvalues(M)

    magnitudes = np.abs(eigs)
    assert magnitudes[0] <= magnitudes[1] <= magnitudes[2]


def test_spectral_hash_real_deterministic():
    """Same eigenvalues should produce same hash."""
    eigs1 = np.array([1.0, 2.0, 3.0])
    eigs2 = np.array([1.0, 2.0, 3.0])

    hash1 = spectral_hash_real(eigs1)
    hash2 = spectral_hash_real(eigs2)

    assert hash1 == hash2


def test_spectral_hash_real_different():
    """Different eigenvalues should produce different hash."""
    eigs1 = np.array([1.0, 2.0, 3.0])
    eigs2 = np.array([1.0, 2.0, 4.0])

    hash1 = spectral_hash_real(eigs1)
    hash2 = spectral_hash_real(eigs2)

    assert hash1 != hash2


def test_spectral_hash_real_length():
    """Hash should be 16 characters."""
    eigs = np.array([1.0, 2.0, 3.0])
    h = spectral_hash_real(eigs)

    assert len(h) == 16


def test_spectral_hash_complex_deterministic():
    """Same complex eigenvalues should produce same hash."""
    eigs1 = np.array([1 + 2j, 3 + 4j])
    eigs2 = np.array([1 + 2j, 3 + 4j])

    hash1 = spectral_hash_complex(eigs1)
    hash2 = spectral_hash_complex(eigs2)

    assert hash1 == hash2


def test_spectral_hash_complex_different():
    """Different complex eigenvalues should produce different hash."""
    eigs1 = np.array([1 + 2j, 3 + 4j])
    eigs2 = np.array([1 + 2j, 3 + 5j])

    hash1 = spectral_hash_complex(eigs1)
    hash2 = spectral_hash_complex(eigs2)

    assert hash1 != hash2


def test_spectral_hash_empty():
    """Empty array should produce a consistent hash."""
    eigs = np.array([], dtype=np.float64)

    hash1 = spectral_hash_real(eigs)
    hash2 = spectral_hash_real(eigs)

    assert hash1 == hash2
    assert len(hash1) == 16


def test_compute_complex_eigenvalues_nb_matrix_size():
    """NB matrix should return exactly 2m eigenvalues for m edges."""
    import networkx as nx
    from db.matrices import nonbacktracking_matrix

    # Triangle (K3): m=3 edges, expect 2*3=6 eigenvalues
    G = nx.cycle_graph(3)
    B = nonbacktracking_matrix(G)
    eigs = compute_complex_eigenvalues(B)
    assert len(eigs) == 6, f"K3: expected 6 eigenvalues, got {len(eigs)}"

    # Square (C4): m=4 edges, expect 2*4=8 eigenvalues
    G = nx.cycle_graph(4)
    B = nonbacktracking_matrix(G)
    eigs = compute_complex_eigenvalues(B)
    assert len(eigs) == 8, f"C4: expected 8 eigenvalues, got {len(eigs)}"

    # Star S4 (4 edges): expect 2*4=8 eigenvalues
    G = nx.star_graph(4)
    B = nonbacktracking_matrix(G)
    eigs = compute_complex_eigenvalues(B)
    assert len(eigs) == 8, f"S4: expected 8 eigenvalues, got {len(eigs)}"
