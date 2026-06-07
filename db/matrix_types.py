"""Central registry of matrix types.

Single source of truth for which matrices SMOL computes spectra for, and their
properties (display name, builder function, real vs complex spectrum, whether
they are only defined for connected graphs, and the database column names).

Historically these facts were duplicated as string literals across the API and
the scripts. New matrix types should be added here and consumed from here.
"""

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import networkx as nx

from .matrices import (
    adjacency_matrix,
    kirchhoff_laplacian,
    signless_laplacian,
    laplacian_matrix,
    nonbacktracking_matrix,
    nonbacktracking_laplacian,
    distance_matrix,
    distance_laplacian,
    distance_signless_laplacian,
    seidel_matrix,
    kblock3_matrix,
    kblock4_matrix,
    kblock3_size,
    kblock4_size,
)


@dataclass(frozen=True)
class MatrixType:
    key: str
    name: str
    builder: Callable[[nx.Graph], Optional[np.ndarray]]
    is_complex: bool
    connected_only: bool = False
    # When True, an empty or all-zero spectrum is stored as NULL (not hashed),
    # so such graphs are not grouped together as cospectral.
    null_if_trivial: bool = False
    # Optional invariant beyond the stored spectrum, folded into the hash. The
    # k-blocking operators use this for M_k's size |states(M_k)|, since two
    # graphs can share the D_k B_k spectrum but differ in M_k's kernel.
    size_fn: Optional[Callable[[nx.Graph], int]] = None

    @property
    def eigenvalue_columns(self) -> tuple[str, ...]:
        """Database column(s) holding the eigenvalues for this matrix type.

        Complex spectra are split into real and imaginary parts; real spectra
        use a single column.
        """
        if self.is_complex:
            return (f"{self.key}_eigenvalues_re", f"{self.key}_eigenvalues_im")
        return (f"{self.key}_eigenvalues",)

    @property
    def hash_column(self) -> str:
        return f"{self.key}_spectral_hash"


# Order here is the canonical display/API order.
MATRIX_TYPES: dict[str, MatrixType] = {
    m.key: m
    for m in (
        MatrixType("adj", "Adjacency", adjacency_matrix, is_complex=False),
        MatrixType("kirchhoff", "Kirchhoff Laplacian", kirchhoff_laplacian, is_complex=False),
        MatrixType("signless", "Signless Laplacian", signless_laplacian, is_complex=False),
        MatrixType("lap", "Normalized Laplacian", laplacian_matrix, is_complex=False),
        MatrixType("nb", "Non-backtracking", nonbacktracking_matrix, is_complex=True),
        MatrixType("nbl", "Non-backtracking Laplacian", nonbacktracking_laplacian, is_complex=True),
        MatrixType("dist", "Distance", distance_matrix, is_complex=False, connected_only=True),
        MatrixType("distlap", "Distance Laplacian", distance_laplacian, is_complex=False, connected_only=True),
        MatrixType("distsign", "Distance Signless Laplacian", distance_signless_laplacian, is_complex=False, connected_only=True),
        MatrixType("seidel", "Seidel", seidel_matrix, is_complex=False),
        MatrixType("kblock3", "3-blocking operator", kblock3_matrix, is_complex=True, null_if_trivial=True, size_fn=kblock3_size),
        MatrixType("kblock4", "4-blocking operator", kblock4_matrix, is_complex=True, null_if_trivial=True, size_fn=kblock4_size),
    )
}

# Ordered tuple of all matrix-type keys.
MATRIX_KEYS: tuple[str, ...] = tuple(MATRIX_TYPES)


def real_keys() -> tuple[str, ...]:
    """Keys of matrix types with a real spectrum, in canonical order."""
    return tuple(k for k, m in MATRIX_TYPES.items() if not m.is_complex)


def complex_keys() -> tuple[str, ...]:
    """Keys of matrix types with a complex spectrum, in canonical order."""
    return tuple(k for k, m in MATRIX_TYPES.items() if m.is_complex)


def is_valid(key: str) -> bool:
    return key in MATRIX_TYPES
