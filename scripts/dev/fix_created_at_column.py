import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def add_created_at_column():
    """Add the missing 'created_at' column to the ProjectFans table."""
    try:
        # Setup database paths
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        os.makedirs(central_db_dir, exist_ok=True)
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        
        # Connect to the database
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        logger.info(f"Connected to database at {central_db_path}")
        
        # Check if 'created_at' column exists in ProjectFans table
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'created_at' not in column_names:
            logger.info("Adding 'created_at' column to ProjectFans table")
            
            # Add the 'created_at' column with a default value of the current timestamp
            cursor.execute('''
                ALTER TABLE ProjectFans ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')
            
            # Update existing rows with the current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                UPDATE ProjectFans SET created_at = ?
            ''', (current_time,))
            
            logger.info(f"Added 'created_at' column and set default value to {current_time}")
        else:
            logger.info("'created_at' column already exists in ProjectFans table")
        
        # Commit the changes
        conn.commit()
        logger.info("Changes committed successfully")
        
        # Close the connection
        conn.close()
        logger.info("Database connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error adding 'created_at' column: {str(e)}")
        return False

if __name__ == "__main__":
    if add_created_at_column():
        print("Successfully added 'created_at' column to ProjectFans table.")
    else:
        print("Failed to add 'created_at' column to ProjectFans table.") 