import sqlite3
from typing import List, Dict, Any

def execute_read_query(sql_query: str, db_path: str = "supply_chain.db") -> List[Dict[str, Any]]:
    """
    Executes a read-only SQL query against the database and returns result dicts.
    """
    # 1. Provide a base safety barrier 
    # (Checking against dangerous SQL operations for safety prior to real execution)
    dangerous_keywords = ["drop", "delete", "update", "insert", "alter", "replace", "grant", "revoke"]
    query_eval = sql_query.lower()
    
    for kw in dangerous_keywords:
        # Check for isolated keywords to block mutation operations
        if f" {kw} " in f" {query_eval} " or query_eval.startswith(f"{kw} "):
            raise ValueError(f"Dangerous SQL Operation prevented. '{kw.upper()}' commands are not allowed.")

    # 2. Database Execution Block
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Maps column results into dictionary structure
    
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        rows = cur.fetchall()
        
        # Convert sqlite3.Row proxies to raw standard dictionaries
        return [dict(row) for row in rows]
        
    except sqlite3.Error as db_error:
        raise ValueError(f"Constraint or syntax error during DB Execution: {db_error}")
    finally:
        conn.close()
