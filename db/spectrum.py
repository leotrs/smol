"""Spectrum computation and hashing."""

import hashlib
import numpy as np
from numpy.linalg import eigvalsh, eigvals

PRECISION = 8


# ---------------------------------------------------------------------------
# Exact characteristic polynomial via Bareiss algorithm
# ---------------------------------------------------------------------------


def _poly_mul(a, b):
    if not a or not b:
        return [0]
    la, lb = len(a), len(b)
    result = [0] * (la + lb - 1)
    for i in range(la):
        if a[i] == 0:
            continue
        for j in range(lb):
            result[i + j] += a[i] * b[j]
    return result


def _poly_sub(a, b):
    result = [0] * max(len(a), len(b))
    for i in range(len(a)):
        result[i] += a[i]
    for i in range(len(b)):
        result[i] -= b[i]
    return result


def _poly_divexact(a, b):
    if all(c == 0 for c in b):
        return [0]
    db = len(b) - 1
    while db > 0 and b[db] == 0:
        db -= 1
    da = len(a) - 1
    while da > 0 and a[da] == 0:
        da -= 1
    if da < db:
        return [0]
    a = list(a)
    result = [0] * (da - db + 1)
    for i in range(da - db, -1, -1):
        q, r = divmod(a[i + db], b[db])
        assert r == 0, f"Bareiss division not exact: {a[i + db]} / {b[db]}"
        result[i] = q
        for j in range(db + 1):
            a[i + j] -= q * b[j]
    return result


def bareiss_poly_det(M_polys, n):
    """Determinant of an n×n matrix of integer polynomials via Bareiss."""
    M = [[list(M_polys[i][j]) for j in range(n)] for i in range(n)]
    prev = [1]
    for k in range(n):
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                num = _poly_sub(
                    _poly_mul(M[k][k], M[i][j]),
                    _poly_mul(M[i][k], M[k][j]),
                )
                M[i][j] = _poly_divexact(num, prev)
            M[i][k] = [0]
        prev = list(M[k][k])
    result = M[n - 1][n - 1]
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result


def nb_charpoly(adjacency: np.ndarray) -> list[int]:
    """Compute the exact NB characteristic polynomial det(M(z)).

    M(z) = I - zA + z²(D - I), where A is the adjacency matrix and D the
    degree matrix. Returns integer coefficients [c₀, c₁, ..., c_{2n}] of
    det(M(z)) = c₀ + c₁z + ... + c_{2n}z^{2n}.

    Uses Bareiss algorithm — exact integer arithmetic, no floating point.
    """
    n = adjacency.shape[0]
    A = adjacency.astype(int)
    degs = A.sum(axis=1)
    M_polys = [[None] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                M_polys[i][j] = [1, -int(A[i, j]), int(degs[i]) - 1]
            else:
                M_polys[i][j] = [0, -int(A[i, j]), 0]
    return bareiss_poly_det(M_polys, n)


def charpoly_hash(coeffs) -> str:
    """Hash a characteristic polynomial (list of integer coefficients).

    Returns 16-character hex hash. Deterministic for identical polynomials.
    """
    canonical = ",".join(str(c) for c in coeffs)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


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
