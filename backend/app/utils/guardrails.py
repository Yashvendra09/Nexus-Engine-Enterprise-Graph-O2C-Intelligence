import re

# Words that are unsafe at the SQL operation level (destructive DML/DDL)
_UNSAFE_SQL_PATTERN = re.compile(
    r'\b(drop|delete|truncate|insert|update|alter|create|replace|exec|execute|pragma)\b',
    re.IGNORECASE
)

# All domain terms that are valid for this dataset - kept broad to handle natural language variations
# Covers SAP O2C entities as well as common English synonyms users might use
_DOMAIN_TERMS = {
    # Core entity terms
    "order", "orders", "partner", "partners", "business", "customer", "customers",
    "invoice", "invoices", "billing", "payment", "payments", "delivery", "deliveries",
    "product", "products", "material", "materials", "stock",
    # SAP specific
    "sales", "outbound", "journal", "receivable", "schedule", "plant", "location",
    # Common query verbs people use (let them through)
    "show", "list", "get", "return", "fetch", "give", "find", "display", "total",
    "count", "sum", "how many", "what", "which", "all", "top", "highest", "lowest",
    "average", "avg", "recent", "latest", "amount", "quantity", "status", "date",
}


def is_safe_query(user_query: str) -> bool:
    """
    Blocks queries that contain destructive SQL keywords anywhere in the input.
    Case-insensitive, word-boundary matched to avoid false positives like 'updated_at'.
    """
    return not bool(_UNSAFE_SQL_PATTERN.search(user_query))


def is_domain_query(user_query: str) -> bool:
    """
    Checks if the query is related to the SAP Order-to-Cash dataset.
    Uses a broad set of domain terms including natural language synonyms.
    The goal is to be permissive (let the LLM handle ambiguity) but reject 
    clearly off-topic queries like weather, coding questions, etc.
    """
    query_lower = user_query.lower()
    # Allow if any domain term appears in the query
    return any(term in query_lower for term in _DOMAIN_TERMS)