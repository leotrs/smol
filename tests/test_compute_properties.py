"""Tests for compute_properties script."""

import networkx as nx
import sys
sys.path.insert(0, "scripts")
from compute_properties import compute_properties, graph6_to_nx


class TestGraph6ToNx:
    def test_star_graph(self):
        """D?{ is K_{1,4} star graph."""
        G = graph6_to_nx("D?{")
        assert G.number_of_nodes() == 5
        assert G.number_of_edges() == 4

    def test_complete_graph(self):
        """D~{ is K_5 complete graph."""
        G = graph6_to_nx("D~{")
        assert G.number_of_nodes() == 5
        assert G.number_of_edges() == 10


class TestComputeProperties:
    def test_complete_graph_k5(self):
        """K_5 has known properties."""
        G = nx.complete_graph(5)
        props = compute_properties(G)

        assert props["clique_number"] == 5
        assert props["chromatic_number"] == 5
        assert props["global_clustering"] == 1.0
        assert props["avg_local_clustering"] == 1.0
        assert props["avg_path_length"] == 1.0

    def test_path_graph(self):
        """Path graph P_5 has known properties."""
        G = nx.path_graph(5)
        props = compute_properties(G)

        assert props["clique_number"] == 2
        assert props["chromatic_number"] == 2
        assert props["global_clustering"] == 0.0
        assert props["avg_local_clustering"] == 0.0

    def test_cycle_graph(self):
        """Cycle C_5 has known properties."""
        G = nx.cycle_graph(5)
        props = compute_properties(G)

        assert props["clique_number"] == 2
        assert props["chromatic_number"] == 3  # odd cycle needs 3 colors
        assert props["global_clustering"] == 0.0

    def test_star_graph(self):
        """Star graph K_{1,4} has known properties."""
        G = nx.star_graph(4)  # creates K_{1,4} with 5 nodes
        props = compute_properties(G)

        assert props["clique_number"] == 2
        assert props["chromatic_number"] == 2
        assert props["global_clustering"] == 0.0

    def test_empty_graph(self):
        """Single node graph."""
        G = nx.Graph()
        G.add_node(0)
        props = compute_properties(G)

        assert props["clique_number"] == 1
        assert props["chromatic_number"] == 1

    def test_algebraic_connectivity_connected(self):
        """Connected graph has positive algebraic connectivity."""
        G = nx.complete_graph(5)
        props = compute_properties(G)
        assert props["algebraic_connectivity"] > 0

    def test_assortativity_regular_graph(self):
        """Regular graphs have undefined or zero assortativity."""
        G = nx.cycle_graph(5)
        props = compute_properties(G)
        # Assortativity is undefined for regular graphs (all same degree)
        assert props["assortativity"] is None or abs(props["assortativity"]) < 1e-10


class TestComputePropertiesEdgeCases:
    def test_two_node_edge(self):
        """K_2 - simplest connected graph."""
        G = nx.Graph([(0, 1)])
        props = compute_properties(G)

        assert props["clique_number"] == 2
        assert props["chromatic_number"] == 2
        assert props["avg_path_length"] == 1.0

    def test_two_node_no_edge(self):
        """Two isolated nodes."""
        G = nx.Graph()
        G.add_nodes_from([0, 1])
        props = compute_properties(G)

        assert props["clique_number"] == 1
        assert props["chromatic_number"] == 1
        assert props["avg_path_length"] is None  # disconnected

    def test_petersen_graph(self):
        """Petersen graph has well-known properties."""
        G = nx.petersen_graph()
        props = compute_properties(G)

        assert G.number_of_nodes() == 10
        assert G.number_of_edges() == 15
        assert props["clique_number"] == 2  # triangle-free
        assert props["chromatic_number"] == 3
        assert props["global_clustering"] == 0.0  # no triangles

    def test_complete_bipartite(self):
        """K_{3,3} complete bipartite graph."""
        G = nx.complete_bipartite_graph(3, 3)
        props = compute_properties(G)

        assert props["clique_number"] == 2  # bipartite has no triangles
        assert props["chromatic_number"] == 2
        assert props["global_clustering"] == 0.0

    def test_wheel_graph(self):
        """Wheel graph W_5 (hub + 4-cycle)."""
        G = nx.wheel_graph(5)  # 5 nodes total
        props = compute_properties(G)

        assert props["clique_number"] == 3  # hub + 2 adjacent rim nodes
        assert props["global_clustering"] > 0  # has triangles

    def test_large_clique(self):
        """Graph with larger clique."""
        G = nx.Graph()
        # K_4 clique
        G.add_edges_from([(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])
        # Plus one pendant
        G.add_edge(0, 4)
        props = compute_properties(G)

        assert props["clique_number"] == 4
        assert props["chromatic_number"] >= 4
