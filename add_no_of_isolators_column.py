import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DBS = [
    'fan_pricing.db',
    os.path.join('data', 'central_database', 'all_projects.db')
]

# List of required columns and their types
REQUIRED_COLUMNS = [
    ('no_of_isolators', 'INTEGER DEFAULT 0'),
    ('fabrication_margin', 'REAL DEFAULT 0'),
    ('bought_out_margin', 'REAL DEFAULT 0'),
]

def add_missing_columns():
    """Add all required columns to ProjectFans table in both databases if missing."""
    for db_path in DBS:
        try:
            logger.info(f"Checking {db_path}...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(ProjectFans)")
            columns = [row[1] for row in cursor.fetchall()]
            for col_name, col_type in REQUIRED_COLUMNS:
                if col_name not in columns:
                    logger.info(f"Adding '{col_name}' column to {db_path}...")
                    cursor.execute(f"ALTER TABLE ProjectFans ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    logger.info(f"Successfully added '{col_name}' column to {db_path}")
                else:
                    logger.info(f"'{col_name}' column already exists in {db_path}")
            conn.close()
        except Exception as e:
            logger.error(f"Error processing {db_path}: {str(e)}")
            if 'conn' in locals():
                conn.close()

if __name__ == '__main__':
    add_missing_columns() 