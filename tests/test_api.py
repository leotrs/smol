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
        assert "kirchhoff" in mates
        assert "signless" in mates
        assert "lap" in mates
        assert "nb" in mates
        assert "nbl" in mates
        # D?{ has adj cospectral mate DEo
        assert "DEo" in mates["adj"]

    def test_graph_with_kirchhoff_signless_eigenvalues(self):
        """All graphs should have Kirchhoff and signless eigenvalues computed."""
        # Test with a graph from n=9 (previously these were NULL)
        response = client.get("/graphs?n=9&limit=1")
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                graph6 = data[0]["graph6"]
                from urllib.parse import quote
                detail_response = client.get(f"/graph/{quote(graph6, safe='')}")
                assert detail_response.status_code == 200
                detail_data = detail_response.json()
                # Should have spectra fields with computed values
                assert "spectra" in detail_data
                assert "kirchhoff_eigenvalues" in detail_data["spectra"]
                assert "signless_eigenvalues" in detail_data["spectra"]
                # Should have actual eigenvalues (not empty)
                kirchhoff = detail_data["spectra"]["kirchhoff_eigenvalues"]
                signless = detail_data["spectra"]["signless_eigenvalues"]
                assert isinstance(kirchhoff, list)
                assert isinstance(signless, list)
                assert len(kirchhoff) == 9  # Should have n eigenvalues
                assert len(signless) == 9
                # Should have corresponding hashes
                assert "kirchhoff_hash" in detail_data["spectra"]
                assert "signless_hash" in detail_data["spectra"]
                assert len(detail_data["spectra"]["kirchhoff_hash"]) == 16
                assert len(detail_data["spectra"]["signless_hash"]) == 16


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
        # D?{ and DEo are adj-cospectral (distance should be 0.0000)
        assert comp["adj"] == "0.0000"

    def test_compare_includes_all_matrices(self):
        """Compare endpoint should include all 6 matrix types in spectral_comparison."""
        response = client.get("/compare?graphs=D%3F%7B,DEo")
        assert response.status_code == 200
        data = response.json()
        comp = data["spectral_comparison"]
        # Should have all 6 matrix types
        assert "adj" in comp
        assert "kirchhoff" in comp
        assert "signless" in comp
        assert "lap" in comp
        assert "nb" in comp
        assert "nbl" in comp
        # When comparing 2 graphs, should show numeric distances
        for matrix, value in comp.items():
            # Should be a numeric string like "0.0000" or "1.2345"
            try:
                float(value)
            except ValueError:
                assert value in ("same", "different", "n/a"), f"Invalid comparison value for {matrix}: {value}"

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

    def test_compare_has_spectra_section(self):
        """Compare page should have a Spectra section with visualization."""
        response = client.get("/compare?graphs=D%3F%7B,DEo", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "Spectra</strong>" in response.text or "Spectra</" in response.text
        assert "compare-spectrum-real-plot" in response.text


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
        assert "message" in data
        assert data["message"] == "About page - use HTML request"


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
        # Same graph should have zero spectral distance
        assert data["spectral_comparison"]["adj"] == "0.0000"

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


@needs_db
class TestSearchEndpoint:
    def test_search_returns_html(self):
        """Search endpoint should return HTML page."""
        response = client.get("/search?n=5&m=6")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Search Results" in response.text

    def test_search_shows_results_count(self):
        """Search should show total count and range."""
        response = client.get("/search?n=5&m=6")
        assert response.status_code == 200
        assert "Found" in response.text
        assert "graphs matching your criteria" in response.text
        assert "Showing" in response.text

    def test_search_with_filters(self):
        """Search should support multiple filters."""
        response = client.get("/search?n=5&m=6&diameter=2")
        assert response.status_code == 200
        assert "Search Results" in response.text

    def test_search_pagination(self):
        """Search should support pagination."""
        response = client.get("/search?n=8&limit=50&page=1")
        assert response.status_code == 200
        # For large result sets, uses client-side pagination with x-text
        assert 'class="results-range"' in response.text

    def test_search_pagination_page_2(self):
        """Search should support page 2."""
        response = client.get("/search?n=8&limit=100&page=2")
        assert response.status_code == 200
        # For large result sets, client-side pagination ignores page param
        # All 1000 results are loaded and pagination is handled client-side
        assert 'class="results-range"' in response.text

    def test_search_sorting(self):
        """Search should support sorting."""
        response = client.get("/search?n=5&sort_by=m&sort_order=desc")
        assert response.status_code == 200
        assert "sort-indicator" in response.text

    def test_search_sorting_ascending(self):
        """Search should support ascending sort."""
        response = client.get("/search?n=5&sort_by=m&sort_order=asc")
        assert response.status_code == 200
        assert "sort-indicator" in response.text

    def test_search_invalid_sort_defaults(self):
        """Invalid sort column should default to 'n'."""
        response = client.get("/search?n=5&sort_by=invalid")
        assert response.status_code == 200

    def test_search_api_equivalent_component(self):
        """Search should show API equivalent component."""
        response = client.get("/search?n=5&m=6")
        assert response.status_code == 200
        assert "API Equivalent" in response.text
        assert "curl" in response.text.lower()
        assert "python" in response.text.lower()
        assert "/graphs?" in response.text

    def test_search_api_equivalent_includes_params(self):
        """API equivalent should include search params."""
        response = client.get("/search?n=5&m=6")
        assert response.status_code == 200
        assert "n=5" in response.text or "n': 5" in response.text or 'n": 5' in response.text

    def test_search_with_tags(self):
        """Search should support tags filter."""
        response = client.get("/search?n=4&tags=complete")
        assert response.status_code == 200
        assert "C~" in response.text

    def test_search_empty_results(self):
        """Search with no matches should show empty message."""
        response = client.get("/search?n=10&m=1&diameter=1")
        assert response.status_code == 200
        assert "Found 0 graphs" in response.text or "No graphs found" in response.text

    def test_search_table_headers_sortable(self):
        """Table headers should be sortable (either via links or Alpine.js)."""
        response = client.get("/search?n=5")
        assert response.status_code == 200
        # Check for sorting capability (either href links or Alpine.js columns)
        assert "sort_by=" in response.text or "sortable: true" in response.text
        # Should have column definitions for sorting
        assert "key: 'n'" in response.text
        assert "key: 'm'" in response.text
        assert "key: 'diameter'" in response.text

    def test_search_preserves_params_in_pagination(self):
        """Pagination links should preserve search params."""
        response = client.get("/search?n=8&m=7&limit=50")
        assert response.status_code == 200
        if "Next" in response.text or "page=2" in response.text:
            assert "n=8" in response.text
            assert "m=7" in response.text

    def test_search_caps_at_1000_results(self):
        """Search should cap results at 1000 and show warning."""
        # Search for all graphs with n=8 (should be >1000 results)
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should show warning banner
        assert "Showing first 1,000" in response.text
        assert "results-cap-warning" in response.text
        assert "For the full dataset, use the" in response.text

        # Should show capped count in pagination
        assert "of 1,000" in response.text or "1-100 of 1,000" in response.text

        # Pagination should be capped to 10 pages (1000 results / 100 per page)
        # Check that we don't show more than 10 pages
        assert "page=11" not in response.text

    def test_search_beyond_cap_redirects_to_page_1(self):
        """Accessing page beyond cap should show page 1."""
        # Try to access page 100 when there are 1000 max results
        response = client.get("/search?n=8&page=100")
        assert response.status_code == 200

        # Should show results range (client-side pagination handles display)
        assert 'class="results-range"' in response.text

    def test_search_count_endpoint(self):
        """Count endpoint should return exact count."""
        response = client.get("/search/count?n=5&m=4")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # Should return a formatted number
        count_text = response.text
        assert count_text.isdigit() or "," in count_text  # May have commas

    def test_search_page_loads_count_async(self):
        """Search page should have HTMX attributes to load count asynchronously."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have HTMX attributes when results are capped
        assert 'hx-get="/search/count' in response.text
        assert 'hx-trigger="load"' in response.text
        assert "1,000+" in response.text

    def test_search_large_results_uses_client_side_sorting(self):
        """Large result sets should embed all data for client-side sorting."""
        # Search for n=8 which has >1000 results
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have Alpine.js data attribute with all results
        assert 'x-data' in response.text
        assert 'allGraphs' in response.text

        # Should have embedded JSON data
        assert 'window.searchData' in response.text or '<script>' in response.text

        # Column headers should have Alpine.js click handlers, not href links
        assert '@click' in response.text or 'x-on:click' in response.text

    def test_search_large_results_embeds_json_data(self):
        """Large result sets should embed all 1000 results as JSON."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have a script tag with data
        assert '<script>' in response.text
        assert 'searchData' in response.text or 'graphs' in response.text

    def test_search_small_results_uses_server_side_pagination(self):
        """Small result sets should use traditional server-side pagination."""
        # Search for n=5&m=4 which has <1000 results
        response = client.get("/search?n=5&m=4")
        assert response.status_code == 200

        # Should use server-side rendering (window.serverGraphs, not window.searchData)
        assert 'window.serverGraphs' in response.text
        assert 'window.searchData' not in response.text

    def test_search_client_side_pagination_markup(self):
        """Large result sets should have Alpine.js pagination controls."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have Alpine.js pagination controls
        assert 'x-data' in response.text


@needs_db
class TestSearchClientSideRegression:
    """Regression tests for client-side sorting and pagination."""

    def test_large_results_always_use_client_side(self):
        """Large result sets (>1000) should always use client-side sorting."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have Alpine.js component
        assert 'x-data' in response.text
        assert 'allGraphs' in response.text
        assert 'sortedGraphs' in response.text
        assert 'paginatedGraphs' in response.text

        # Should embed JSON data
        assert 'window.searchData' in response.text

        # Table headers should use @click, not href
        assert '@click="toggleSort' in response.text

        # Should NOT have server-side pagination links
        assert 'href="/search?' not in response.text or 'page=' not in response.text

    def test_small_results_always_use_server_side(self):
        """Small result sets (<=1000) should use server-side sorting."""
        response = client.get("/search?n=5&m=4")
        assert response.status_code == 200

        # Should use server-side data (window.serverGraphs)
        assert 'window.serverGraphs' in response.text

        # Should NOT have client-side data (window.searchData)
        assert 'window.searchData' not in response.text

    def test_client_side_sorting_all_columns(self):
        """Client-side sorting should handle all sortable columns."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have sortable column definitions
        assert "key: 'graph6', label: 'graph6', sortable: true" in response.text
        assert "key: 'n', label: 'n', sortable: true" in response.text
        assert "key: 'm', label: 'm', sortable: true" in response.text
        assert "key: 'diameter', label: 'Diameter', sortable: true" in response.text
        assert "key: 'girth', label: 'Girth', sortable: true" in response.text

        # Should have toggleSort function
        assert 'toggleSort' in response.text
        # Should have sort indicators
        assert 'sort-indicator' in response.text

    def test_client_side_pagination_controls(self):
        """Client-side pagination should have Previous/Next buttons."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have pagination buttons (not links)
        assert '@click="currentPage' in response.text
        assert 'Previous' in response.text
        assert 'Next' in response.text

        # Should have page number display
        assert 'x-text="p"' in response.text

    def test_client_side_handles_nullable_properties(self):
        """Client-side sorting should handle null diameter/girth."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have null handling in sort logic
        assert '??' in response.text or 'Infinity' in response.text

    def test_client_side_respects_initial_sort(self):
        """Client-side should initialize with requested sort params."""
        response = client.get("/search?n=8&sort_by=m&sort_order=desc")
        assert response.status_code == 200

        # Should initialize Alpine.js with sort params
        assert "sortBy: 'm'" in response.text
        assert "sortOrder: 'desc'" in response.text

    def test_boundary_at_1000_results(self):
        """Exactly 1000 results should trigger client-side mode."""
        # Find a query that returns exactly 1000 results
        # For now, just verify >1000 uses client-side
        response = client.get("/search?n=8")
        assert response.status_code == 200
        assert 'window.searchData' in response.text

    def test_capped_warning_shows_for_large_results(self):
        """Should show warning when results are capped at 1000."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have cap warning
        assert '1,000+' in response.text or '1000+' in response.text
        assert 'first 1,000' in response.text or 'first 1000' in response.text

    def test_all_1000_results_embedded_in_json(self):
        """All 1000 results should be embedded for client-side use."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should have searchData array
        assert 'window.searchData = [' in response.text

        # Should be a large JSON array (rough check)
        assert response.text.count('"graph6"') >= 100

    def test_table_uses_alpine_template(self):
        """Table body should use Alpine.js x-for template."""
        response = client.get("/search?n=8")
        assert response.status_code == 200

        # Should use x-for template for rows
        assert 'x-for="g in paginatedGraphs"' in response.text
        assert ':key="g.graph6"' in response.text

        # Should use x-for template for dynamic columns
        assert 'x-for="col in availableColumns"' in response.text
        # Should use getValue function for accessing column data
        assert 'getValue(g, col.key)' in response.text or "getValue(g, 'n')" in response.text


@needs_db
class TestSearchColumnPicker:
    """Tests for interactive column selection."""

    def test_search_has_column_picker_ui(self):
        """Search page should have column picker button/dropdown."""
        response = client.get("/search?n=5")
        assert response.status_code == 200

        # Should have column picker UI element
        assert 'Columns' in response.text or 'columns' in response.text
        # Should have Alpine.js data for column management
        assert 'availableColumns' in response.text or 'visibleColumns' in response.text

    def test_column_picker_has_all_properties(self):
        """Column picker should list all available numeric properties."""
        response = client.get("/search?n=5")
        assert response.status_code == 200

        # Should have options for numeric properties
        assert 'radius' in response.text.lower()
        assert 'min_degree' in response.text.lower() or 'min degree' in response.text.lower()
        assert 'max_degree' in response.text.lower() or 'max degree' in response.text.lower()
        assert 'triangle' in response.text.lower()

        # Boolean properties should NOT be columns (they're shown as tags)
        assert "key: 'is_bipartite'" not in response.text
        assert "key: 'is_planar'" not in response.text
        assert "key: 'is_regular'" not in response.text

        # Should have getAllTags function that includes boolean properties
        assert 'getAllTags' in response.text
        assert 'is_bipartite' in response.text
        assert "tags.push('bipartite')" in response.text
        assert "tags.push('planar')" in response.text
        assert "tags.push('regular')" in response.text

    def test_default_columns_shown(self):
        """Default columns should be graph6, n, m, tags, diameter, girth."""
        response = client.get("/search?n=5")
        assert response.status_code == 200

        # Should have column definitions in JavaScript
        assert "key: 'graph6'" in response.text
        assert "key: 'n'" in response.text
        assert "key: 'm'" in response.text
        assert "key: 'tags'" in response.text
        assert "key: 'diameter'" in response.text
        assert "key: 'girth'" in response.text

        # Default columns should be marked as default: true
        assert "default: true" in response.text

    def test_boolean_properties_shown_as_tags(self):
        """Boolean properties should appear as tags in the Tags column, not as separate columns."""
        # Get a graph that we know is bipartite, planar, and regular (cycle graph)
        response = client.get("/search?n=5&m=5")
        assert response.status_code == 200

        # The getAllTags function should include these properties
        assert 'getAllTags' in response.text
        assert "tags.push('bipartite')" in response.text
        assert "tags.push('planar')" in response.text
        assert "tags.push('regular')" in response.text


@needs_db
class TestSearchExport:
    def test_export_csv_format(self):
        """Export should support CSV format."""
        response = client.get("/search/export?n=5&m=4&format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert ".csv" in response.headers["Content-Disposition"]

        # Check CSV content
        content = response.text
        assert "graph6,n,m,diameter,girth" in content
        assert "D?{" in content

    def test_export_json_format(self):
        """Export should support JSON format."""
        response = client.get("/search/export?n=5&m=4&format=json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert ".json" in response.headers["Content-Disposition"]

        # Check JSON structure
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "graph6" in data[0]
        assert data[0]["n"] == 5
        assert data[0]["m"] == 4

    def test_export_graph6_format(self):
        """Export should support graph6 list format."""
        response = client.get("/search/export?n=5&m=4&format=graph6")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert ".g6" in response.headers["Content-Disposition"]

        # Check graph6 content (one per line)
        content = response.text
        lines = content.strip().split("\n")
        assert len(lines) > 0
        assert all(len(line.strip()) > 0 for line in lines)
        assert "D?{" in content

    def test_export_respects_filters(self):
        """Export should respect search filters."""
        # Export with specific filters
        response = client.get("/search/export?n=5&m=6&format=json")
        assert response.status_code == 200
        data = response.json()

        # All results should match filters
        for graph in data:
            assert graph["n"] == 5
            assert graph["m"] == 6

    def test_export_default_format_json(self):
        """Export should default to JSON if no format specified."""
        response = client.get("/search/export?n=5&m=4")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert isinstance(data, list)

    def test_export_invalid_format_defaults_to_json(self):
        """Invalid export format should default to JSON."""
        response = client.get("/search/export?n=5&m=4&format=invalid")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_export_empty_results(self):
        """Export with no matches should return empty list/file."""
        response = client.get("/search/export?n=10&m=1&diameter=1&format=json")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_export_csv_with_properties(self):
        """CSV export should include all important properties."""
        response = client.get("/search/export?n=5&m=4&format=csv")
        assert response.status_code == 200
        content = response.text
        lines = content.split("\n")
        headers = lines[0].strip().split(",")

        # Should include key columns
        assert "graph6" in headers
        assert "n" in headers
        assert "m" in headers

    def test_export_respects_limit(self):
        """Export should respect limit parameter."""
        response = client.get("/search/export?n=8&limit=10&format=json")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    def test_export_with_tags(self):
        """Export should work with tags filter."""
        response = client.get("/search/export?n=4&tags=complete&format=json")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # K4 should be in the results
        assert any(g["graph6"] == "C~" for g in data)

    def test_search_page_has_export_ui(self):
        """Search results page should have export UI."""
        response = client.get("/search?n=5&m=4")
        assert response.status_code == 200
        assert "/search/export" in response.text
        assert "format=csv" in response.text
        assert "format=json" in response.text
        assert "format=graph6" in response.text
        # Export buttons should be present
        assert "CSV" in response.text
        assert "JSON" in response.text
        assert "graph6" in response.text


class TestErrorPages:
    @pytest.mark.needs_db
    def test_404_returns_html_for_browser(self):
        """404 errors should return HTML error page for browser requests."""
        response = client.get("/graph/INVALID_GRAPH", headers={"Accept": "text/html"})
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "404" in response.text
        assert "not found" in response.text.lower()
        assert "Back to Search" in response.text

    @pytest.mark.needs_db
    def test_404_returns_json_for_api(self):
        """404 errors should return JSON for API requests."""
        response = client.get("/graph/INVALID_GRAPH")
        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]
        assert "detail" in response.json()

    def test_400_returns_html_for_browser(self):
        """400 errors should return HTML error page for browser requests."""
        response = client.get("/compare?graphs=single", headers={"Accept": "text/html"})
        assert response.status_code == 400
        assert "text/html" in response.headers["content-type"]
        assert "400" in response.text

    def test_400_returns_json_for_api(self):
        """400 errors should return JSON for API requests."""
        response = client.get("/compare?graphs=single")
        assert response.status_code == 400
        assert "application/json" in response.headers["content-type"]


class TestLoadingIndicator:
    def test_base_template_has_loading_indicator(self):
        """Base template should include loading indicator element."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="loading-indicator"' in response.text
        assert "htmx-indicator" in response.text
        assert "Loading..." in response.text

    def test_loading_indicator_hidden_by_default(self):
        """Loading indicator should be hidden by default via htmx-indicator class."""
        response = client.get("/")
        assert response.status_code == 200
        import re
        # htmx-indicator must have display: none
        htmx_ind = re.search(r'\.htmx-indicator\s*\{[^}]*\}', response.text)
        assert htmx_ind, ".htmx-indicator CSS rule must exist"
        assert "display" in htmx_ind.group() and "none" in htmx_ind.group()
        # loading-overlay must NOT set display (would override htmx-indicator)
        overlay = re.search(r'\.loading-overlay\s*\{[^}]*\}', response.text)
        assert overlay, ".loading-overlay CSS rule must exist"
        assert "display" not in overlay.group(), ".loading-overlay must not set display property"

    def test_base_template_has_error_toast(self):
        """Base template should include error toast element."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="error-toast"' in response.text

    def test_htmx_timeout_configured(self):
        """HTMX should be configured with 30s timeout."""
        response = client.get("/")
        assert response.status_code == 200
        assert "htmx.config.timeout = 30000" in response.text

    def test_search_form_uses_regular_submission(self):
        """Search form should use regular form submission (not HTMX)."""
        response = client.get("/")
        assert response.status_code == 200
        # Search form should submit to /search with GET
        assert 'action="/search"' in response.text
        assert 'method="get"' in response.text
        # Should NOT have HTMX on search form
        assert 'hx-get="/graphs"' not in response.text or 'action="/search"' in response.text


class TestAccessibility:
    """Test accessibility features."""

    def test_skip_link_present(self):
        """Page should have skip to main content link."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'href="#main-content"' in response.text
        assert "Skip to main content" in response.text

    def test_main_content_landmark(self):
        """Main element should have proper id and role."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="main-content"' in response.text
        assert 'role="main"' in response.text

    def test_header_landmark(self):
        """Header should have proper role."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'role="banner"' in response.text

    def test_nav_landmark(self):
        """Navigation should have proper role and label."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'role="navigation"' in response.text
        assert 'aria-label="Main navigation"' in response.text

    def test_footer_landmark(self):
        """Footer should have proper role."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'role="contentinfo"' in response.text

    def test_query_tabs_have_aria_attributes(self):
        """Query tabs should have proper ARIA attributes."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'role="tablist"' in response.text
        assert 'aria-label="Query methods"' in response.text
        assert 'role="tab"' in response.text
        assert 'aria-selected' in response.text
        assert 'aria-controls="lookup-panel"' in response.text
        assert 'aria-controls="compare-panel"' in response.text
        assert 'aria-controls="search-panel"' in response.text

    def test_tab_panels_have_aria_attributes(self):
        """Tab panels should have proper ARIA attributes."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'role="tabpanel"' in response.text
        assert 'id="lookup-panel"' in response.text
        assert 'id="compare-panel"' in response.text
        assert 'id="search-panel"' in response.text
        assert 'aria-labelledby="lookup-tab"' in response.text
        assert 'aria-labelledby="compare-tab"' in response.text
        assert 'aria-labelledby="search-tab"' in response.text

    def test_examples_tabs_have_aria_attributes(self):
        """Example category tabs should have proper ARIA attributes."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'aria-label="Example categories"' in response.text
        assert 'aria-controls="examples-panel"' in response.text
        assert 'aria-controls="adjacency-panel"' in response.text

    def test_form_inputs_have_labels(self):
        """Form inputs should have associated labels."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'for="graph6-input"' in response.text
        assert 'id="graph6-input"' in response.text
        assert 'for="compare-graphs-input"' in response.text
        assert 'id="compare-graphs-input"' in response.text

    def test_screen_reader_only_class_defined(self):
        """Screen reader only utility class should be defined."""
        response = client.get("/")
        assert response.status_code == 200
        assert ".sr-only" in response.text

    def test_loading_indicator_has_aria_live(self):
        """Loading indicator should have aria-live region."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'role="status"' in response.text
        assert 'aria-live="polite"' in response.text
        assert 'aria-label="Loading"' in response.text

    def test_error_toast_has_aria_live(self):
        """Error toast should have assertive aria-live region."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'role="alert"' in response.text
        assert 'aria-live="assertive"' in response.text

    def test_results_section_has_aria_live(self):
        """Results section should have polite aria-live region."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="results"' in response.text
        assert 'aria-live="polite"' in response.text

    def test_theme_toggle_has_aria_pressed(self):
        """Theme toggle should have aria-pressed attribute."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'aria-pressed' in response.text
        assert 'id="theme-toggle-btn"' in response.text

    def test_theme_icons_have_aria_hidden(self):
        """Decorative theme icons should be hidden from screen readers."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'aria-hidden="true"' in response.text

    def test_multiselect_has_aria_attributes(self):
        """Multiselect dropdown should have proper ARIA attributes."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'role="button"' in response.text
        assert 'aria-expanded' in response.text
        assert 'role="listbox"' in response.text
        assert 'id="tags-label"' in response.text

    def test_focus_indicators_defined(self):
        """Focus indicators should be defined in CSS."""
        response = client.get("/")
        assert response.status_code == 200
        assert ":focus-visible" in response.text
        assert "outline: 2px solid" in response.text
