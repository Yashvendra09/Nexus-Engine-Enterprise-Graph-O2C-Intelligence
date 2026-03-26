from app.models.schemas import QueryRequest, QueryResponse
from app.services.llm_service import generate_sql_from_query
from app.services.db_executor import execute_read_query
from app.utils.guardrails import is_safe_query, is_domain_query


def process_query(request: QueryRequest) -> QueryResponse:
    """
    End-to-end query pipeline:
    - Validate user input (guardrails)
    - Convert NL → SQL via LLM
    - Execute SQL safely
    - Return structured response
    """

    user_query = request.query.strip()

    print(f"\n[DEBUG] --- Starting Query Flow ---")
    print(f"[DEBUG] Received User Input: '{user_query}'")

    try:
        # 🔒 Guardrail 1: Block unsafe queries
        if not is_safe_query(user_query):
            print("[DEBUG] Blocked unsafe query")
            return QueryResponse(
                answer="Only read-only queries are allowed.",
                data=[]
            )

        # 🔒 Guardrail 2: Ensure domain relevance
        if not is_domain_query(user_query):
            print("[DEBUG] Blocked irrelevant query")
            return QueryResponse(
                answer="This system only answers questions related to the dataset.",
                data=[]
            )

        # 🧠 Step 1: Generate SQL via LLM
        sql_query = generate_sql_from_query(user_query)
        print(f"[DEBUG] Generated SQL:\n    {sql_query}\n")

        # 🚫 Handle invalid LLM output
        if "INVALID_QUERY" in sql_query:
            print("[DEBUG] LLM could not map query to schema")
            return QueryResponse(
                answer="I could not understand the query in the context of the dataset.",
                data=[]
            )

        # 🗃️ Step 2: Execute SQL
        data_rows = execute_read_query(sql_query)
        print(f"[DEBUG] Execution successful. Extracted {len(data_rows)} rows.")

        # 🧾 Step 3: Format response
        if not data_rows:
            answer = "Query executed successfully but returned no results."
        else:
            answer = f"Query executed successfully. Retrieved {len(data_rows)} rows."

        return QueryResponse(answer=answer, data=data_rows)

    except ValueError as val_error:
        # Controlled failure (bad SQL / blocked ops)
        print(f"[ERROR] Process blocked / SQL invalid: {val_error}")
        return QueryResponse(
            answer=f"Failed to process query: {val_error}",
            data=[]
        )

    except Exception as e:
        # Unexpected failure
        print(f"[ERROR] Critical failure: {e}")
        return QueryResponse(
            answer="An unexpected error occurred while processing the query.",
            data=[]
        )