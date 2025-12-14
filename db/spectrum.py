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
    Compute ALL eigenvalues of a general (possibly non-symmetric) matrix.

    Returns all eigenvalues (including both members of conjugate pairs),
    rounded to specified precision and sorted by (real part, imaginary part).
    """
    if matrix.size == 0:
        return np.array([], dtype=np.complex128)

    eigs = eigvals(matrix)

    # Round to ensure consistent handling of near-zero values
    re = np.round(eigs.real, decimals=precision)
    im = np.round(eigs.imag, decimals=precision)
    re = np.where(re == 0, 0.0, re)
    im = np.where(im == 0, 0.0, im)
    eigs_rounded = re + 1j * im

    # Sort by real part, then imaginary part
    sort_keys = np.lexsort((eigs_rounded.imag, eigs_rounded.real))

    return eigs_rounded[sort_keys]


def _half_spectrum(eigenvalues: np.ndarray) -> np.ndarray:
    """
    Filter complex eigenvalues to one representative from each conjugate pair.

    Keeps eigenvalues with non-negative imaginary part. Used for hashing
    since conjugate pairs are redundant for cospectrality comparison.
    """
    if eigenvalues.size == 0:
        return eigenvalues
    return eigenvalues[eigenvalues.imag >= 0]


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

    Internally filters to one representative from each conjugate pair
    (keeping eigenvalues with non-negative imaginary part) before hashing,
    since conjugate pairs are redundant for cospectrality comparison.

    Args:
        eigenvalues: Array of complex eigenvalues (full spectrum)
        precision: Number of decimal places for formatting

    Returns:
        16-character hex hash
    """
    if eigenvalues.size == 0:
        return hashlib.sha256(b"empty").hexdigest()[:16]

    # Filter to half-spectrum for hashing (one from each conjugate pair)
    half = _half_spectrum(eigenvalues)

    canonical = ",".join(
        f"({r:.{precision}f},{i:.{precision}f})"
        for r, i in zip(half.real, half.imag)
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
