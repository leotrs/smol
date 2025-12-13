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


def compute_complex_eigenvalues(matrix: np.ndarray, precision: int = 6) -> np.ndarray:
    """
    Compute eigenvalues of a general (possibly non-symmetric) matrix.

    For real matrices, eigenvalues come in conjugate pairs. We round first,
    then keep only eigenvalues with non-negative imaginary part (one from
    each conjugate pair), then sort by (real part, imaginary part).
    """
    if matrix.size == 0:
        return np.array([], dtype=np.complex128)

    eigs = eigvals(matrix)

    # Round first to ensure consistent handling of near-zero values
    re = np.round(eigs.real, decimals=precision)
    im = np.round(eigs.imag, decimals=precision)
    re = np.where(re == 0, 0.0, re)
    im = np.where(im == 0, 0.0, im)
    eigs_rounded = re + 1j * im

    # Keep only eigenvalues with non-negative imaginary part
    # (one representative from each conjugate pair)
    eigs_half = eigs_rounded[im >= 0]

    # Sort by real part, then imaginary part
    sort_keys = np.lexsort((eigs_half.imag, eigs_half.real))

    return eigs_half[sort_keys]


def spectral_hash_real(eigenvalues: np.ndarray, precision: int = 6) -> str:
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


def spectral_hash_complex(eigenvalues: np.ndarray, precision: int = 6) -> str:
    """
    Compute a hash of complex eigenvalues for co-spectral detection.

    Args:
        eigenvalues: Array of complex eigenvalues (already rounded and filtered
                     to non-negative imaginary part by compute_complex_eigenvalues)
        precision: Number of decimal places for formatting

    Returns:
        16-character hex hash
    """
    if eigenvalues.size == 0:
        return hashlib.sha256(b"empty").hexdigest()[:16]

    canonical = ",".join(
        f"({r:.{precision}f},{i:.{precision}f})"
        for r, i in zip(eigenvalues.real, eigenvalues.imag)
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
