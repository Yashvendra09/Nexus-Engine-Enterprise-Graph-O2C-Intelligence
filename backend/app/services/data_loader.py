import sqlite3
import pandas as pd
import json

def get_db_connection(db_path: str = "database.db") -> sqlite3.Connection:
    """
    Initializes and returns a SQLite database connection.
    """
    conn = sqlite3.connect(db_path)
    return conn

def load_jsonl_to_table(jsonl_path: str, table_name: str, conn: sqlite3.Connection) -> None:
    """
    Loads a JSON Lines (.jsonl) file into a SQLite table using pandas.
    Nested objects (if any) are stringified to prevent SQL insertion errors.
    If the table already exists, it appends to allow multi-file ingestion.
    """
    print(f"Loading '{jsonl_path}' into table '{table_name}'...")
    
    # Read the JSONL file. 
    # Because some enterprise data has nested dicts (like creationTime: {hours: 13, minutes: ...}), 
    # we need to stringify nested objects before sending to SQLite.
    
    records = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            # Flatten/stringify any nested dictionaries or lists
            for key, val in row.items():
                if isinstance(val, (dict, list)):
                    row[key] = json.dumps(val)
            records.append(row)

    if not records:
        print(f"File {jsonl_path} is empty. Skipping.")
        return

    df = pd.DataFrame(records)
    
    # Write the dataframe to SQLite without an index column. Use 'append' instead of 'replace'
    # in case multiple part-*.jsonl files belong to the same directory (table)
    df.to_sql(name=table_name, con=conn, if_exists='append', index=False)
    print(f"Successfully appended {len(df)} rows into '{table_name}'.")
