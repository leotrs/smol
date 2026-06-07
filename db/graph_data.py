"""Graph data processing - combines all computations for a single graph."""

from dataclasses import dataclass
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
)
from .spectrum import (
    compute_real_eigenvalues,
    compute_complex_eigenvalues,
    spectral_hash_real,
    spectral_hash_complex,
)
from .metadata import compute_metadata


def _complex_spectrum_or_none(M):
    """Complex eigenvalues (real, imag) and hash for a matrix.

    Returns (None, None, None) when the spectrum is empty or all-zero, so the
    graph is stored with a NULL hash and not grouped as cospectral.
    """
    eigs = compute_complex_eigenvalues(M)
    if eigs.size == 0 or np.allclose(eigs, 0.0):
        return None, None, None
    return eigs.real, eigs.imag, spectral_hash_complex(eigs)


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
            self.adj_eigenvalues.tolist(),
            self.adj_spectral_hash,
            self.kirchhoff_eigenvalues.tolist(),
            self.kirchhoff_spectral_hash,
            self.signless_eigenvalues.tolist(),
            self.signless_spectral_hash,
            self.lap_eigenvalues.tolist(),
            self.lap_spectral_hash,
            self.nb_eigenvalues_re.tolist(),
            self.nb_eigenvalues_im.tolist(),
            self.nb_spectral_hash,
            self.nbl_eigenvalues_re.tolist(),
            self.nbl_eigenvalues_im.tolist(),
            self.nbl_spectral_hash,
            self.dist_eigenvalues.tolist() if self.dist_eigenvalues is not None else None,
            self.dist_spectral_hash,
            self.distlap_eigenvalues.tolist() if self.distlap_eigenvalues is not None else None,
            self.distlap_spectral_hash,
            self.distsign_eigenvalues.tolist() if self.distsign_eigenvalues is not None else None,
            self.distsign_spectral_hash,
            self.seidel_eigenvalues.tolist(),
            self.seidel_spectral_hash,
            self.kblock3_eigenvalues_re.tolist() if self.kblock3_eigenvalues_re is not None else None,
            self.kblock3_eigenvalues_im.tolist() if self.kblock3_eigenvalues_im is not None else None,
            self.kblock3_spectral_hash,
            self.kblock4_eigenvalues_re.tolist() if self.kblock4_eigenvalues_re is not None else None,
            self.kblock4_eigenvalues_im.tolist() if self.kblock4_eigenvalues_im is not None else None,
            self.kblock4_spectral_hash,
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

    kb3_re, kb3_im, kb3_hash = _complex_spectrum_or_none(kblock3_matrix(G))
    kb4_re, kb4_im, kb4_hash = _complex_spectrum_or_none(kblock4_matrix(G))

    # Compute metadata
    meta = compute_metadata(G)

    return GraphRecord(
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


def graph_from_graph6(graph6_str: str) -> nx.Graph:
    """Parse a graph6 string into a NetworkX graph."""
    return nx.from_graph6_bytes(graph6_str.encode("ascii"))
