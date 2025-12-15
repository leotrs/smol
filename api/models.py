"""Pydantic models for API responses."""

from pydantic import BaseModel


class GraphProperties(BaseModel):
    # Structural properties
    is_bipartite: bool
    is_planar: bool
    is_regular: bool
    diameter: int | None
    girth: int | None
    radius: int | None
    min_degree: int
    max_degree: int
    triangle_count: int
    # Graph-theoretic properties
    clique_number: int | None = None
    chromatic_number: int | None = None
    # Network science properties
    algebraic_connectivity: float | None = None
    global_clustering: float | None = None
    avg_local_clustering: float | None = None
    avg_path_length: float | None = None
    assortativity: float | None = None
    # Distributions (sorted arrays)
    degree_sequence: list[int] | None = None
    betweenness_centrality: list[float] | None = None
    closeness_centrality: list[float] | None = None
    eigenvector_centrality: list[float] | None = None


class Spectra(BaseModel):
    adj_eigenvalues: list[float]
    adj_hash: str
    lap_eigenvalues: list[float]
    lap_hash: str
    nb_eigenvalues_re: list[float]
    nb_eigenvalues_im: list[float]
    nb_hash: str
    nbl_eigenvalues_re: list[float]
    nbl_eigenvalues_im: list[float]
    nbl_hash: str


class CospectralMates(BaseModel):
    adj: list[str]
    lap: list[str]
    nb: list[str]
    nbl: list[str]


class GraphFull(BaseModel):
    graph6: str
    n: int
    m: int
    edges: list[tuple[int, int]]  # For visualization
    properties: GraphProperties
    spectra: Spectra
    cospectral_mates: CospectralMates


class GraphSummary(BaseModel):
    graph6: str
    n: int
    m: int
    properties: GraphProperties


class CompareResult(BaseModel):
    graphs: list[GraphFull]
    spectral_comparison: dict[str, str]  # matrix -> "same" or "different"


class PropertyStats(BaseModel):
    total: int
    computed: int
    percent: float


class PropertyRange(BaseModel):
    min: float
    max: float
    avg: float


class Stats(BaseModel):
    total_graphs: int
    connected_graphs: int
    counts_by_n: dict[int, int]
    cospectral_counts: dict[str, dict[int, int]]  # matrix -> n -> count
    property_stats: PropertyStats | None = None
    property_ranges: dict[str, PropertyRange] | None = None
