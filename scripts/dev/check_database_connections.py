import sqlite3
import logging
import os
import inspect
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def read_file_content(file_path):
    """Read and return the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None

def extract_database_paths(content):
    """Extract database paths from file content."""
    # Common patterns for database connections
    patterns = [
        r"sqlite3\.connect\(['\"]([^'\"]+)['\"]",  # sqlite3.connect('db_path')
        r"connect\(['\"]([^'\"]+)['\"]",           # connect('db_path')
        r"database_path\s*=\s*['\"]([^'\"]+)['\"]" # database_path = 'db_path'
    ]
    
    paths = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        paths.extend(matches)
    
    return paths

def check_database_connections():
    """Check database connections in the app."""
    try:
        logger.info("Checking database connections in files...")
        
        # Dictionary to store file paths and their database paths
        file_db_paths = {}
        
        # List of Python files to check
        files_to_check = [
            'app.py', 
            'database.py', 
            'create_projects_table.py',
            'routes.py'
        ]
        
        # Read each file and extract database paths
        for file_path in files_to_check:
            if os.path.exists(file_path):
                content = read_file_content(file_path)
                if content:
                    db_paths = extract_database_paths(content)
                    file_db_paths[file_path] = db_paths
                    logger.info(f"File: {file_path}, Database paths: {db_paths}")
        
        # Check for actual database files
        db_files = [f for f in os.listdir() if f.endswith('.db')]
        logger.info(f"Database files in root directory: {db_files}")
        
        if os.path.exists('database'):
            db_files_in_dir = [os.path.join('database', f) for f in os.listdir('database') if f.endswith('.db')]
            logger.info(f"Database files in database directory: {db_files_in_dir}")
            db_files.extend(db_files_in_dir)
        
        # Check each database file
        for db_file in db_files:
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"Database file: {db_file}, Tables: {tables}")
                
                # Check if Projects table exists
                if 'Projects' in tables:
                    # Get record count
                    cursor.execute("SELECT COUNT(*) FROM Projects")
                    count = cursor.fetchone()[0]
                    logger.info(f"Projects table in {db_file} has {count} records")
                
                conn.close()
            except Exception as e:
                logger.error(f"Error checking database {db_file}: {str(e)}")
        
        logger.info("Database connection check completed")
        
        # Find root cause of the error
        logger.info("\nPOTENTIAL ISSUE ANALYSIS:")
        for file, paths in file_db_paths.items():
            for path in paths:
                # Check if this path exists
                if os.path.exists(path):
                    logger.info(f"Database path in {file}: {path} (EXISTS)")
                else:
                    logger.info(f"Database path in {file}: {path} (DOES NOT EXIST)")
        
        # Check if different files are using different databases
        all_paths = []
        for paths in file_db_paths.values():
            all_paths.extend(paths)
        
        unique_paths = set(all_paths)
        if len(unique_paths) > 1:
            logger.warning("ISSUE FOUND: Different files are using different database paths:")
            for path in unique_paths:
                logger.warning(f"  - {path}")
            logger.warning("This may be causing the error. Ensure all files use the same database.")
        
        return True
    except Exception as e:
        logger.error(f"Error checking database connections: {str(e)}")
        return False

if __name__ == "__main__":
    if check_database_connections():
        print("Database connection check completed successfully")
    else:
        print("Failed to check database connections") 