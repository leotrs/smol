"""Exact hashes for non3cyc, non4cyc and kblock_family (db/charpoly.py).

The reduced determinants are checked against the determinant of the full matrix mod p,
and the hashes against pairs that are known to be cospectral."""

import networkx as nx
import numpy as np
import pytest

from db import charpoly as cp
from db.matrices import cycle_core, kblocking_matrix, non3cyc_matrix, non4cyc_matrix

ATLAS = [G for G in nx.graph_atlas_g()[1:] if G.number_of_nodes() <= 6]


def full_charval(M, x, p):
    """det(xI - M) mod p computed on the full integer matrix."""
    n = M.shape[0]
    if n == 0:
        return 1
    A = (x * np.eye(n, dtype=np.int64) - np.rint(M).astype(np.int64)) % p
    return cp._det_mod(A, p)


@pytest.mark.parametrize("k,builder", [(3, non3cyc_matrix), (4, non4cyc_matrix)])
def test_noncyc_reduction_matches_full_determinant(k, builder):
    for G in ATLAS:
        M = builder(G)
        for x, p in ((cp._X1, cp._P1), (cp._X2, cp._P2)):
            val, N = cp._noncyc_charvals(G, k, x, p)
            assert N == M.shape[0]
            assert val == full_charval(M, x, p)


def test_kblock_reduction_matches_full_determinant():
    from math import comb
    for G in ATLAS:
        k = 2
        while cycle_core(G, k).number_of_edges() > 0:
            Hk = cycle_core(G, k)
            z = {v: comb(G.degree(v) - 2, k - 2) for v in Hk}
            M = kblocking_matrix(G, k)
            for x, p in ((cp._X1, cp._P1), (cp._X2, cp._P2)):
                assert cp._zb_charval(Hk, z, x, p) == full_charval(M, x, p)
            k += 1


@pytest.mark.parametrize("key,a,b", [
    ("non3cyc", "EEhW", "EEio"),
    ("non3cyc", "ECvo", "EEro"),
    ("kblock_family", "H?`DUVF", "HCOedfJ"),
    ("kblock_family", "H?B@eNb", "H?b@dqr"),
])
def test_known_cospectral_pairs_share_a_hash(key, a, b):
    Ga, Gb = (nx.from_graph6_bytes(g.encode()) for g in (a, b))
    assert not nx.is_isomorphic(Ga, Gb)
    assert cp.exact_spectral_hash(key, Ga) == cp.exact_spectral_hash(key, Gb) is not None


def test_trivial_spectra_have_no_hash():
    tree = nx.path_graph(6)
    assert cp.exact_spectral_hash("non3cyc", tree) is None
    assert cp.exact_spectral_hash("non4cyc", nx.cycle_graph(4)) is None
    assert cp.exact_spectral_hash("kblock_family", tree) is None
