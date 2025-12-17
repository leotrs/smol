"""Spectrum computation and hashing."""

import hashlib
import numpy as np
from numpy.linalg import eigvalsh, eigvals

PRECISION = 8


def compute_real_eigenvalues(matrix: np.ndarray) -> np.ndarray:
    """
    Compute eigenvalues of a symmetric real matrix.
    Returns sorted eigenvalues (ascending), rounded to PRECISION decimals.
    """
    if matrix.size == 0:
        return np.array([], dtype=np.float64)
    eigs = eigvalsh(matrix)
    eigs = np.sort(eigs)
    eigs = np.round(eigs, decimals=PRECISION)
    eigs = np.where(eigs == 0, 0.0, eigs)  # Handle -0.0
    return eigs


def compute_complex_eigenvalues(matrix: np.ndarray) -> np.ndarray:
    """
    Compute ALL eigenvalues of a general (possibly non-symmetric) matrix.

    Returns all eigenvalues (including both members of conjugate pairs),
    rounded to PRECISION decimals and sorted by (real part, imaginary part).
    """
    if matrix.size == 0:
        return np.array([], dtype=np.complex128)

    eigs = eigvals(matrix)

    # Round to ensure consistent handling of near-zero values
    re = np.round(eigs.real, decimals=PRECISION)
    im = np.round(eigs.imag, decimals=PRECISION)
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


def spectral_hash_real(eigenvalues: np.ndarray) -> str:
    """
    Compute a hash of real eigenvalues for co-spectral detection.

    Eigenvalues should already be rounded to PRECISION decimals by
    compute_real_eigenvalues, with no -0.0 values.

    Args:
        eigenvalues: Sorted array of real eigenvalues (pre-rounded, no -0.0)

    Returns:
        16-character hex hash
    """
    if eigenvalues.size == 0:
        return hashlib.sha256(b"empty").hexdigest()[:16]

    canonical = ",".join(f"{x:.{PRECISION}f}" for x in eigenvalues)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def spectral_hash_complex(eigenvalues: np.ndarray) -> str:
    """
    Compute a hash of complex eigenvalues for co-spectral detection.

    Internally filters to one representative from each conjugate pair
    (keeping eigenvalues with non-negative imaginary part) before hashing,
    since conjugate pairs are redundant for cospectrality comparison.

    Eigenvalues should already be rounded to PRECISION decimals by
    compute_complex_eigenvalues.

    Args:
        eigenvalues: Array of complex eigenvalues (full spectrum, pre-rounded)

    Returns:
        16-character hex hash
    """
    if eigenvalues.size == 0:
        return hashlib.sha256(b"empty").hexdigest()[:16]

    # Filter to half-spectrum for hashing (one from each conjugate pair)
    half = _half_spectrum(eigenvalues)

    canonical = ",".join(
        f"({r:.{PRECISION}f},{i:.{PRECISION}f})"
        for r, i in zip(half.real, half.imag)
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
