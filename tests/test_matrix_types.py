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
    signature_keys,
    is_valid,
)


def test_canonical_keys_and_order():
    assert MATRIX_KEYS == (
        "adj", "kirchhoff", "signless", "lap", "nb", "nbl",
        "dist", "distlap", "distsign", "kblock_family",
        "yoon2", "yoon3", "non3cyc", "non4cyc",
    )


def test_real_vs_complex_partition():
    assert real_keys() == (
        "adj", "kirchhoff", "signless", "lap", "dist", "distlap", "distsign",
        "yoon2", "yoon3",
    )
    assert complex_keys() == ("nb", "nbl", "non3cyc", "non4cyc")
    # The k-blocking family is a composite, hash-only signature: neither a
    # real- nor complex-eigenvalue matrix.
    assert signature_keys() == ("kblock_family",)
    # Real / complex / signature partition the keys exhaustively and disjointly.
    assert set(real_keys()) | set(complex_keys()) | set(signature_keys()) == set(MATRIX_KEYS)
    assert set(real_keys()) & set(complex_keys()) == set()
    assert set(signature_keys()) & (set(real_keys()) | set(complex_keys())) == set()


def test_kblock_family_is_signature_only():
    mt = MATRIX_TYPES["kblock_family"]
    assert mt.signature_fn is not None
    assert mt.eigenvalue_columns == ()
    assert mt.hash_column == "kblock_family_spectral_hash"
    # The replaced standalone blocking matrices are gone from the registry.
    assert "kblock3" not in MATRIX_KEYS
    assert "kblock4" not in MATRIX_KEYS


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


def test_hash_only_keys():
    """The large-spectrum matrices are hash-only: complex and null_if_trivial."""
    from db.matrix_types import HASH_ONLY_KEYS
    assert HASH_ONLY_KEYS == ("non3cyc", "non4cyc")
    for k in HASH_ONLY_KEYS:
        assert MATRIX_TYPES[k].is_complex
        assert MATRIX_TYPES[k].null_if_trivial


def test_export_nulls_only_hash_only_array_columns():
    """The SQLite export blanks exactly the array columns of the hash-only
    matrices (keeping their hash columns and all small-matrix arrays)."""
    from scripts.export_to_sqlite import NULLED_COLUMNS
    from db.matrix_types import HASH_ONLY_KEYS
    expected = {
        f"{k}_eigenvalues_re" for k in HASH_ONLY_KEYS
    } | {f"{k}_eigenvalues_im" for k in HASH_ONLY_KEYS}
    assert set(NULLED_COLUMNS) == expected
    # Hash columns and small-matrix arrays are never nulled.
    assert not any(c.endswith("_spectral_hash") for c in NULLED_COLUMNS)
    assert "adj_eigenvalues" not in NULLED_COLUMNS
    assert "nb_eigenvalues_re" not in NULLED_COLUMNS


def test_builders_callable_on_path_graph():
    P3 = nx.path_graph(3)
    for key, m in MATRIX_TYPES.items():
        if m.signature_fn is not None:
            # Signature-only types have no single-matrix builder; they produce a
            # composite hash directly.
            assert m.builder is None, key
            assert m.signature_fn(P3) is None  # P3 is a forest -> trivial family
            continue
        result = m.builder(P3)
        # Some matrices are conditionally defined (e.g. yoon3 needs n > 3),
        # in which case the builder returns None.
        assert result is None or isinstance(result, np.ndarray), key


def test_adjacency_builder_matches_networkx():
    P3 = nx.path_graph(3)
    expected = nx.to_numpy_array(P3, dtype=np.float64)
    assert np.array_equal(MATRIX_TYPES["adj"].builder(P3), expected)
