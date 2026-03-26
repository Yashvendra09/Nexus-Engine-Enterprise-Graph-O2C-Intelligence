from pydantic import BaseModel
from typing import List, Any

class GraphResponse(BaseModel):
    """Schema for graph representation with nodes and edges."""
    nodes: List[Any] = []
    edges: List[Any] = []

class QueryRequest(BaseModel):
    """Schema for incoming user queries."""
    query: str

class QueryResponse(BaseModel):
    """Schema for the query response."""
    answer: str
    data: List[Any] = []
