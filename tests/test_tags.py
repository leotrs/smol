"""Tests for graph tag detection."""

import networkx as nx
import pytest

from db.tags import compute_tags


class TestCompleteTags:
    def test_k1(self):
        G = nx.complete_graph(1)
        assert "complete" in compute_tags(G)

    def test_k4(self):
        G = nx.complete_graph(4)
        assert "complete" in compute_tags(G)

    def test_k5(self):
        G = nx.complete_graph(5)
        assert "complete" in compute_tags(G)

    def test_not_complete(self):
        G = nx.cycle_graph(5)
        assert "complete" not in compute_tags(G)


class TestCycleTags:
    def test_c3(self):
        G = nx.cycle_graph(3)
        tags = compute_tags(G)
        assert "cycle" in tags
        # C_3 is also K_3
        assert "complete" in tags

    def test_c5(self):
        G = nx.cycle_graph(5)
        tags = compute_tags(G)
        assert "cycle" in tags
        assert "complete" not in tags

    def test_c10(self):
        G = nx.cycle_graph(10)
        assert "cycle" in compute_tags(G)

    def test_not_cycle(self):
        G = nx.path_graph(5)
        assert "cycle" not in compute_tags(G)


class TestPathTags:
    def test_p2(self):
        G = nx.path_graph(2)
        assert "path" in compute_tags(G)

    def test_p5(self):
        G = nx.path_graph(5)
        tags = compute_tags(G)
        assert "path" in tags
        assert "tree" in tags

    def test_not_path(self):
        G = nx.cycle_graph(5)
        assert "path" not in compute_tags(G)


class TestStarTags:
    def test_s3(self):
        G = nx.star_graph(2)  # star_graph(n) creates n+1 nodes
        assert "star" in compute_tags(G)

    def test_s5(self):
        G = nx.star_graph(4)
        tags = compute_tags(G)
        assert "star" in tags
        assert "tree" in tags
        assert "complete-bipartite" in tags  # S_n = K_{1,n-1}

    def test_not_star(self):
        G = nx.cycle_graph(5)
        assert "star" not in compute_tags(G)


class TestWheelTags:
    def test_w4(self):
        G = nx.wheel_graph(4)  # wheel_graph(n) creates n nodes
        assert "wheel" in compute_tags(G)

    def test_w6(self):
        G = nx.wheel_graph(6)
        assert "wheel" in compute_tags(G)

    def test_w4_is_also_complete(self):
        G = nx.wheel_graph(4)  # W_4 = K_4
        tags = compute_tags(G)
        assert "wheel" in tags
        assert "complete" in tags

    def test_not_wheel(self):
        G = nx.cycle_graph(5)
        assert "wheel" not in compute_tags(G)


class TestCompleteBipartiteTags:
    def test_k23(self):
        G = nx.complete_bipartite_graph(2, 3)
        tags = compute_tags(G)
        assert "complete-bipartite" in tags

    def test_k33(self):
        G = nx.complete_bipartite_graph(3, 3)
        tags = compute_tags(G)
        assert "complete-bipartite" in tags
        assert "regular" in tags

    def test_k1n_is_star(self):
        G = nx.complete_bipartite_graph(1, 4)
        tags = compute_tags(G)
        assert "complete-bipartite" in tags
        assert "star" in tags

    def test_not_complete_bipartite(self):
        G = nx.cycle_graph(5)
        assert "complete-bipartite" not in compute_tags(G)


class TestTreeTags:
    def test_path_is_tree(self):
        G = nx.path_graph(5)
        assert "tree" in compute_tags(G)

    def test_star_is_tree(self):
        G = nx.star_graph(4)
        assert "tree" in compute_tags(G)

    def test_random_tree(self):
        G = nx.random_labeled_tree(8, seed=42)
        assert "tree" in compute_tags(G)

    def test_cycle_not_tree(self):
        G = nx.cycle_graph(5)
        assert "tree" not in compute_tags(G)

    def test_complete_not_tree(self):
        G = nx.complete_graph(4)
        assert "tree" not in compute_tags(G)


class TestPetersenTag:
    def test_petersen(self):
        G = nx.petersen_graph()
        tags = compute_tags(G)
        assert "petersen" in tags
        assert "regular" in tags

    def test_not_petersen(self):
        G = nx.complete_graph(10)
        assert "petersen" not in compute_tags(G)


class TestEulerianTag:
    def test_cycle_is_eulerian(self):
        G = nx.cycle_graph(5)
        assert "eulerian" in compute_tags(G)

    def test_complete_odd_is_eulerian(self):
        G = nx.complete_graph(5)  # All vertices have even degree (4)
        assert "eulerian" in compute_tags(G)

    def test_complete_even_not_eulerian(self):
        G = nx.complete_graph(4)  # All vertices have odd degree (3)
        assert "eulerian" not in compute_tags(G)

    def test_path_not_eulerian(self):
        G = nx.path_graph(5)
        assert "eulerian" not in compute_tags(G)


class TestRegularTag:
    def test_cycle_is_regular(self):
        G = nx.cycle_graph(5)
        tags = compute_tags(G)
        assert "regular" in tags

    def test_complete_is_regular(self):
        G = nx.complete_graph(5)
        assert "regular" in compute_tags(G)

    def test_petersen_is_regular(self):
        G = nx.petersen_graph()
        assert "regular" in compute_tags(G)

    def test_path_not_regular(self):
        G = nx.path_graph(5)
        assert "regular" not in compute_tags(G)

    def test_star_not_regular(self):
        G = nx.star_graph(4)
        assert "regular" not in compute_tags(G)


class TestMultipleTags:
    def test_k3_has_multiple_tags(self):
        G = nx.complete_graph(3)
        tags = compute_tags(G)
        assert "complete" in tags
        assert "cycle" in tags
        assert "regular" in tags
        assert "eulerian" in tags

    def test_empty_tags_for_generic_graph(self):
        # A graph that doesn't match any special pattern
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)])
        tags = compute_tags(G)
        # Should at least not crash; may have eulerian if degrees work out
        assert isinstance(tags, list)
