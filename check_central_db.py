import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_central_db():
    """Check if the central database exists and has the correct structure."""
    # Use the data directory for the central database
    data_dir = 'data'
    central_db_path = os.path.join(data_dir, 'central_database', 'all_projects.db')
    
    # If the database doesn't exist in the data directory, check the original location
    original_db_path = 'central_database/all_projects.db'
    if not os.path.exists(central_db_path) and os.path.exists(original_db_path):
        # Create the directory structure
        os.makedirs(os.path.dirname(central_db_path), exist_ok=True)
        # Copy the database
        import shutil
        shutil.copy(original_db_path, central_db_path)
        logger.info(f"Copied central database to {central_db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Check if the Projects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Projects'")
        if cursor.fetchone() is None:
            print("Projects table doesn't exist in the central database")
            conn.close()
            return False
        
        # Check if the ProjectFans table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
        if cursor.fetchone() is None:
            print("ProjectFans table doesn't exist in the central database")
            conn.close()
            return False
            
        # Tables exist, database is valid
        print("Central database is valid, all required tables exist")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error checking central database: {e}")
        return False

if __name__ == "__main__":
    check_central_db() 