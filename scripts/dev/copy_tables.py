import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def copy_tables_between_dbs():
    """Copy required tables from fan_weights.db to fan_pricing.db."""
    try:
        # Connect to source database
        source_db_path = 'database/fan_weights.db'
        if not os.path.exists(source_db_path):
            logger.error(f"Source database not found: {source_db_path}")
            return False
            
        source_conn = sqlite3.connect(source_db_path)
        source_cursor = source_conn.cursor()
        
        # Connect to target database
        target_db_path = 'fan_pricing.db'
        target_conn = sqlite3.connect(target_db_path)
        target_cursor = target_conn.cursor()
        
        # Get tables in source database
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        source_tables = [row[0] for row in source_cursor.fetchall()]
        logger.info(f"Tables in source database: {source_tables}")
        
        # Get tables in target database
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        target_tables = [row[0] for row in target_cursor.fetchall()]
        logger.info(f"Tables in target database before copy: {target_tables}")
        
        # List of tables needed for the application
        required_tables = [
            'FanWeights', 
            'VendorWeightDetails', 
            'BearingLookup', 
            'MotorPrices', 
            'DrivePackLookup'
        ]
        
        # Copy each required table if it doesn't exist in target DB
        for table in required_tables:
            if table in source_tables and table not in target_tables:
                logger.info(f"Copying table: {table}")
                
                # Get table schema
                source_cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in source_cursor.fetchall()]
                columns_sql = ", ".join([f'"{col}"' for col in columns])
                
                # Create table in target DB with same schema
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                create_sql = source_cursor.fetchone()[0]
                target_cursor.execute(create_sql)
                
                # Copy data
                source_cursor.execute(f"SELECT {columns_sql} FROM {table}")
                rows = source_cursor.fetchall()
                
                if rows:
                    placeholders = ", ".join(["?" for _ in columns])
                    target_cursor.executemany(
                        f"INSERT INTO {table} ({columns_sql}) VALUES ({placeholders})",
                        rows
                    )
                    logger.info(f"Copied {len(rows)} rows to {table}")
                else:
                    logger.info(f"No data to copy for table {table}")
            elif table in target_tables:
                logger.info(f"Table {table} already exists in target database")
            else:
                logger.warning(f"Table {table} not found in source database")
        
        # Commit changes
        target_conn.commit()
        
        # Verify tables in target database
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        target_tables_after = [row[0] for row in target_cursor.fetchall()]
        logger.info(f"Tables in target database after copy: {target_tables_after}")
        
        # Close connections
        source_conn.close()
        target_conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error copying tables: {str(e)}")
        return False

if __name__ == "__main__":
    if copy_tables_between_dbs():
        print("Tables copied successfully")
    else:
        print("Failed to copy tables") 