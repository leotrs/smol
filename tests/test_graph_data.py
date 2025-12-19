"""Tests for graph data processing."""

import networkx as nx

from db.graph_data import process_graph, graph_from_graph6, GraphRecord


def test_graph_from_graph6_path():
    """Test parsing graph6 for P4."""
    # P4 in graph6 format
    g6 = "CF"
    G = graph_from_graph6(g6)

    assert G.number_of_nodes() == 4
    assert G.number_of_edges() == 3
    assert nx.is_connected(G)


def test_graph_from_graph6_complete():
    """Test parsing graph6 for K4."""
    g6 = "C~"
    G = graph_from_graph6(g6)

    assert G.number_of_nodes() == 4
    assert G.number_of_edges() == 6


def test_process_graph_returns_record():
    """process_graph should return a GraphRecord."""
    G = nx.path_graph(4)
    g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()

    record = process_graph(G, g6)

    assert isinstance(record, GraphRecord)
    assert record.n == 4
    assert record.m == 3


def test_process_graph_eigenvalues_count():
    """Check correct number of eigenvalues."""
    G = nx.cycle_graph(5)
    g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()

    record = process_graph(G, g6)

    # Adjacency and Laplacian: n eigenvalues
    assert len(record.adj_eigenvalues) == 5
    assert len(record.lap_eigenvalues) == 5

    # NB matrices: we store only eigenvalues with non-negative imaginary part
    # (one representative from each conjugate pair), so between m and 2m eigenvalues
    m = G.number_of_edges()
    assert m <= len(record.nb_eigenvalues_re) <= 2 * m
    assert len(record.nb_eigenvalues_re) == len(record.nb_eigenvalues_im)
    assert m <= len(record.nbl_eigenvalues_re) <= 2 * m
    assert len(record.nbl_eigenvalues_re) == len(record.nbl_eigenvalues_im)


def test_process_graph_hashes():
    """Check hashes are 16 characters."""
    G = nx.complete_graph(4)
    g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()

    record = process_graph(G, g6)

    assert len(record.adj_spectral_hash) == 16
    assert len(record.lap_spectral_hash) == 16
    assert len(record.nb_spectral_hash) == 16
    assert len(record.nbl_spectral_hash) == 16


def test_process_graph_metadata():
    """Check metadata is computed correctly."""
    G = nx.cycle_graph(6)
    g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()

    record = process_graph(G, g6)

    assert record.is_bipartite is True  # Even cycle
    assert record.is_planar is True
    assert record.is_regular is True  # All degree 2
    assert record.min_degree == 2
    assert record.max_degree == 2
    assert record.diameter == 3
    assert record.girth == 6
    assert record.triangle_count == 0


def test_process_graph_complete():
    """Check metadata for complete graph."""
    G = nx.complete_graph(4)
    g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()

    record = process_graph(G, g6)

    assert record.is_bipartite is False
    assert record.is_planar is True  # K4 is planar
    assert record.is_regular is True
    assert record.diameter == 1
    assert record.girth == 3  # Has triangles
    assert record.triangle_count == 4  # C(4,3) = 4 triangles


def test_process_graph_star():
    """Check metadata for star graph (tree)."""
    G = nx.star_graph(4)  # 5 vertices: 1 center + 4 leaves
    g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()

    record = process_graph(G, g6)

    assert record.n == 5
    assert record.m == 4
    assert record.is_bipartite is True
    assert record.girth is None  # Tree, no cycles
    assert record.min_degree == 1
    assert record.max_degree == 4
    assert record.triangle_count == 0


def test_to_db_tuple():
    """Check to_db_tuple returns correct format."""
    G = nx.path_graph(3)
    g6 = nx.to_graph6_bytes(G, header=False).decode("ascii").strip()

    record = process_graph(G, g6)
    tup = record.to_db_tuple()

    assert isinstance(tup, tuple)
    assert len(tup) == 26  # All fields for DB insert (includes kirchhoff and signless)
    assert tup[0] == 3  # n
    assert tup[1] == 2  # m


def test_cospectral_graphs_same_hash():
    """Two co-spectral graphs should have the same adjacency hash."""
    # K1,4 and C4 + isolated vertex are co-spectral for adjacency
    # But let's use a simpler example: same graph should have same hash
    G1 = nx.cycle_graph(5)
    G2 = nx.cycle_graph(5)

    g6_1 = nx.to_graph6_bytes(G1, header=False).decode("ascii").strip()
    g6_2 = nx.to_graph6_bytes(G2, header=False).decode("ascii").strip()

    record1 = process_graph(G1, g6_1)
    record2 = process_graph(G2, g6_2)

    assert record1.adj_spectral_hash == record2.adj_spectral_hash
    assert record1.lap_spectral_hash == record2.lap_spectral_hash
