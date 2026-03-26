from app.models.schemas import GraphResponse
from app.services.graph_builder import build_graph, graph_to_json

ALLOWED_NODE_TYPES = {"partner", "order", "order_item", "product", "delivery", "invoice", "payment", "customer", "address"}

def get_graph_data(node_type: str = None, limit: int = 500, offset: int = 0) -> GraphResponse:
    """
    Fetches the current graph data mapped out from the database, applying filtering and pagination.
    """
    # Defensive programming for invalid parameters
    if node_type and node_type not in ALLOWED_NODE_TYPES:
        raise ValueError(f"Invalid node_type: '{node_type}'. Allowed types are: {', '.join(ALLOWED_NODE_TYPES)}")

    # Build the complete internal directed graph from DB
    graph = build_graph() 
    
    # 1. Filter Nodes by Type
    if node_type:
        primary_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == node_type]
    else:
        primary_nodes = list(graph.nodes())

    # 2. Apply Pagination Boundaries
    paginated_nodes = primary_nodes[offset : offset + limit]

    # 3. Include 1-hop neighbors (both incoming and outgoing)
    final_node_set = set(paginated_nodes)
    for node in paginated_nodes:
        # Add nodes that point to this node
        final_node_set.update(graph.predecessors(node))
        # Add nodes this node points to
        final_node_set.update(graph.successors(node))

    # 4. Create Subgraph 
    # (NetworkX intrinsically guarantees that only edges connecting the elements of this strictly returned subset of nodes are kept)
    subgraph = graph.subgraph(list(final_node_set))
    
    # Export it to the JSON schema payload we declared
    json_data = graph_to_json(subgraph)
    
    return GraphResponse(nodes=json_data["nodes"], edges=json_data["edges"])
