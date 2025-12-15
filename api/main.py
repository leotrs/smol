"""SMOL API - Spectral graph database."""

import logging
import time
from pathlib import Path

import networkx as nx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import (
    fetch_cospectral_mates,
    fetch_graph,
    fetch_random_cospectral_class,
    fetch_random_graph,
    fetch_similar_graphs,
    get_stats,
    query_graphs,
)
from .models import (
    CospectralMates,
    GraphFull,
    GraphProperties,
    GraphSummary,
    Spectra,
    Stats,
    CompareResult,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("smol")

app = FastAPI(
    title="SMOL",
    description="Spectra and Matrices Of Little graphs",
    version="0.1.0",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    if not request.url.path.startswith("/static"):
        logger.info(f"{request.method} {request.url.path} {response.status_code} {elapsed*1000:.0f}ms")
    return response


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def wants_html(request: Request) -> bool:
    """Check if request wants HTML (browser or HTMX) vs JSON (API)."""
    if request.headers.get("hx-request"):
        return True
    accept = request.headers.get("accept", "")
    return "text/html" in accept and "application/json" not in accept


def row_to_graph_full(row: dict, mates: dict[str, list[str]]) -> GraphFull:
    G = nx.from_graph6_bytes(row["graph6"].encode())
    edges = [tuple(sorted(e)) for e in G.edges()]
    return GraphFull(
        graph6=row["graph6"],
        n=row["n"],
        m=row["m"],
        edges=edges,
        properties=GraphProperties(
            is_bipartite=row["is_bipartite"],
            is_planar=row["is_planar"],
            is_regular=row["is_regular"],
            diameter=row["diameter"],
            girth=row["girth"],
            radius=row["radius"],
            min_degree=row["min_degree"],
            max_degree=row["max_degree"],
            triangle_count=row["triangle_count"],
            clique_number=row.get("clique_number"),
            chromatic_number=row.get("chromatic_number"),
            algebraic_connectivity=row.get("algebraic_connectivity"),
            global_clustering=row.get("global_clustering"),
            avg_local_clustering=row.get("avg_local_clustering"),
            avg_path_length=row.get("avg_path_length"),
            assortativity=row.get("assortativity"),
            degree_sequence=row.get("degree_sequence"),
            betweenness_centrality=row.get("betweenness_centrality"),
            closeness_centrality=row.get("closeness_centrality"),
            eigenvector_centrality=row.get("eigenvector_centrality"),
        ),
        spectra=Spectra(
            adj_eigenvalues=row["adj_eigenvalues"],
            adj_hash=row["adj_spectral_hash"],
            lap_eigenvalues=row["lap_eigenvalues"],
            lap_hash=row["lap_spectral_hash"],
            nb_eigenvalues_re=row["nb_eigenvalues_re"],
            nb_eigenvalues_im=row["nb_eigenvalues_im"],
            nb_hash=row["nb_spectral_hash"],
            nbl_eigenvalues_re=row["nbl_eigenvalues_re"],
            nbl_eigenvalues_im=row["nbl_eigenvalues_im"],
            nbl_hash=row["nbl_spectral_hash"],
        ),
        cospectral_mates=CospectralMates(**mates),
        tags=row.get("tags") or [],
    )


def row_to_graph_summary(row: dict) -> GraphSummary:
    return GraphSummary(
        graph6=row["graph6"],
        n=row["n"],
        m=row["m"],
        properties=GraphProperties(
            is_bipartite=row["is_bipartite"],
            is_planar=row["is_planar"],
            is_regular=row["is_regular"],
            diameter=row["diameter"],
            girth=row["girth"],
            radius=row["radius"],
            min_degree=row["min_degree"],
            max_degree=row["max_degree"],
            triangle_count=row["triangle_count"],
            clique_number=row.get("clique_number"),
            chromatic_number=row.get("chromatic_number"),
            algebraic_connectivity=row.get("algebraic_connectivity"),
            global_clustering=row.get("global_clustering"),
            avg_local_clustering=row.get("avg_local_clustering"),
            avg_path_length=row.get("avg_path_length"),
            assortativity=row.get("assortativity"),
            degree_sequence=row.get("degree_sequence"),
            betweenness_centrality=row.get("betweenness_centrality"),
            closeness_centrality=row.get("closeness_centrality"),
            eigenvector_centrality=row.get("eigenvector_centrality"),
        ),
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with search."""
    return templates.TemplateResponse(request, "home.html")


@app.get("/graph/{graph6}")
async def get_graph_by_id(graph6: str, request: Request):
    """Look up a graph by its graph6 string."""
    t0 = time.perf_counter()

    row = await fetch_graph(graph6)
    t1 = time.perf_counter()
    logger.info(f"  fetch_graph: {(t1-t0)*1000:.0f}ms")

    if not row:
        raise HTTPException(status_code=404, detail=f"Graph '{graph6}' not found")

    hashes = {
        "adj": row["adj_spectral_hash"],
        "lap": row["lap_spectral_hash"],
        "nb": row["nb_spectral_hash"],
        "nbl": row["nbl_spectral_hash"],
    }
    mates = await fetch_cospectral_mates(graph6, row["n"], hashes)
    t2 = time.perf_counter()
    logger.info(f"  fetch_cospectral_mates: {(t2-t1)*1000:.0f}ms")

    graph = row_to_graph_full(row, mates)
    t3 = time.perf_counter()
    logger.info(f"  row_to_graph_full: {(t3-t2)*1000:.0f}ms")

    if wants_html(request):
        resp = templates.TemplateResponse(
            request, "graph_detail.html", {"graph": graph}
        )
        t4 = time.perf_counter()
        logger.info(f"  template render: {(t4-t3)*1000:.0f}ms")
        return resp
    return graph


@app.get("/random")
async def random_graph():
    """Redirect to a random graph."""
    from fastapi.responses import RedirectResponse
    from urllib.parse import quote

    row = await fetch_random_graph()
    if not row:
        raise HTTPException(status_code=404, detail="No graphs in database")
    return RedirectResponse(url=f"/graph/{quote(row['graph6'], safe='')}", status_code=302)


@app.get("/random/cospectral")
async def random_cospectral(matrix: str = "adj"):
    """Redirect to compare page with a random cospectral class."""
    from fastapi.responses import RedirectResponse
    from urllib.parse import quote

    if matrix not in ("adj", "lap", "nb", "nbl"):
        raise HTTPException(status_code=400, detail="Invalid matrix type")

    graphs = await fetch_random_cospectral_class(matrix)
    if not graphs:
        raise HTTPException(status_code=404, detail="No cospectral pairs found")

    graphs_param = ",".join(quote(g, safe="") for g in graphs)
    return RedirectResponse(url=f"/compare?graphs={graphs_param}", status_code=302)


@app.get("/graphs")
async def list_graphs(
    request: Request,
    graph6: str | None = None,
    n: str | None = None,
    n_min: str | None = None,
    n_max: str | None = None,
    m: str | None = None,
    m_min: str | None = None,
    m_max: str | None = None,
    bipartite: str | None = None,
    planar: str | None = None,
    regular: str | None = None,
    connected: bool = True,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
):
    """Query graphs with filters."""
    n = int(n) if n else None
    n_min = int(n_min) if n_min else None
    n_max = int(n_max) if n_max else None
    m = int(m) if m else None
    m_min = int(m_min) if m_min else None
    m_max = int(m_max) if m_max else None
    bipartite = bipartite == "true" if bipartite else None
    planar = planar == "true" if planar else None
    regular = regular == "true" if regular else None

    if graph6:
        row = await fetch_graph(graph6)
        if not row:
            if wants_html(request):
                return templates.TemplateResponse(
                    request, "graph_list.html", {"graphs": []}
                )
            return []
        hashes = {
            "adj": row["adj_spectral_hash"],
            "lap": row["lap_spectral_hash"],
            "nb": row["nb_spectral_hash"],
            "nbl": row["nbl_spectral_hash"],
        }
        mates = await fetch_cospectral_mates(graph6, row["n"], hashes)
        graph = row_to_graph_full(row, mates)
        if wants_html(request):
            return templates.TemplateResponse(
                request, "graph_detail.html", {"graph": graph}
            )
        return [graph]

    rows = await query_graphs(
        n=n,
        n_min=n_min,
        n_max=n_max,
        m=m,
        m_min=m_min,
        m_max=m_max,
        bipartite=bipartite,
        planar=planar,
        regular=regular,
        connected=connected,
        limit=limit,
        offset=offset,
    )
    graphs = [row_to_graph_summary(row) for row in rows]

    if wants_html(request):
        return templates.TemplateResponse(
            request, "graph_list.html", {"graphs": graphs}
        )
    return graphs


@app.get("/compare")
async def compare_graphs(
    request: Request,
    graphs: str = Query(..., description="Comma-separated graph6 strings"),
):
    """Compare multiple graphs side-by-side."""
    graph6_list = [g.strip() for g in graphs.split(",")]
    if len(graph6_list) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 graphs to compare")
    if len(graph6_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 graphs per comparison")

    full_graphs = []
    all_hashes = {"adj": set(), "lap": set(), "nb": set(), "nbl": set()}

    for g6 in graph6_list:
        row = await fetch_graph(g6)
        if not row:
            raise HTTPException(status_code=404, detail=f"Graph '{g6}' not found")

        hashes = {
            "adj": row["adj_spectral_hash"],
            "lap": row["lap_spectral_hash"],
            "nb": row["nb_spectral_hash"],
            "nbl": row["nbl_spectral_hash"],
        }
        for matrix, h in hashes.items():
            all_hashes[matrix].add(h)

        mates = await fetch_cospectral_mates(g6, row["n"], hashes)
        full_graphs.append(row_to_graph_full(row, mates))

    comparison = {
        matrix: "same" if len(hashes) == 1 else "different"
        for matrix, hashes in all_hashes.items()
    }

    result = CompareResult(graphs=full_graphs, spectral_comparison=comparison)

    if wants_html(request):
        prop_diffs = {
            "n": len(set(g.n for g in full_graphs)) > 1,
            "m": len(set(g.m for g in full_graphs)) > 1,
            "is_bipartite": len(set(g.properties.is_bipartite for g in full_graphs)) > 1,
            "is_planar": len(set(g.properties.is_planar for g in full_graphs)) > 1,
            "is_regular": len(set(g.properties.is_regular for g in full_graphs)) > 1,
            "diameter": len(set(g.properties.diameter for g in full_graphs)) > 1,
            "girth": len(set(g.properties.girth for g in full_graphs)) > 1,
            "triangle_count": len(set(g.properties.triangle_count for g in full_graphs)) > 1,
            "clique_number": len(set(g.properties.clique_number for g in full_graphs)) > 1,
            "chromatic_number": len(set(g.properties.chromatic_number for g in full_graphs)) > 1,
            "algebraic_connectivity": len(set(g.properties.algebraic_connectivity for g in full_graphs)) > 1,
            "global_clustering": len(set(g.properties.global_clustering for g in full_graphs)) > 1,
            "avg_local_clustering": len(set(g.properties.avg_local_clustering for g in full_graphs)) > 1,
            "avg_path_length": len(set(g.properties.avg_path_length for g in full_graphs)) > 1,
            "assortativity": len(set(g.properties.assortativity for g in full_graphs)) > 1,
        }
        return templates.TemplateResponse(
            request, "compare.html", {"result": result.model_dump(), "prop_diffs": prop_diffs}
        )
    return result


@app.get("/glossary", response_class=HTMLResponse)
async def glossary(request: Request):
    """Terminology glossary."""
    return templates.TemplateResponse(request, "glossary.html")


@app.get("/about")
async def about(request: Request):
    """About page with statistics."""
    data = await get_stats()
    stats = Stats(**data)

    if wants_html(request):
        return templates.TemplateResponse(
            request, "about.html", {"stats": stats}
        )
    return stats


@app.get("/stats")
async def stats(request: Request):
    """Get database statistics (API)."""
    data = await get_stats()
    result = Stats(**data)

    if wants_html(request):
        return templates.TemplateResponse(
            request, "about.html", {"stats": result}
        )
    return result


@app.get("/similar/{graph6}")
async def similar_graphs(
    graph6: str,
    request: Request,
    matrix: str = Query(default="adj", description="Matrix type: adj, lap, nb, nbl"),
    limit: int = Query(default=10, le=50),
):
    """Find graphs with similar spectrum (by L2 distance)."""
    if matrix not in ("adj", "lap", "nb", "nbl"):
        raise HTTPException(status_code=400, detail="Invalid matrix type")

    results = await fetch_similar_graphs(graph6, matrix=matrix, limit=limit)

    if not results:
        raise HTTPException(status_code=404, detail=f"Graph '{graph6}' not found or no similar graphs")

    similar = [
        {
            "graph": row_to_graph_summary(row),
            "distance": round(dist, 6),
        }
        for row, dist in results
    ]

    if wants_html(request):
        return templates.TemplateResponse(
            request, "similar.html", {"source_graph6": graph6, "matrix": matrix, "results": similar}
        )
    return similar
