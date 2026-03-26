from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.models.schemas import GraphResponse
from app.services import graph_service

router = APIRouter(
    prefix="/graph",
    tags=["graph"]
)

@router.get("/", response_model=GraphResponse)
async def get_graph(
    node_type: Optional[str] = Query(None, description="Filter nodes by type"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of nodes to return"),
    offset: int = Query(0, ge=0, description="Number of nodes to skip")
):
    """
    Retrieve the graph structure.
    Returns filtered and paginated nodes, and computes the relevant connecting edges.
    """
    try:
        return graph_service.get_graph_data(node_type=node_type, limit=limit, offset=offset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
