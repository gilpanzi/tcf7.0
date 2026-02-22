import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_project_fans_table():
    try:
        # Connect to the database
        conn = sqlite3.connect('fan_pricing.db')
        cursor = conn.cursor()
        
        logger.info("Connected to database")
        
        # Check if optional_items column exists
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Existing columns: {columns}")
        
        if 'optional_items' not in columns:
            logger.info("Adding missing optional_items column to ProjectFans table")
            # Add the optional_items column
            cursor.execute("ALTER TABLE ProjectFans ADD COLUMN optional_items TEXT")
            conn.commit()
            logger.info("Added optional_items column to ProjectFans table")
        else:
            logger.info("optional_items column already exists in ProjectFans table")
        
        # Close the connection
        conn.close()
        logger.info("Database connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error fixing ProjectFans table: {str(e)}")
        return False

if __name__ == "__main__":
    if fix_project_fans_table():
        print("ProjectFans table fixed successfully.")
    else:
        print("Failed to fix ProjectFans table.") 