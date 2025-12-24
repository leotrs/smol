"""API routes for switching mechanisms."""

from typing import Optional

from fastapi import APIRouter, Query

from ..database import fetch_graph_mechanisms, fetch_mechanism_stats

router = APIRouter(prefix="/api", tags=["mechanisms"])


@router.get("/graph/{graph6}/mechanisms")
async def get_graph_mechanisms(
    graph6: str,
    matrix_type: Optional[str] = Query(None, description="Filter by matrix type")
):
    """Get all mechanisms for a specific graph."""
    return await fetch_graph_mechanisms(graph6, matrix_type)


@router.get("/stats/mechanisms")
async def get_mechanism_stats(
    n: Optional[int] = Query(None, description="Filter by vertex count"),
    matrix_type: str = Query("adj", description="Matrix type")
):
    """Get statistics about mechanism coverage."""
    return await fetch_mechanism_stats(n, matrix_type)
