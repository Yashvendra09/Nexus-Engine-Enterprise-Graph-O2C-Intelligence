from fastapi import APIRouter
from app.models.schemas import QueryRequest, QueryResponse
from app.services import query_service

router = APIRouter(
    prefix="/query",
    tags=["query"]
)

@router.post("/", response_model=QueryResponse)
async def submit_query(request: QueryRequest):
    """
    Submit a query for the LLM layer.
    Returns a placeholder answer.
    """
    return query_service.process_query(request)
