"""Graph data processing - combines all computations for a single graph."""

from dataclasses import dataclass
import numpy as np
import networkx as nx

from .matrices import (
    adjacency_matrix,
    laplacian_matrix,
    nonbacktracking_matrix,
    nonbacktracking_laplacian,
)
from .spectrum import (
    compute_real_eigenvalues,
    compute_complex_eigenvalues,
    spectral_hash_real,
    spectral_hash_complex,
)
from .metadata import compute_metadata


@dataclass
class GraphRecord:
    """Complete record for a graph ready for database insertion."""

    graph6: str
    n: int
    m: int

    # Adjacency spectrum
    adj_eigenvalues: np.ndarray
    adj_spectral_hash: str

    # Laplacian spectrum
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
            list(self.adj_eigenvalues),
            self.adj_spectral_hash,
            list(self.lap_eigenvalues),
            self.lap_spectral_hash,
            list(self.nb_eigenvalues_re),
            list(self.nb_eigenvalues_im),
            self.nb_spectral_hash,
            list(self.nbl_eigenvalues_re),
            list(self.nbl_eigenvalues_im),
            self.nbl_spectral_hash,
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
    L = laplacian_matrix(G)
    B = nonbacktracking_matrix(G)
    L_NB = nonbacktracking_laplacian(G)

    # Compute eigenvalues
    adj_eigs = compute_real_eigenvalues(A)
    lap_eigs = compute_real_eigenvalues(L)
    nb_eigs = compute_complex_eigenvalues(B)
    nbl_eigs = compute_complex_eigenvalues(L_NB)

    # Compute hashes
    adj_hash = spectral_hash_real(adj_eigs)
    lap_hash = spectral_hash_real(lap_eigs)
    nb_hash = spectral_hash_complex(nb_eigs)
    nbl_hash = spectral_hash_complex(nbl_eigs)

    # Compute metadata
    meta = compute_metadata(G)

    return GraphRecord(
        graph6=graph6_str,
        n=meta["n"],
        m=meta["m"],
        adj_eigenvalues=adj_eigs,
        adj_spectral_hash=adj_hash,
        lap_eigenvalues=lap_eigs,
        lap_spectral_hash=lap_hash,
        nb_eigenvalues_re=nb_eigs.real,
        nb_eigenvalues_im=nb_eigs.imag,
        nb_spectral_hash=nb_hash,
        nbl_eigenvalues_re=nbl_eigs.real,
        nbl_eigenvalues_im=nbl_eigs.imag,
        nbl_spectral_hash=nbl_hash,
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
