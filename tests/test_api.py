"""Tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


class TestHomeEndpoint:
    def test_home_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "SMOL" in response.text
        assert "Search" in response.text


class TestGraphEndpoint:
    def test_graph_returns_json_by_default(self):
        response = client.get("/graph/D%3F%7B")  # D?{
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert data["graph6"] == "D?{"
        assert data["n"] == 5
        assert data["m"] == 4
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
