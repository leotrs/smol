"""SMOL API - Spectral graph database."""

import csv
import io
import logging
import time
from pathlib import Path

import networkx as nx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import (
    fetch_cospectral_mates,
    fetch_graph,
    fetch_graph_mechanisms,
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
from .routes import mechanisms

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

# Include routers
app.include_router(mechanisms.router)


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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Render HTML error pages for browser requests."""
    if wants_html(request):
        error_messages = {
            404: "The graph or page you're looking for doesn't exist.",
            400: "The request was invalid or malformed.",
            500: "Something went wrong on our end.",
            408: "The request took too long to process.",
        }
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "code": exc.status_code,
                "title": exc.detail or "Error",
                "message": error_messages.get(exc.status_code, "An error occurred."),
            },
            status_code=exc.status_code,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


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
            kirchhoff_eigenvalues=row["kirchhoff_eigenvalues"] or [],
            kirchhoff_hash=row["kirchhoff_spectral_hash"] or "",
            signless_eigenvalues=row["signless_eigenvalues"] or [],
            signless_hash=row["signless_spectral_hash"] or "",
            lap_eigenvalues=row["lap_eigenvalues"],
            lap_hash=row["lap_spectral_hash"],
            nb_eigenvalues_re=row["nb_eigenvalues_re"],
            nb_eigenvalues_im=row["nb_eigenvalues_im"],
            nb_hash=row["nb_spectral_hash"],
            nbl_eigenvalues_re=row["nbl_eigenvalues_re"],
            nbl_eigenvalues_im=row["nbl_eigenvalues_im"],
            nbl_hash=row["nbl_spectral_hash"],
            dist_eigenvalues=row["dist_eigenvalues"],
            dist_hash=row["dist_spectral_hash"],
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
        tags=row.get("tags", []) or [],
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
        "kirchhoff": row["kirchhoff_spectral_hash"] or "",
        "signless": row["signless_spectral_hash"] or "",
        "lap": row["lap_spectral_hash"],
        "nb": row["nb_spectral_hash"],
        "nbl": row["nbl_spectral_hash"],
    }
    mates = await fetch_cospectral_mates(graph6, row["n"], hashes)
    t2 = time.perf_counter()
    logger.info(f"  fetch_cospectral_mates: {(t2-t1)*1000:.0f}ms")

    mechanisms_data = await fetch_graph_mechanisms(graph6)
    t2_5 = time.perf_counter()
    logger.info(f"  fetch_graph_mechanisms: {(t2_5-t2)*1000:.0f}ms")

    graph = row_to_graph_full(row, mates)
    t3 = time.perf_counter()
    logger.info(f"  row_to_graph_full: {(t3-t2_5)*1000:.0f}ms")

    if wants_html(request):
        resp = templates.TemplateResponse(
            request, "graph_detail.html", {"graph": graph, "mechanisms": mechanisms_data}
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
async def random_cospectral(matrix: str | None = None):
    """Redirect to compare page with a random cospectral class.

    If no matrix is specified, uniformly samples a matrix type first,
    then samples a random cospectral family for that matrix.
    """
    import random
    from fastapi.responses import RedirectResponse
    from urllib.parse import quote

    # If no matrix specified, choose one uniformly at random
    if matrix is None:
        matrix = random.choice(["adj", "kirchhoff", "signless", "lap", "nb", "nbl", "dist"])
    elif matrix not in ("adj", "kirchhoff", "signless", "lap", "nb", "nbl", "dist"):
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
            "kirchhoff": row["kirchhoff_spectral_hash"] or "",
            "signless": row["signless_spectral_hash"] or "",
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

    # Cap count check at 10k for API performance
    # API consumers can paginate through results or use export
    MAX_COUNT = 10000

    rows, total_count = await query_graphs(
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
        max_count=MAX_COUNT,
    )
    graphs = [row_to_graph_summary(row) for row in rows]

    if wants_html(request):
        return templates.TemplateResponse(
            request, "graph_list.html", {"graphs": graphs}
        )
    return graphs


@app.get("/search")
async def search_graphs(
    request: Request,
    n: str | None = None,
    m: str | None = None,
    min_degree: str | None = None,
    max_degree: str | None = None,
    diameter: str | None = None,
    radius: str | None = None,
    girth: str | None = None,
    triangle_count: str | None = None,
    bipartite: str | None = None,
    planar: str | None = None,
    regular: str | None = None,
    tags: list[str] = Query(default=[]),
    has_mechanism: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, le=1000),
    sort_by: str = Query(default="n"),
    sort_order: str = Query(default="asc"),
):
    """Search graphs with filters - returns HTML page with results."""
    # Parse params
    n_val = int(n) if n else None
    m_val = int(m) if m else None
    min_degree_val = int(min_degree) if min_degree else None
    max_degree_val = int(max_degree) if max_degree else None
    diameter_val = int(diameter) if diameter else None
    radius_val = int(radius) if radius else None
    girth_val = int(girth) if girth else None
    triangle_count_val = int(triangle_count) if triangle_count else None
    bipartite_val = bipartite == "true" if bipartite else None
    planar_val = planar == "true" if planar else None
    regular_val = regular == "true" if regular else None

    # Cap results at 1000 to keep site responsive
    MAX_RESULTS = 1000

    # First, get the total count to check if we need to cap
    offset = (page - 1) * limit

    # Prevent accessing beyond the cap
    if offset >= MAX_RESULTS:
        offset = 0
        page = 1

    # Check if we'll need to cap results (fast count up to 1001)
    _, estimated_count = await query_graphs(
        n=n_val,
        m=m_val,
        min_degree=min_degree_val,
        max_degree=max_degree_val,
        diameter=diameter_val,
        radius=radius_val,
        girth=girth_val,
        triangle_count=triangle_count_val,
        bipartite=bipartite_val,
        planar=planar_val,
        regular=regular_val,
        tags=tags if tags else None,
        has_mechanism=has_mechanism,
        connected=True,
        limit=0,
        offset=0,
        max_count=MAX_RESULTS,
    )

    # Check if results are capped
    results_capped = estimated_count > MAX_RESULTS

    if results_capped:
        # For large result sets: fetch all 1000 results for client-side sorting/pagination
        rows, total_count = await query_graphs(
            n=n_val,
            m=m_val,
            min_degree=min_degree_val,
            max_degree=max_degree_val,
            diameter=diameter_val,
            radius=radius_val,
            girth=girth_val,
            triangle_count=triangle_count_val,
            bipartite=bipartite_val,
            planar=planar_val,
            regular=regular_val,
            tags=tags if tags else None,
            has_mechanism=has_mechanism,
            connected=True,
            limit=MAX_RESULTS,
            offset=0,
            sort_by="n",  # Use fast indexed order
            sort_order="asc",
            max_count=MAX_RESULTS,
        )

        # Convert ALL results to graph objects for client-side use
        graph_objects = [row_to_graph_summary(row) for row in rows]
        graphs = graph_objects  # Pass all to template for server-side display
        all_graphs = [g.model_dump() for g in graph_objects]  # Convert to dicts for JSON
    else:
        # For small result sets: use SQL ORDER BY (normal server-side pagination)
        rows, total_count = await query_graphs(
            n=n_val,
            m=m_val,
            min_degree=min_degree_val,
            max_degree=max_degree_val,
            diameter=diameter_val,
            radius=radius_val,
            girth=girth_val,
            triangle_count=triangle_count_val,
            bipartite=bipartite_val,
            planar=planar_val,
            regular=regular_val,
            tags=tags if tags else None,
            has_mechanism=has_mechanism,
            connected=True,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            max_count=MAX_RESULTS,
        )
        graph_objects = [row_to_graph_summary(row) for row in rows]
        graphs = [g.model_dump() for g in graph_objects]  # Convert to dicts for JSON
        all_graphs = None  # Not needed for server-side pagination

    display_count = min(total_count, MAX_RESULTS)

    # Build query params for API call display and pagination
    query_params = {}
    if n:
        query_params["n"] = n
    if m:
        query_params["m"] = m
    if min_degree:
        query_params["min_degree"] = min_degree
    if max_degree:
        query_params["max_degree"] = max_degree
    if diameter:
        query_params["diameter"] = diameter
    if radius:
        query_params["radius"] = radius
    if girth:
        query_params["girth"] = girth
    if triangle_count:
        query_params["triangle_count"] = triangle_count
    if bipartite:
        query_params["bipartite"] = bipartite
    if planar:
        query_params["planar"] = planar
    if regular:
        query_params["regular"] = regular
    for tag in tags:
        query_params.setdefault("tags", []).append(tag) if isinstance(query_params.get("tags"), list) else query_params.update({"tags": [tag]})
    if has_mechanism:
        query_params["has_mechanism"] = has_mechanism

    # Pagination info - use capped count for pagination
    total_pages = (display_count + limit - 1) // limit
    has_prev = page > 1
    has_next = page < total_pages
    start_idx = offset + 1 if display_count > 0 else 0
    end_idx = min(offset + limit, display_count)

    return templates.TemplateResponse(
        request,
        "search_results.html",
        {
            "graphs": graphs,
            "all_graphs": all_graphs,  # All 1000 for client-side sorting when capped
            "total_count": total_count,
            "results_capped": results_capped,
            "display_count": display_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "start_idx": start_idx,
            "end_idx": end_idx,
            "query_params": query_params,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    )


@app.get("/search/count")
async def search_count(
    n: str | None = None,
    m: str | None = None,
    min_degree: str | None = None,
    max_degree: str | None = None,
    diameter: str | None = None,
    radius: str | None = None,
    girth: str | None = None,
    triangle_count: str | None = None,
    bipartite: str | None = None,
    planar: str | None = None,
    regular: str | None = None,
    tags: list[str] = Query(default=[]),
    has_mechanism: str | None = None,
):
    """Get exact count of search results (async endpoint for updating UI)."""
    # Parse params
    n_val = int(n) if n else None
    m_val = int(m) if m else None
    min_degree_val = int(min_degree) if min_degree else None
    max_degree_val = int(max_degree) if max_degree else None
    diameter_val = int(diameter) if diameter else None
    radius_val = int(radius) if radius else None
    girth_val = int(girth) if girth else None
    triangle_count_val = int(triangle_count) if triangle_count else None
    bipartite_val = bipartite == "true" if bipartite else None
    planar_val = planar == "true" if planar else None
    regular_val = regular == "true" if regular else None

    # Get exact count without limit
    _, total_count = await query_graphs(
        n=n_val,
        m=m_val,
        min_degree=min_degree_val,
        max_degree=max_degree_val,
        diameter=diameter_val,
        radius=radius_val,
        girth=girth_val,
        triangle_count=triangle_count_val,
        bipartite=bipartite_val,
        planar=planar_val,
        regular=regular_val,
        tags=tags if tags else None,
        has_mechanism=has_mechanism,
        connected=True,
        limit=0,
        offset=0,
    )

    # Return just the formatted count text
    return Response(
        content=f'{"{:,}".format(total_count)}',
        media_type="text/plain",
    )


@app.get("/search/export")
async def export_search_results(
    n: str | None = None,
    m: str | None = None,
    min_degree: str | None = None,
    max_degree: str | None = None,
    diameter: str | None = None,
    radius: str | None = None,
    girth: str | None = None,
    triangle_count: str | None = None,
    bipartite: str | None = None,
    planar: str | None = None,
    regular: str | None = None,
    tags: list[str] = Query(default=[]),
    limit: int = Query(default=1000, le=10000),
    format: str = Query(default="json"),
    sort_by: str = Query(default="n"),
    sort_order: str = Query(default="asc"),
):
    """Export search results in CSV, JSON, or graph6 format."""
    # Parse params (same as search endpoint)
    n_val = int(n) if n else None
    m_val = int(m) if m else None
    min_degree_val = int(min_degree) if min_degree else None
    max_degree_val = int(max_degree) if max_degree else None
    diameter_val = int(diameter) if diameter else None
    radius_val = int(radius) if radius else None
    girth_val = int(girth) if girth else None
    triangle_count_val = int(triangle_count) if triangle_count else None
    bipartite_val = bipartite == "true" if bipartite else None
    planar_val = planar == "true" if planar else None
    regular_val = regular == "true" if regular else None

    rows, total_count = await query_graphs(
        n=n_val,
        m=m_val,
        min_degree=min_degree_val,
        max_degree=max_degree_val,
        diameter=diameter_val,
        radius=radius_val,
        girth=girth_val,
        triangle_count=triangle_count_val,
        bipartite=bipartite_val,
        planar=planar_val,
        regular=regular_val,
        tags=tags if tags else None,
        connected=True,
        limit=limit,
        offset=0,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    graphs = [row_to_graph_summary(row) for row in rows]

    # Export based on format
    format_lower = format.lower()

    if format_lower == "csv":
        # CSV export
        output = io.StringIO()
        if graphs:
            # Get all keys from first graph
            fieldnames = [
                "graph6",
                "n",
                "m",
                "diameter",
                "girth",
                "radius",
                "min_degree",
                "max_degree",
                "triangle_count",
                "is_bipartite",
                "is_planar",
                "is_regular",
                "tags",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for graph in graphs:
                row_data = {
                    "graph6": graph.graph6,
                    "n": graph.n,
                    "m": graph.m,
                    "diameter": graph.properties.diameter if graph.properties else None,
                    "girth": graph.properties.girth if graph.properties else None,
                    "radius": graph.properties.radius if graph.properties else None,
                    "min_degree": graph.properties.min_degree if graph.properties else None,
                    "max_degree": graph.properties.max_degree if graph.properties else None,
                    "triangle_count": graph.properties.triangle_count if graph.properties else None,
                    "is_bipartite": graph.properties.is_bipartite if graph.properties else None,
                    "is_planar": graph.properties.is_planar if graph.properties else None,
                    "is_regular": graph.properties.is_regular if graph.properties else None,
                    "tags": ",".join(graph.tags) if graph.tags else "",
                }
                writer.writerow(row_data)

        content = output.getvalue()
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=graphs.csv"},
        )

    elif format_lower == "graph6":
        # graph6 list export (one per line)
        lines = [graph.graph6 for graph in graphs]
        content = "\n".join(lines)
        if content:
            content += "\n"

        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=graphs.g6"},
        )

    else:
        # JSON export (default)
        data = [graph.model_dump() for graph in graphs]
        return JSONResponse(
            content=data,
            headers={"Content-Disposition": "attachment; filename=graphs.json"},
        )


@app.get("/compare")
async def compare_graphs(
    request: Request,
    graphs: str = Query(..., description="Comma-separated graph6 strings"),
):
    """Compare multiple graphs side-by-side."""
    t0 = time.perf_counter()

    graph6_list = [g.strip() for g in graphs.split(",")]
    if len(graph6_list) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 graphs to compare")
    if len(graph6_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 graphs per comparison")

    full_graphs = []
    all_hashes = {"adj": set(), "kirchhoff": set(), "signless": set(), "lap": set(), "nb": set(), "nbl": set(), "dist": set()}

    for g6 in graph6_list:
        row = await fetch_graph(g6)
        if not row:
            raise HTTPException(status_code=404, detail=f"Graph '{g6}' not found")

        hashes = {
            "adj": row["adj_spectral_hash"],
            "kirchhoff": row["kirchhoff_spectral_hash"] or "",
            "signless": row["signless_spectral_hash"] or "",
            "lap": row["lap_spectral_hash"],
            "nb": row["nb_spectral_hash"],
            "nbl": row["nbl_spectral_hash"],
            "dist": row["dist_spectral_hash"] or "",
        }
        for matrix, h in hashes.items():
            all_hashes[matrix].add(h)

        mates = await fetch_cospectral_mates(g6, row["n"], hashes)
        full_graphs.append(row_to_graph_full(row, mates))

    logger.info(f"  compare fetch {len(graph6_list)} graphs: {(time.perf_counter()-t0)*1000:.0f}ms")

    # Compute spectral distances
    distance_matrix_data = None
    if len(graph6_list) == 2:
        import numpy as np
        from scipy.stats import wasserstein_distance
        import ot

        g1_row = await fetch_graph(graph6_list[0])
        g2_row = await fetch_graph(graph6_list[1])

        comparison = {}
        for matrix in ["adj", "kirchhoff", "signless", "lap", "nb", "nbl", "dist"]:
            if matrix in ("adj", "kirchhoff", "signless", "lap", "dist"):
                # 1D Wasserstein for real eigenvalues
                eigs1 = g1_row[f"{matrix}_eigenvalues"]
                eigs2 = g2_row[f"{matrix}_eigenvalues"]
                if eigs1 is not None and eigs2 is not None and len(eigs1) == len(eigs2):
                    dist = wasserstein_distance(eigs1, eigs2)
                    if dist < 1e-8:
                        dist = 0.0
                    comparison[matrix] = f"{dist:.4f}"
                else:
                    comparison[matrix] = "n/a"
            else:
                # 2D Wasserstein for complex eigenvalues
                re1 = g1_row[f"{matrix}_eigenvalues_re"]
                im1 = g1_row[f"{matrix}_eigenvalues_im"]
                re2 = g2_row[f"{matrix}_eigenvalues_re"]
                im2 = g2_row[f"{matrix}_eigenvalues_im"]

                if re1 is not None and re2 is not None and len(re1) == len(re2):
                    eigs1 = np.column_stack([re1, im1])
                    eigs2 = np.column_stack([re2, im2])
                    n_eigs = len(eigs1)
                    a = np.ones(n_eigs) / n_eigs
                    b = np.ones(n_eigs) / n_eigs
                    M = ot.dist(eigs1, eigs2, metric='euclidean')
                    dist = ot.emd2(a, b, M)
                    if dist < 1e-8:
                        dist = 0.0
                    comparison[matrix] = f"{dist:.4f}"
                else:
                    comparison[matrix] = "n/a"
    elif len(graph6_list) > 2:
        # Compute distance matrix for all pairs
        import numpy as np
        from scipy.stats import wasserstein_distance
        import ot

        # Fetch all graph rows
        graph_rows = [await fetch_graph(g6) for g6 in graph6_list]
        n = len(graph6_list)

        distance_matrix_data = {}
        for matrix in ["adj", "kirchhoff", "signless", "lap", "nb", "nbl", "dist"]:
            dist_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

            for i in range(n):
                for j in range(i + 1, n):
                    g1_row = graph_rows[i]
                    g2_row = graph_rows[j]

                    if matrix in ("adj", "kirchhoff", "signless", "lap", "dist"):
                        # 1D Wasserstein for real eigenvalues
                        eigs1 = g1_row[f"{matrix}_eigenvalues"]
                        eigs2 = g2_row[f"{matrix}_eigenvalues"]
                        if eigs1 is not None and eigs2 is not None and len(eigs1) == len(eigs2):
                            dist = wasserstein_distance(eigs1, eigs2)
                        else:
                            dist = float('nan')
                    else:
                        # 2D Wasserstein for complex eigenvalues
                        re1 = g1_row[f"{matrix}_eigenvalues_re"]
                        im1 = g1_row[f"{matrix}_eigenvalues_im"]
                        re2 = g2_row[f"{matrix}_eigenvalues_re"]
                        im2 = g2_row[f"{matrix}_eigenvalues_im"]

                        if re1 is not None and re2 is not None and len(re1) == len(re2):
                            eigs1 = np.column_stack([re1, im1])
                            eigs2 = np.column_stack([re2, im2])
                            n_eigs = len(eigs1)
                            a = np.ones(n_eigs) / n_eigs
                            b = np.ones(n_eigs) / n_eigs
                            M = ot.dist(eigs1, eigs2, metric='euclidean')
                            dist = ot.emd2(a, b, M)
                        else:
                            dist = float('nan')

                    # Round tiny floating point errors to exactly 0
                    if not np.isnan(dist) and dist < 1e-8:
                        dist = 0.0

                    dist_matrix[i][j] = dist
                    dist_matrix[j][i] = dist

            distance_matrix_data[matrix] = dist_matrix

        # For backward compatibility, still provide a summary
        comparison = {
            matrix: "same" if len(hashes) == 1 else "different"
            for matrix, hashes in all_hashes.items()
        }
    else:
        comparison = {
            matrix: "same" if len(hashes) == 1 else "different"
            for matrix, hashes in all_hashes.items()
        }

    # Fetch mechanisms only for 2-graph comparisons (that's all we display)
    mechanisms_by_pair = {}
    if len(graph6_list) == 2:
        from api.database import fetch_pairwise_mechanisms
        mechs = await fetch_pairwise_mechanisms(graph6_list[0], graph6_list[1])
        if mechs:
            mechanisms_by_pair["0_1"] = mechs

    result = CompareResult(graphs=full_graphs, spectral_comparison=comparison, distance_matrix=distance_matrix_data)

    if wants_html(request):
        # Compare tags (combine explicit tags + boolean properties)
        all_tag_sets = []
        for g in full_graphs:
            tags = set(g.tags or [])
            if g.properties.is_bipartite:
                tags.add("bipartite")
            if g.properties.is_planar:
                tags.add("planar")
            if g.properties.is_regular:
                tags.add("regular")
            all_tag_sets.append(frozenset(tags))

        prop_diffs = {
            "n": len(set(g.n for g in full_graphs)) > 1,
            "m": len(set(g.m for g in full_graphs)) > 1,
            "tags": len(set(all_tag_sets)) > 1,
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
            request, "compare.html", {"result": result.model_dump(), "prop_diffs": prop_diffs, "mechanisms": mechanisms_by_pair}
        )
    return result


@app.get("/glossary", response_class=HTMLResponse)
async def glossary(request: Request):
    """Terminology glossary."""
    return templates.TemplateResponse(request, "glossary.html")


@app.get("/about")
async def about(request: Request):
    """About page."""
    if wants_html(request):
        return templates.TemplateResponse(
            request, "about.html", {}
        )
    return {"message": "About page - use HTML request"}


@app.get("/stats")
async def stats(request: Request):
    """Get database statistics (API)."""
    t0 = time.perf_counter()
    data = await get_stats()
    logger.info(f"  get_stats: {(time.perf_counter()-t0)*1000:.0f}ms")
    result = Stats(**data)

    if wants_html(request):
        return templates.TemplateResponse(
            request, "stats.html", {"stats": result}
        )
    return result


@app.get("/similar/{graph6}")
async def similar_graphs(
    graph6: str,
    request: Request,
    matrix: str = Query(default="adj", description="Matrix type: adj, kirchhoff, signless, lap, nb, nbl, dist"),
    limit: int = Query(default=10, le=50),
):
    """Find graphs with similar spectrum (by Earth Mover's Distance)."""
    t0 = time.perf_counter()

    if matrix not in ("adj", "kirchhoff", "signless", "lap", "nb", "nbl", "dist"):
        raise HTTPException(status_code=400, detail="Invalid matrix type")

    results = await fetch_similar_graphs(graph6, matrix=matrix, limit=limit)
    logger.info(f"  fetch_similar_graphs: {(time.perf_counter()-t0)*1000:.0f}ms")

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
