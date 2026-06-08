"""Graph data processing - combines all computations for a single graph."""

import os
from dataclasses import dataclass, fields, replace
import numpy as np
import networkx as nx

# When set, process_graph skips the k-blocking and non-cycling matrices, whose
# per-graph cost dwarfs everything else (~1000x). Used to generate n=10 (12M
# graphs) for the cheap matrices in hours rather than weeks; the expensive
# matrices can be backfilled separately later.
SKIP_EXPENSIVE = os.environ.get("SMOL_SKIP_EXPENSIVE") == "1"

# When set, store only the spectral hashes (+ metadata), not the eigenvalue
# arrays. The hash is all cospectrality needs; this makes generation
# compute-bound instead of insert-bound (~20x faster at n=10) and keeps the
# database small. Used for n=10, which is local-only and never browsed
# graph-by-graph at 12M scale.
HASH_ONLY = os.environ.get("SMOL_HASH_ONLY") == "1"

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
    yoon2_matrix,
    yoon3_matrix,
    non3cyc_matrix,
    non4cyc_matrix,
)
from .spectrum import (
    compute_real_eigenvalues,
    compute_complex_eigenvalues,
    spectral_hash_real,
    spectral_hash_complex,
)
from .metadata import compute_metadata


def _real_spectrum_or_none(M):
    """Real eigenvalues and hash, or (None, None) when the matrix is None
    (e.g. a Yoon m-Laplacian on a graph with n <= m)."""
    if M is None:
        return None, None
    eigs = compute_real_eigenvalues(M)
    return eigs, spectral_hash_real(eigs)


def _complex_spectrum_or_none(M, size=None):
    """Complex eigenvalues (real, imag) and hash for a matrix.

    Returns (None, None, None) when the spectrum is empty or all-zero, so the
    graph is stored with a NULL hash and not grouped as cospectral. ``size``,
    when given, is folded into the hash as an exact-integer tag (used for the
    k-blocking operator's |states(M_k)|).
    """
    eigs = compute_complex_eigenvalues(M)
    if eigs.size == 0 or np.allclose(eigs, 0.0):
        return None, None, None
    extra = "" if size is None else f"|states={size}"
    return eigs.real, eigs.imag, spectral_hash_complex(eigs, extra=extra)


# Canonical column order for inserting a GraphRecord. to_db_tuple() emits values
# in exactly this order; consumers (e.g. scripts/generate.py) build their INSERT
# column list from here so the two cannot drift apart.
INSERT_COLUMNS = (
    "n", "m", "graph6",
    "adj_eigenvalues", "adj_spectral_hash",
    "kirchhoff_eigenvalues", "kirchhoff_spectral_hash",
    "signless_eigenvalues", "signless_spectral_hash",
    "lap_eigenvalues", "lap_spectral_hash",
    "nb_eigenvalues_re", "nb_eigenvalues_im", "nb_spectral_hash",
    "nbl_eigenvalues_re", "nbl_eigenvalues_im", "nbl_spectral_hash",
    "dist_eigenvalues", "dist_spectral_hash",
    "distlap_eigenvalues", "distlap_spectral_hash",
    "distsign_eigenvalues", "distsign_spectral_hash",
    "seidel_eigenvalues", "seidel_spectral_hash",
    "kblock3_eigenvalues_re", "kblock3_eigenvalues_im", "kblock3_spectral_hash",
    "kblock4_eigenvalues_re", "kblock4_eigenvalues_im", "kblock4_spectral_hash",
    "yoon2_eigenvalues", "yoon2_spectral_hash",
    "yoon3_eigenvalues", "yoon3_spectral_hash",
    "non3cyc_eigenvalues_re", "non3cyc_eigenvalues_im", "non3cyc_spectral_hash",
    "non4cyc_eigenvalues_re", "non4cyc_eigenvalues_im", "non4cyc_spectral_hash",
    "is_bipartite", "is_planar", "is_regular",
    "diameter", "girth", "radius",
    "min_degree", "max_degree", "triangle_count",
)


@dataclass
class GraphRecord:
    """Complete record for a graph ready for database insertion."""

    graph6: str
    n: int
    m: int

    # Adjacency spectrum
    adj_eigenvalues: np.ndarray
    adj_spectral_hash: str

    # Kirchhoff Laplacian spectrum
    kirchhoff_eigenvalues: np.ndarray
    kirchhoff_spectral_hash: str

    # Signless Laplacian spectrum
    signless_eigenvalues: np.ndarray
    signless_spectral_hash: str

    # Normalized Laplacian spectrum
    lap_eigenvalues: np.ndarray
    lap_spectral_hash: str

    # Non-backtracking spectrum (complex)
    nb_eigenvalues_re: np.ndarray
    nb_eigenvalues_im: np.ndarray
    nb_spectral_hash: str

    # NB Laplacian spectrum (complex)
    nbl_eigenvalues_re: np.ndarray
    nbl_eigenvalues_im: np.ndarray
    nbl_spectral_hash: str

    # Distance spectrum (real; None for disconnected graphs)
    dist_eigenvalues: np.ndarray | None
    dist_spectral_hash: str | None

    # Distance Laplacian / distance signless Laplacian (real; None if disconnected)
    distlap_eigenvalues: np.ndarray | None
    distlap_spectral_hash: str | None
    distsign_eigenvalues: np.ndarray | None
    distsign_spectral_hash: str | None

    # Seidel spectrum (real)
    seidel_eigenvalues: np.ndarray
    seidel_spectral_hash: str

    # k-blocking spectra (complex; None when the cycle core is empty/trivial)
    kblock3_eigenvalues_re: np.ndarray | None
    kblock3_eigenvalues_im: np.ndarray | None
    kblock3_spectral_hash: str | None
    kblock4_eigenvalues_re: np.ndarray | None
    kblock4_eigenvalues_im: np.ndarray | None
    kblock4_spectral_hash: str | None

    # Yoon m-Laplacian spectra (real; None when n <= m)
    yoon2_eigenvalues: np.ndarray | None
    yoon2_spectral_hash: str | None
    yoon3_eigenvalues: np.ndarray | None
    yoon3_spectral_hash: str | None

    # Non-k-cycling spectra (complex; None when nilpotent / all-zero spectrum)
    non3cyc_eigenvalues_re: np.ndarray | None
    non3cyc_eigenvalues_im: np.ndarray | None
    non3cyc_spectral_hash: str | None
    non4cyc_eigenvalues_re: np.ndarray | None
    non4cyc_eigenvalues_im: np.ndarray | None
    non4cyc_spectral_hash: str | None

    # Metadata
    is_bipartite: bool
    is_planar: bool
    is_regular: bool
    diameter: int
    girth: int | None
    radius: int
    min_degree: int
    max_degree: int
    triangle_count: int

    def to_db_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (
            self.n,
            self.m,
            self.graph6,
            self.adj_eigenvalues.tolist() if self.adj_eigenvalues is not None else None,
            self.adj_spectral_hash,
            self.kirchhoff_eigenvalues.tolist() if self.kirchhoff_eigenvalues is not None else None,
            self.kirchhoff_spectral_hash,
            self.signless_eigenvalues.tolist() if self.signless_eigenvalues is not None else None,
            self.signless_spectral_hash,
            self.lap_eigenvalues.tolist() if self.lap_eigenvalues is not None else None,
            self.lap_spectral_hash,
            self.nb_eigenvalues_re.tolist() if self.nb_eigenvalues_re is not None else None,
            self.nb_eigenvalues_im.tolist() if self.nb_eigenvalues_im is not None else None,
            self.nb_spectral_hash,
            self.nbl_eigenvalues_re.tolist() if self.nbl_eigenvalues_re is not None else None,
            self.nbl_eigenvalues_im.tolist() if self.nbl_eigenvalues_im is not None else None,
            self.nbl_spectral_hash,
            self.dist_eigenvalues.tolist() if self.dist_eigenvalues is not None else None,
            self.dist_spectral_hash,
            self.distlap_eigenvalues.tolist() if self.distlap_eigenvalues is not None else None,
            self.distlap_spectral_hash,
            self.distsign_eigenvalues.tolist() if self.distsign_eigenvalues is not None else None,
            self.distsign_spectral_hash,
            self.seidel_eigenvalues.tolist() if self.seidel_eigenvalues is not None else None,
            self.seidel_spectral_hash,
            self.kblock3_eigenvalues_re.tolist() if self.kblock3_eigenvalues_re is not None else None,
            self.kblock3_eigenvalues_im.tolist() if self.kblock3_eigenvalues_im is not None else None,
            self.kblock3_spectral_hash,
            self.kblock4_eigenvalues_re.tolist() if self.kblock4_eigenvalues_re is not None else None,
            self.kblock4_eigenvalues_im.tolist() if self.kblock4_eigenvalues_im is not None else None,
            self.kblock4_spectral_hash,
            self.yoon2_eigenvalues.tolist() if self.yoon2_eigenvalues is not None else None,
            self.yoon2_spectral_hash,
            self.yoon3_eigenvalues.tolist() if self.yoon3_eigenvalues is not None else None,
            self.yoon3_spectral_hash,
            self.non3cyc_eigenvalues_re.tolist() if self.non3cyc_eigenvalues_re is not None else None,
            self.non3cyc_eigenvalues_im.tolist() if self.non3cyc_eigenvalues_im is not None else None,
            self.non3cyc_spectral_hash,
            self.non4cyc_eigenvalues_re.tolist() if self.non4cyc_eigenvalues_re is not None else None,
            self.non4cyc_eigenvalues_im.tolist() if self.non4cyc_eigenvalues_im is not None else None,
            self.non4cyc_spectral_hash,
            self.is_bipartite,
            self.is_planar,
            self.is_regular,
            self.diameter,
            self.girth,
            self.radius,
            self.min_degree,
            self.max_degree,
            self.triangle_count,
        )


def process_graph(G: nx.Graph, graph6_str: str) -> GraphRecord:
    """
    Process a graph and compute all spectral and metadata properties.

    Args:
        G: NetworkX graph object
        graph6_str: The graph6 encoding of the graph

    Returns:
        GraphRecord with all computed properties
    """
    # Compute matrices
    A = adjacency_matrix(G)
    L_kirchhoff = kirchhoff_laplacian(G)
    Q_signless = signless_laplacian(G)
    L_normalized = laplacian_matrix(G)
    B = nonbacktracking_matrix(G)
    L_NB = nonbacktracking_laplacian(G)
    D_dist = distance_matrix(G)  # None for disconnected graphs
    S_seidel = seidel_matrix(G)

    # Compute eigenvalues
    adj_eigs = compute_real_eigenvalues(A)
    kirchhoff_eigs = compute_real_eigenvalues(L_kirchhoff)
    signless_eigs = compute_real_eigenvalues(Q_signless)
    lap_eigs = compute_real_eigenvalues(L_normalized)
    nb_eigs = compute_complex_eigenvalues(B)
    nbl_eigs = compute_complex_eigenvalues(L_NB)

    # Compute hashes
    adj_hash = spectral_hash_real(adj_eigs)
    kirchhoff_hash = spectral_hash_real(kirchhoff_eigs)
    signless_hash = spectral_hash_real(signless_eigs)
    lap_hash = spectral_hash_real(lap_eigs)
    nb_hash = spectral_hash_complex(nb_eigs)
    nbl_hash = spectral_hash_complex(nbl_eigs)

    # Distance-based spectra are only defined for connected graphs.
    if D_dist is not None:
        dist_eigs = compute_real_eigenvalues(D_dist)
        dist_hash = spectral_hash_real(dist_eigs)
        distlap_eigs = compute_real_eigenvalues(distance_laplacian(G))
        distlap_hash = spectral_hash_real(distlap_eigs)
        distsign_eigs = compute_real_eigenvalues(distance_signless_laplacian(G))
        distsign_hash = spectral_hash_real(distsign_eigs)
    else:
        dist_eigs = dist_hash = None
        distlap_eigs = distlap_hash = None
        distsign_eigs = distsign_hash = None

    seidel_eigs = compute_real_eigenvalues(S_seidel)
    seidel_hash = spectral_hash_real(seidel_eigs)

    # The k-blocking and non-cycling matrices are ~1000x slower per graph than
    # all the others combined (large De Bruijn-style operators), so at n=10
    # scale they are skipped during generation and can be backfilled later.
    if SKIP_EXPENSIVE:
        kb3_re = kb3_im = kb3_hash = None
        kb4_re = kb4_im = kb4_hash = None
        n3_re = n3_im = n3_hash = None
        n4_re = n4_im = n4_hash = None
    else:
        kb3_re, kb3_im, kb3_hash = _complex_spectrum_or_none(kblock3_matrix(G), size=kblock3_size(G))
        kb4_re, kb4_im, kb4_hash = _complex_spectrum_or_none(kblock4_matrix(G), size=kblock4_size(G))
        n3_re, n3_im, n3_hash = _complex_spectrum_or_none(non3cyc_matrix(G))
        n4_re, n4_im, n4_hash = _complex_spectrum_or_none(non4cyc_matrix(G))

    yoon2_eigs, yoon2_hash = _real_spectrum_or_none(yoon2_matrix(G))
    yoon3_eigs, yoon3_hash = _real_spectrum_or_none(yoon3_matrix(G))

    # Compute metadata
    meta = compute_metadata(G)

    record = GraphRecord(
        graph6=graph6_str,
        n=meta["n"],
        m=meta["m"],
        adj_eigenvalues=adj_eigs,
        adj_spectral_hash=adj_hash,
        kirchhoff_eigenvalues=kirchhoff_eigs,
        kirchhoff_spectral_hash=kirchhoff_hash,
        signless_eigenvalues=signless_eigs,
        signless_spectral_hash=signless_hash,
        lap_eigenvalues=lap_eigs,
        lap_spectral_hash=lap_hash,
        nb_eigenvalues_re=nb_eigs.real,
        nb_eigenvalues_im=nb_eigs.imag,
        nb_spectral_hash=nb_hash,
        nbl_eigenvalues_re=nbl_eigs.real,
        nbl_eigenvalues_im=nbl_eigs.imag,
        nbl_spectral_hash=nbl_hash,
        dist_eigenvalues=dist_eigs,
        dist_spectral_hash=dist_hash,
        distlap_eigenvalues=distlap_eigs,
        distlap_spectral_hash=distlap_hash,
        distsign_eigenvalues=distsign_eigs,
        distsign_spectral_hash=distsign_hash,
        seidel_eigenvalues=seidel_eigs,
        seidel_spectral_hash=seidel_hash,
        kblock3_eigenvalues_re=kb3_re,
        kblock3_eigenvalues_im=kb3_im,
        kblock3_spectral_hash=kb3_hash,
        kblock4_eigenvalues_re=kb4_re,
        kblock4_eigenvalues_im=kb4_im,
        kblock4_spectral_hash=kb4_hash,
        yoon2_eigenvalues=yoon2_eigs,
        yoon2_spectral_hash=yoon2_hash,
        yoon3_eigenvalues=yoon3_eigs,
        yoon3_spectral_hash=yoon3_hash,
        non3cyc_eigenvalues_re=n3_re,
        non3cyc_eigenvalues_im=n3_im,
        non3cyc_spectral_hash=n3_hash,
        non4cyc_eigenvalues_re=n4_re,
        non4cyc_eigenvalues_im=n4_im,
        non4cyc_spectral_hash=n4_hash,
        is_bipartite=meta["is_bipartite"],
        is_planar=meta["is_planar"],
        is_regular=meta["is_regular"],
        diameter=meta["diameter"],
        girth=meta["girth"],
        radius=meta["radius"],
        min_degree=meta["min_degree"],
        max_degree=meta["max_degree"],
        triangle_count=meta["triangle_count"],
    )

    if HASH_ONLY:
        # Keep the spectral hashes (cospectrality); drop the eigenvalue arrays.
        record = replace(record, **{
            f.name: None for f in fields(record)
            if f.name.endswith(("_eigenvalues", "_eigenvalues_re", "_eigenvalues_im"))
        })
    return record


def graph_from_graph6(graph6_str: str) -> nx.Graph:
    """Parse a graph6 string into a NetworkX graph."""
    return nx.from_graph6_bytes(graph6_str.encode("ascii"))
