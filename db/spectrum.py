"""Spectrum computation and hashing."""

import hashlib
import numpy as np
from numpy.linalg import eigvalsh, eigvals


def compute_real_eigenvalues(matrix: np.ndarray) -> np.ndarray:
    """
    Compute eigenvalues of a symmetric real matrix.
    Returns sorted eigenvalues (ascending).
    """
    if matrix.size == 0:
        return np.array([], dtype=np.float64)
    eigs = eigvalsh(matrix)
    return np.sort(eigs)


def compute_complex_eigenvalues(matrix: np.ndarray) -> np.ndarray:
    """
    Compute eigenvalues of a general (possibly non-symmetric) matrix.
    Returns eigenvalues sorted by magnitude, then by phase.
    """
    if matrix.size == 0:
        return np.array([], dtype=np.complex128)

    eigs = eigvals(matrix)

    magnitudes = np.abs(eigs)
    phases = np.angle(eigs)
    sort_keys = np.lexsort((phases, magnitudes))

    return eigs[sort_keys]


def spectral_hash_real(eigenvalues: np.ndarray, precision: int = 8) -> str:
    """
    Compute a hash of real eigenvalues for co-spectral detection.

    Args:
        eigenvalues: Sorted array of real eigenvalues
        precision: Number of decimal places for rounding

    Returns:
        16-character hex hash
    """
    if eigenvalues.size == 0:
        return hashlib.sha256(b"empty").hexdigest()[:16]

    rounded = np.round(eigenvalues, decimals=precision)
    rounded = np.where(rounded == 0, 0.0, rounded)  # Handle -0.0

    canonical = ",".join(f"{x:.{precision}f}" for x in rounded)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def spectral_hash_complex(eigenvalues: np.ndarray, precision: int = 8) -> str:
    """
    Compute a hash of complex eigenvalues for co-spectral detection.

    Args:
        eigenvalues: Array of complex eigenvalues (sorted by magnitude, then phase)
        precision: Number of decimal places for rounding

    Returns:
        16-character hex hash
    """
    if eigenvalues.size == 0:
        return hashlib.sha256(b"empty").hexdigest()[:16]

    re = np.round(eigenvalues.real, decimals=precision)
    im = np.round(eigenvalues.imag, decimals=precision)
    re = np.where(re == 0, 0.0, re)
    im = np.where(im == 0, 0.0, im)

    canonical = ",".join(
        f"({r:.{precision}f},{i:.{precision}f})" for r, i in zip(re, im)
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
