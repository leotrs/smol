"""Comprehensive tests for /search API query parameters."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


pytestmark = pytest.mark.needs_db

client = TestClient(app)


class TestBasicQueries:
    """Test basic n and m queries."""

    def test_query_by_n(self):
        """Test filtering by exact n."""
        response = client.get("/search?n=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(g["n"] == 5 for g in data)

    def test_query_by_n_range(self):
        """Test filtering by n range."""
        response = client.get("/search?n_min=4&n_max=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(4 <= g["n"] <= 5 for g in data)

    def test_query_by_m(self):
        """Test filtering by exact m."""
        response = client.get("/search?n=5&m=4")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(g["m"] == 4 for g in data)

    def test_query_by_m_range(self):
        """Test filtering by m range."""
        response = client.get("/search?n=5&m_min=3&m_max=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(3 <= g["m"] <= 5 for g in data)


class TestDegreeQueries:
    """Test degree-based queries."""

    def test_query_by_min_degree(self):
        """Test filtering by min_degree."""
        response = client.get("/search?n=6&min_degree=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(g["min_degree"] == 2 for g in data)

    def test_query_by_max_degree(self):
        """Test filtering by max_degree."""
        response = client.get("/search?n=6&max_degree=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(g["max_degree"] == 3 for g in data)


class TestStructuralQueries:
    """Test structural property queries."""

    def test_query_by_diameter(self):
        """Test filtering by exact diameter."""
        response = client.get("/search?n=6&diameter=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(g["diameter"] == 2 for g in data)

    def test_query_by_diameter_range(self):
        """Test filtering by diameter range."""
        response = client.get("/search?n=6&diameter_min=2&diameter_max=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(2 <= g["diameter"] <= 3 for g in data)

    def test_query_by_radius(self):
        """Test filtering by exact radius."""
        response = client.get("/search?n=6&radius=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(g["radius"] == 2 for g in data)

    def test_query_by_radius_range(self):
        """Test filtering by radius range."""
        response = client.get("/search?n=6&radius_min=1&radius_max=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(1 <= g["radius"] <= 2 for g in data)

    def test_query_by_girth(self):
        """Test filtering by exact girth."""
        response = client.get("/search?n=6&girth=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(g["girth"] == 3 for g in data)

    def test_query_by_girth_range(self):
        """Test filtering by girth range."""
        response = client.get("/search?n=6&girth_min=3&girth_max=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(3 <= g["girth"] <= 5 for g in data if g["girth"] is not None)

    def test_query_by_triangle_count(self):
        """Test filtering by exact triangle count."""
        response = client.get("/search?n=5&triangle_count=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(g["triangle_count"] == 0 for g in data)

    def test_query_by_triangle_count_range(self):
        """Test filtering by triangle count range."""
        response = client.get("/search?n=5&triangle_count_min=1&triangle_count_max=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(1 <= g["triangle_count"] <= 3 for g in data)


class TestBooleanQueries:
    """Test boolean property queries (now via tags)."""

    def test_query_bipartite(self):
        """Test filtering by bipartite tag."""
        response = client.get("/search?n=6&tags=bipartite")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("bipartite" in g.get("tags", []) for g in data)

    def test_query_planar(self):
        """Test filtering by planar tag."""
        response = client.get("/search?n=5&tags=planar")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("planar" in g.get("tags", []) for g in data)

    def test_query_regular(self):
        """Test filtering by regular tag."""
        response = client.get("/search?n=5&tags=regular")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("regular" in g.get("tags", []) for g in data)


class TestTagQueries:
    """Test tag-based queries."""

    def test_query_single_tag(self):
        """Test filtering by single tag."""
        response = client.get("/search?n=5&tags=complete")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("complete" in g.get("tags", []) for g in data)

    def test_query_multiple_tags_or(self):
        """Test filtering by multiple tags with OR."""
        response = client.get("/search?n=6&tags=bipartite&tags=planar&tag_mode=OR")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # At least one tag should match
        assert all(
            "bipartite" in g.get("tags", []) or "planar" in g.get("tags", [])
            for g in data
        )

    def test_query_multiple_tags_and(self):
        """Test filtering by multiple tags with AND."""
        response = client.get("/search?n=6&tags=bipartite&tags=planar&tag_mode=AND")
        assert response.status_code == 200
        data = response.json()
        # All tags should match (or no results)
        if len(data) > 0:
            assert all(
                "bipartite" in g.get("tags", []) and "planar" in g.get("tags", [])
                for g in data
            )


class TestCospectralQueries:
    """Test cospectral mate queries."""

    def test_query_has_cospectral_mate_adj(self):
        """Test filtering by adjacency cospectral mates."""
        response = client.get("/search?n=8&has_cospectral_mate=adj&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_query_has_cospectral_mate_kirchhoff(self):
        """Test filtering by kirchhoff cospectral mates."""
        response = client.get("/search?n=8&has_cospectral_mate=kirchhoff&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_query_no_cospectral_mates(self):
        """Test filtering graphs with no cospectral mates."""
        response = client.get("/search?n=5&has_cospectral_mate=none&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0


class TestMechanismQueries:
    """Test switching mechanism queries."""

    def test_query_gm_mechanism(self):
        """Test filtering by GM switching mechanism."""
        response = client.get("/search?n=8&has_mechanism=gm&limit=10")
        assert response.status_code == 200
        data = response.json()
        # May or may not have results depending on data
        assert response.status_code == 200

    def test_query_any_mechanism(self):
        """Test filtering graphs with any mechanism."""
        response = client.get("/search?n=8&has_mechanism=any&limit=10")
        assert response.status_code == 200
        data = response.json()
        # May or may not have results
        assert response.status_code == 200

    def test_query_no_mechanism(self):
        """Test filtering graphs with no known mechanism."""
        response = client.get("/search?n=8&has_mechanism=none&limit=10")
        assert response.status_code == 200
        data = response.json()
        # May or may not have results
        assert response.status_code == 200


class TestCombinedQueries:
    """Test combinations of query parameters."""

    def test_combined_n_m_diameter(self):
        """Test combining n, m, and diameter filters."""
        response = client.get("/search?n=6&m_min=7&diameter=2")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            assert all(g["n"] == 6 and g["m"] >= 7 and g["diameter"] == 2 for g in data)

    def test_combined_tags_and_properties(self):
        """Test combining tags with numeric properties."""
        response = client.get("/search?n=6&tags=bipartite&diameter_max=3")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            assert all(
                g["n"] == 6
                and "bipartite" in g.get("tags", [])
                and g["diameter"] <= 3
                for g in data
            )

    def test_combined_cospectral_and_structure(self):
        """Test combining cospectral filter with structural properties."""
        response = client.get("/search?n=8&has_cospectral_mate=adj&tags=regular&limit=10")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            assert all(g["n"] == 8 and "regular" in g.get("tags", []) for g in data)


class TestPagination:
    """Test pagination parameters."""

    def test_limit(self):
        """Test limit parameter."""
        response = client.get("/search?n=5&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_offset(self):
        """Test offset parameter."""
        response1 = client.get("/search?n=5&limit=5&offset=0")
        response2 = client.get("/search?n=5&limit=5&offset=5")
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        # Results should be different (non-overlapping pages)
        if len(data1) > 0 and len(data2) > 0:
            graph6_set1 = {g["graph6"] for g in data1}
            graph6_set2 = {g["graph6"] for g in data2}
            assert graph6_set1.isdisjoint(graph6_set2)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_n(self):
        """Test with invalid n value."""
        response = client.get("/search?n=invalid")
        # Should handle gracefully
        assert response.status_code in [200, 422]

    def test_empty_result(self):
        """Test query that returns no results."""
        response = client.get("/search?n=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_contradictory_filters(self):
        """Test contradictory filters."""
        response = client.get("/search?n_min=8&n_max=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestHTMLResponse:
    """Test HTML response for browser requests."""

    def test_html_response(self):
        """Test that HTML is returned with Accept: text/html."""
        response = client.get(
            "/search?n=5&limit=5",
            headers={"Accept": "text/html"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
