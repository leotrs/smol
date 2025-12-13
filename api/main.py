"""SMOL API - Spectral graph database."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .database import fetch_cospectral_mates, fetch_graph, get_stats, query_graphs
from .models import (
    CospectralMates,
    GraphFull,
    GraphProperties,
    GraphSummary,
    Spectra,
    Stats,
    CompareResult,
)

app = FastAPI(
    title="SMOL",
    description="Spectra and Matrices Of Little graphs",
    version="0.1.0",
)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept and "application/json" not in accept


def row_to_graph_full(row: dict, mates: dict[str, list[str]]) -> GraphFull:
    return GraphFull(
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
        ),
    )


@app.get("/graphs/{graph6}")
async def get_graph_by_id(graph6: str, request: Request):
    """Look up a graph by its graph6 string."""
    row = fetch_graph(graph6)
    if not row:
        raise HTTPException(status_code=404, detail=f"Graph '{graph6}' not found")

    hashes = {
        "adj": row["adj_spectral_hash"],
        "lap": row["lap_spectral_hash"],
        "nb": row["nb_spectral_hash"],
        "nbl": row["nbl_spectral_hash"],
    }
    mates = fetch_cospectral_mates(graph6, row["n"], hashes)
    graph = row_to_graph_full(row, mates)

    if wants_html(request):
        return templates.TemplateResponse(
            "graph_detail.html", {"request": request, "graph": graph}
        )
    return graph


@app.get("/graphs")
async def list_graphs(
    request: Request,
    n: int | None = None,
    n_min: int | None = None,
    n_max: int | None = None,
    m: int | None = None,
    m_min: int | None = None,
    m_max: int | None = None,
    bipartite: bool | None = None,
    planar: bool | None = None,
    regular: bool | None = None,
    connected: bool = True,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
):
    """Query graphs with filters."""
    rows = query_graphs(
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
            "graph_list.html", {"request": request, "graphs": graphs}
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
        row = fetch_graph(g6)
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

        mates = fetch_cospectral_mates(g6, row["n"], hashes)
        full_graphs.append(row_to_graph_full(row, mates))

    comparison = {
        matrix: "same" if len(hashes) == 1 else "different"
        for matrix, hashes in all_hashes.items()
    }

    result = CompareResult(graphs=full_graphs, spectral_comparison=comparison)

    if wants_html(request):
        return templates.TemplateResponse(
            "compare.html", {"request": request, "result": result}
        )
    return result


@app.get("/stats")
async def stats(request: Request):
    """Get database statistics."""
    data = get_stats()
    result = Stats(**data)

    if wants_html(request):
        return templates.TemplateResponse(
            "stats.html", {"request": request, "stats": result}
        )
    return result
