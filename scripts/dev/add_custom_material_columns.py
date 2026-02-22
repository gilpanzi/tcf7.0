import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def add_custom_material_columns():
    """Add custom material columns to ProjectFans table in both databases."""
    databases = [
        'fan_pricing.db',
        'data/central_database/all_projects.db'
    ]
    
    for db_path in databases:
        if not os.path.exists(db_path):
            logger.warning(f"Database {db_path} not found, skipping...")
            continue
            
        logger.info(f"Adding custom material columns to {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add columns for each custom material (0-4)
        for i in range(5):
            columns_to_add = [
                f'material_name_{i} TEXT',
                f'material_weight_{i} REAL DEFAULT 0',
                f'material_rate_{i} REAL DEFAULT 0'
            ]
            
            for column_def in columns_to_add:
                column_name = column_def.split()[0]
                try:
                    cursor.execute(f"SELECT {column_name} FROM ProjectFans LIMIT 1")
                    logger.info(f"Column {column_name} already exists")
                except sqlite3.OperationalError:
                    logger.info(f"Adding column {column_name}")
                    cursor.execute(f"ALTER TABLE ProjectFans ADD COLUMN {column_def}")
                    logger.info(f"Added column {column_name} successfully")
        
        conn.commit()
        conn.close()
        logger.info(f"Finished updating {db_path}")

if __name__ == "__main__":
    add_custom_material_columns() 