import os
import glob
import logging
import sqlite3
import pandas as pd
from typing import List, Optional
from app.services.data_loader import load_jsonl_to_table, get_db_connection

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IngestionEngine:
    """
    Enterprise-grade data ingestion engine for SAP Order-to-Cash JSONL datasets.
    Handles dynamic schema inference and recursive directory scanning.
    """
    
    def __init__(self, data_dir: str, db_path: str):
        self.data_dir = os.path.abspath(data_dir)
        self.db_path = os.path.abspath(db_path)
        
    def validate_environment(self) -> bool:
        """Checks if the target data directory exists."""
        if not os.path.exists(self.data_dir):
            logger.error(f"Data directory not found: {self.data_dir}")
            return False
        logger.info(f"Verified data directory: {self.data_dir}")
        return True

    def _discover_tables(self) -> List[str]:
        """Identifies subdirectories in the data folder as table names."""
        return [
            d for d in os.listdir(self.data_dir) 
            if os.path.isdir(os.path.join(self.data_dir, d))
        ]

    def run(self, reset_db: bool = False):
        """
        Executes the full ingestion pipeline.
        
        Args:
            reset_db: If True, deletes the existing database file before starting.
        """
        if not self.validate_environment():
            return

        if reset_db and os.path.exists(self.db_path):
            logger.warning(f"Resetting database at {self.db_path}")
            os.remove(self.db_path)

        tables = self._discover_tables()
        logger.info(f"Found {len(tables)} target tables for ingestion.")

        conn = get_db_connection(self.db_path)
        
        try:
            for table_name in tables:
                table_path = os.path.join(self.data_dir, table_name)
                jsonl_files = glob.glob(os.path.join(table_path, "*.jsonl"))
                
                if not jsonl_files:
                    logger.warning(f"No .jsonl files found for table: {table_name}")
                    continue

                logger.info(f"Ingesting {len(jsonl_files)} files into table: {table_name}")
                
                for file_path in jsonl_files:
                    try:
                        load_jsonl_to_table(file_path, table_name, conn)
                    except Exception as e:
                        logger.error(f"Failed to load {file_path} into {table_name}: {e}")
            
            logger.info("Ingestion completed successfully.")
        finally:
            conn.close()
            logger.info("Database connection closed.")

def main():
    # Resolve absolute paths relative to the script location for portability
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Target path from Downloads (hardcoded for this specific environment as requested)
    target_data = r"C:\Users\yash2\Downloads\sap-order-to-cash-dataset\sap-o2c-data"
    target_db = os.path.join(script_dir, "supply_chain.db")

    engine = IngestionEngine(data_dir=target_data, db_path=target_db)
    engine.run(reset_db=False)

if __name__ == "__main__":
    main()
