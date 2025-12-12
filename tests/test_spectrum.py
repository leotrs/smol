"""Tests for spectrum computation and hashing."""

import numpy as np

from db.spectrum import (
    compute_real_eigenvalues,
    compute_complex_eigenvalues,
    spectral_hash_real,
    spectral_hash_complex,
)


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
    # Rotation matrix has complex eigenvalues
    theta = np.pi / 4
    M = np.array(
        [
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ]
    )
    eigs = compute_complex_eigenvalues(M)

    # Should have eigenvalues e^{±iθ}
    assert len(eigs) == 2
    np.testing.assert_almost_equal(np.abs(eigs[0]), 1.0)
    np.testing.assert_almost_equal(np.abs(eigs[1]), 1.0)


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


def test_spectral_hash_real_handles_negative_zero():
    """Hash should treat -0.0 and 0.0 the same."""
    eigs1 = np.array([-0.0, 1.0, 2.0])
    eigs2 = np.array([0.0, 1.0, 2.0])

    hash1 = spectral_hash_real(eigs1)
    hash2 = spectral_hash_real(eigs2)

    assert hash1 == hash2


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
