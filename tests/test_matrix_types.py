"""Tests for the matrix-type registry.

These pin the exact set/order/classification of matrix types so the migration
of the previously-hardcoded string lists is provably behavior-preserving.
"""

import numpy as np
import networkx as nx

from db.matrix_types import (
    MATRIX_TYPES,
    MATRIX_KEYS,
    real_keys,
    complex_keys,
    is_valid,
)


def test_canonical_keys_and_order():
    assert MATRIX_KEYS == (
        "adj", "kirchhoff", "signless", "lap", "nb", "nbl",
        "dist", "distlap", "distsign", "seidel", "kblock3", "kblock4",
        "yoon2", "yoon3", "non3cyc", "non4cyc",
    )


def test_real_vs_complex_partition():
    assert real_keys() == (
        "adj", "kirchhoff", "signless", "lap", "dist", "distlap", "distsign",
        "seidel", "yoon2", "yoon3",
    )
    assert complex_keys() == ("nb", "nbl", "kblock3", "kblock4", "non3cyc", "non4cyc")
    # Partition is exhaustive and disjoint.
    assert set(real_keys()) | set(complex_keys()) == set(MATRIX_KEYS)
    assert set(real_keys()) & set(complex_keys()) == set()


def test_connected_only_flag():
    connected_only = {"dist", "distlap", "distsign"}
    assert all(MATRIX_TYPES[k].connected_only for k in connected_only)
    assert all(
        not m.connected_only
        for k, m in MATRIX_TYPES.items()
        if k not in connected_only
    )


def test_column_names():
    assert MATRIX_TYPES["adj"].eigenvalue_columns == ("adj_eigenvalues",)
    assert MATRIX_TYPES["adj"].hash_column == "adj_spectral_hash"
    assert MATRIX_TYPES["nb"].eigenvalue_columns == (
        "nb_eigenvalues_re",
        "nb_eigenvalues_im",
    )
    assert MATRIX_TYPES["nb"].hash_column == "nb_spectral_hash"


def test_is_valid():
    assert is_valid("adj")
    assert not is_valid("bogus")


def test_builders_callable_on_path_graph():
    P3 = nx.path_graph(3)
    for key, m in MATRIX_TYPES.items():
        result = m.builder(P3)
        # Some matrices are conditionally defined (e.g. yoon3 needs n > 3),
        # in which case the builder returns None.
        assert result is None or isinstance(result, np.ndarray), key


def test_adjacency_builder_matches_networkx():
    P3 = nx.path_graph(3)
    expected = nx.to_numpy_array(P3, dtype=np.float64)
    assert np.array_equal(MATRIX_TYPES["adj"].builder(P3), expected)
