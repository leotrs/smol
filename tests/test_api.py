"""Tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

needs_db = pytest.mark.needs_db


class TestHomeEndpoint:
    def test_home_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "SMOL" in response.text
        assert "Search" in response.text


@needs_db
class TestGraphEndpoint:
    def test_graph_returns_json_by_default(self):
        response = client.get("/graph/D%3F%7B")  # D?{
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert data["graph6"] == "D?{"
        assert data["n"] == 5
        assert data["m"] == 4
        assert "edges" in data
        assert len(data["edges"]) == 4
        assert "properties" in data
        assert "spectra" in data
        assert "cospectral_mates" in data

    def test_graph_returns_html_for_htmx(self):
        response = client.get("/graph/D%3F%7B", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "D?{" in response.text
        assert "5 vertices" in response.text

    def test_graph_returns_html_for_browser(self):
        response = client.get("/graph/D%3F%7B", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_graph_not_found(self):
        response = client.get("/graph/INVALID")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_graph_properties(self):
        response = client.get("/graph/D%3F%7B")
        data = response.json()
        props = data["properties"]
        assert props["is_bipartite"] is True
        assert props["is_planar"] is True
        assert props["diameter"] == 2

    def test_graph_has_network_science_properties(self):
        """New network science properties should be present in response."""
        response = client.get("/graph/D%3F%7B")
        data = response.json()
        props = data["properties"]
        # These fields should exist (may be null if not computed)
        assert "clique_number" in props
        assert "chromatic_number" in props
        assert "algebraic_connectivity" in props
        assert "global_clustering" in props
        assert "avg_local_clustering" in props
        assert "avg_path_length" in props
        assert "assortativity" in props
        assert "degree_sequence" in props
        assert "betweenness_centrality" in props
        assert "closeness_centrality" in props
        assert "eigenvector_centrality" in props

    def test_graph_has_tags(self):
        """Tags field should be present in response (may be empty list)."""
        response = client.get("/graph/D%3F%7B")
        data = response.json()
        assert "tags" in data
        assert isinstance(data["tags"], list)

    def test_graph_spectra(self):
        response = client.get("/graph/D%3F%7B")
        data = response.json()
        spectra = data["spectra"]
        assert len(spectra["adj_eigenvalues"]) == 5
        assert len(spectra["lap_eigenvalues"]) == 5
        assert "adj_hash" in spectra
        assert len(spectra["adj_hash"]) == 16

    def test_graph_cospectral_mates(self):
        response = client.get("/graph/D%3F%7B")
        data = response.json()
        mates = data["cospectral_mates"]
        assert "adj" in mates
        assert "lap" in mates
        assert "nb" in mates
        assert "nbl" in mates
        # D?{ has adj cospectral mate DEo
        assert "DEo" in mates["adj"]


@needs_db
class TestGraphsEndpoint:
    def test_graphs_query_by_n(self):
        response = client.get("/graphs?n=5&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
        for g in data:
            assert g["n"] == 5

    def test_graphs_query_by_properties(self):
        response = client.get("/graphs?n=5&bipartite=true&limit=10")
        assert response.status_code == 200
        data = response.json()
        for g in data:
            assert g["properties"]["is_bipartite"] is True

    def test_graphs_returns_html_for_htmx(self):
        response = client.get("/graphs?n=5&limit=5", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<table" in response.text

    def test_graphs_direct_lookup(self):
        response = client.get("/graphs?graph6=D%3F%7B")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["graph6"] == "D?{"

    def test_graphs_direct_lookup_not_found(self):
        response = client.get("/graphs?graph6=INVALID")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_graphs_limit(self):
        response = client.get("/graphs?n=7&limit=5")
        data = response.json()
        assert len(data) <= 5

    def test_graphs_limit_max(self):
        response = client.get("/graphs?limit=9999")
        assert response.status_code == 422  # Validation error, limit > 1000


@needs_db
class TestCompareEndpoint:
    def test_compare_two_graphs(self):
        response = client.get("/compare?graphs=D%3F%7B,DEo")
        assert response.status_code == 200
        data = response.json()
        assert len(data["graphs"]) == 2
        assert "spectral_comparison" in data

    def test_compare_spectral_comparison(self):
        response = client.get("/compare?graphs=D%3F%7B,DEo")
        data = response.json()
        comp = data["spectral_comparison"]
        # D?{ and DEo are adj-cospectral
        assert comp["adj"] == "same"

    def test_compare_returns_html_for_htmx(self):
        response = client.get(
            "/compare?graphs=D%3F%7B,DEo", headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Comparing" in response.text

    def test_compare_needs_two_graphs(self):
        response = client.get("/compare?graphs=D%3F%7B")
        assert response.status_code == 400
        assert "at least 2" in response.json()["detail"].lower()

    def test_compare_max_ten_graphs(self):
        graphs = ",".join(["D%3F%7B"] * 11)
        response = client.get(f"/compare?graphs={graphs}")
        assert response.status_code == 400
        assert "maximum 10" in response.json()["detail"].lower()

    def test_compare_graph_not_found(self):
        response = client.get("/compare?graphs=D%3F%7B,INVALID")
        assert response.status_code == 404


class TestGlossaryEndpoint:
    def test_glossary_returns_html(self):
        response = client.get("/glossary")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Glossary" in response.text
        assert "graph6" in response.text
        assert "adjacency" in response.text
        assert "cospectral" in response.text


@needs_db
class TestAboutEndpoint:
    def test_about_returns_html_for_browser(self):
        response = client.get("/about", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "About" in response.text

    def test_about_returns_json_by_default(self):
        response = client.get("/about")
        assert response.status_code == 200
        data = response.json()
        assert "total_graphs" in data
        assert "connected_graphs" in data
        assert "counts_by_n" in data
        assert "cospectral_counts" in data


@needs_db
class TestStatsEndpoint:
    def test_stats_returns_json(self):
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_graphs" in data
        assert "connected_graphs" in data
        assert "counts_by_n" in data
        assert "cospectral_counts" in data

    def test_stats_structure(self):
        response = client.get("/stats")
        data = response.json()
        # Check structure without waiting for slow aggregation
        cospectral = data["cospectral_counts"]
        assert "adj" in cospectral
        assert "lap" in cospectral
        assert "nb" in cospectral
        assert "nbl" in cospectral


@needs_db
class TestRandomEndpoints:
    def test_random_graph_redirects(self):
        response = client.get("/random", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"].startswith("/graph/")

    def test_random_graph_follows_redirect(self):
        response = client.get("/random", follow_redirects=True)
        assert response.status_code == 200
        # Should end up at a graph detail page
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert "graph6" in data
        assert "n" in data

    def test_random_cospectral_redirects(self):
        response = client.get("/random/cospectral", follow_redirects=False)
        # Might be 302 (found cospectral) or 404 (none found in attempts)
        assert response.status_code in (302, 404)
        if response.status_code == 302:
            assert "/compare?graphs=" in response.headers["location"]

    def test_random_cospectral_with_matrix_type(self):
        response = client.get("/random/cospectral?matrix=lap", follow_redirects=False)
        assert response.status_code in (302, 404)

    def test_random_cospectral_invalid_matrix(self):
        response = client.get("/random/cospectral?matrix=invalid")
        assert response.status_code == 400
        assert "invalid matrix" in response.json()["detail"].lower()


@needs_db
class TestGraphsEdgeCases:
    def test_graphs_empty_params(self):
        # Empty string params should be treated as None
        response = client.get("/graphs?n=&m=&bipartite=&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_graphs_with_all_filters(self):
        response = client.get(
            "/graphs?n=6&bipartite=true&planar=true&regular=true&limit=5"
        )
        assert response.status_code == 200
        data = response.json()
        for g in data:
            assert g["n"] == 6
            assert g["properties"]["is_bipartite"] is True
            assert g["properties"]["is_planar"] is True
            assert g["properties"]["is_regular"] is True

    def test_graphs_by_edge_count(self):
        response = client.get("/graphs?n=5&m=5&limit=10")
        assert response.status_code == 200
        data = response.json()
        for g in data:
            assert g["n"] == 5
            assert g["m"] == 5


@needs_db
class TestGraphSpecialCharacters:
    def test_graph_with_question_mark(self):
        # D?{ contains a question mark
        response = client.get("/graph/D%3F%7B")
        assert response.status_code == 200
        assert response.json()["graph6"] == "D?{"

    def test_graph_with_backtick(self):
        # Some graph6 strings contain backticks
        response = client.get("/graph/E%60o")  # E`o
        # Might or might not exist, just check no server error
        assert response.status_code in (200, 404)

    def test_graph_with_special_chars_html(self):
        response = client.get("/graph/D%3F%7B", headers={"Accept": "text/html"})
        assert response.status_code == 200
        # Check that special chars are properly escaped in HTML
        assert "D?{" in response.text or "D?{" in response.text


@needs_db
class TestCompareEdgeCases:
    def test_compare_same_graph_twice(self):
        response = client.get("/compare?graphs=D%3F%7B,D%3F%7B")
        assert response.status_code == 200
        data = response.json()
        assert len(data["graphs"]) == 2
        # Same graph should have same spectrum
        assert data["spectral_comparison"]["adj"] == "same"

    def test_compare_html_has_visualizations(self):
        response = client.get(
            "/compare?graphs=D%3F%7B,DEo", headers={"Accept": "text/html"}
        )
        assert response.status_code == 200
        assert "viz-" in response.text  # D3 viz containers
        assert "renderGraphs" in response.text  # JS function


class TestHomeSearch:
    def test_home_has_search_form(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Lookup" in response.text
        assert "Search" in response.text
        assert "graph6" in response.text

    def test_home_has_compare_tab(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Compare" in response.text
        assert "compareGraphs" in response.text

    def test_home_has_random_links_in_footer(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "/random" in response.text
        assert "Random graph" in response.text
        assert "Random cospectral family" in response.text

    @needs_db
    def test_home_example_graphs_exist(self):
        """Verify all example graphs on home page exist in database."""
        from urllib.parse import quote
        # Example graphs + cospectral family examples (adj, lap, nb, nbl)
        example_graphs = [
            "D~{", "EEh_", "E?Bw", "G?zTb_",  # Named graphs
            "D?{", "DEo", "ECRw", "EEiW",      # Adj cospectral
            "CF", "C]", "E?zW", "ECxw",        # Lap cospectral
            "DC{", "DEk", "E?ro", "E?zO",      # NB cospectral
            "CU", "E?bw", "ECZG",              # NBL cospectral (CF already listed)
        ]
        for g6 in example_graphs:
            response = client.get(f"/graph/{quote(g6, safe='')}")
            assert response.status_code == 200, f"Example graph {g6} not found"


@needs_db
class TestComparePropertyDiffs:
    def test_compare_highlights_different_properties(self):
        """Compare endpoint should flag properties that differ between graphs."""
        # D~{ (K5, diameter=1) vs DQo (P5, diameter=4)
        response = client.get(
            "/compare?graphs=D~%7B,DQo",
            headers={"Accept": "text/html"}
        )
        assert response.status_code == 200
        assert 'class="row-diff"' in response.text

    def test_compare_same_graphs_no_diff_highlight(self):
        """Same graph compared to itself should have no diff highlights."""
        response = client.get(
            "/compare?graphs=D%3F%7B,D%3F%7B",
            headers={"Accept": "text/html"}
        )
        assert response.status_code == 200
        assert 'class="row-diff"' not in response.text

    def test_eigenvalues_formatted_as_python_list(self):
        """Eigenvalues should be wrapped in brackets for Python list syntax."""
        response = client.get("/graph/D%3F%7B", headers={"Accept": "text/html"})
        assert response.status_code == 200
        # Check for opening bracket at start of eigenvalue list
        assert "[" in response.text and "]" in response.text

    def test_graph_detail_has_code_snippet(self):
        """Graph detail page should have copyable Python code snippet."""
        response = client.get("/graph/D%3F%7B", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "import networkx as nx" in response.text
        assert "nx.from_graph6_bytes" in response.text
        assert 'b"D?{"' in response.text

    def test_graph_detail_has_export_buttons(self):
        """Graph detail page should have export buttons."""
        response = client.get("/graph/D%3F%7B", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "Export" in response.text
        assert "downloadJSON" in response.text
        assert "downloadEdgeList" in response.text
        assert "downloadAdjList" in response.text

    def test_graph_detail_has_find_similar_link(self):
        """Graph detail page should have link to find similar spectra."""
        response = client.get("/graph/D%3F%7B", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "Find similar" in response.text
        assert "/similar/" in response.text


@needs_db
class TestSimilarEndpoint:
    def test_similar_returns_json(self):
        response = client.get("/similar/D%3F%7B")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert "graph" in item
            assert "distance" in item
            assert item["distance"] >= 0

    def test_similar_includes_cospectral_mates_with_zero_distance(self):
        """Cospectral mates should appear first with distance ~0."""
        # D?{ and DEo are known adj-cospectral mates
        response = client.get("/similar/D%3F%7B?matrix=adj")
        assert response.status_code == 200
        data = response.json()

        # Find DEo in results
        deo_result = next((item for item in data if item["graph"]["graph6"] == "DEo"), None)
        assert deo_result is not None, "Cospectral mate DEo should appear in results"
        assert deo_result["distance"] < 1e-6, "Cospectral mate should have distance ~0"

    def test_similar_with_matrix_param(self):
        response = client.get("/similar/D%3F%7B?matrix=lap")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_similar_invalid_matrix(self):
        response = client.get("/similar/D%3F%7B?matrix=invalid")
        assert response.status_code == 400
        assert "invalid matrix" in response.json()["detail"].lower()

    def test_similar_not_found(self):
        response = client.get("/similar/INVALID")
        assert response.status_code == 404

    def test_similar_returns_html(self):
        response = client.get("/similar/D%3F%7B", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Similar" in response.text
