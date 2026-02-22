import sqlite3
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_database_issue():
    """Analyze database schema and SQL statements to identify mismatches."""
    try:
        # Connect to the database
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Get the table schema
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"Database has {len(columns)} columns in ProjectFans table:")
        for i, col in enumerate(column_names):
            logger.info(f"{i+1}. {col}")
        
        conn.close()
        
        # Check routes.py file for INSERT statements
        routes_file = "routes.py"
        with open(routes_file, 'r') as f:
            routes_content = f.read()
        
        # Find INSERT statement
        insert_match = re.search(r'INSERT INTO ProjectFans\s*\(([^)]+)\)', routes_content)
        if insert_match:
            insert_columns = [col.strip() for col in insert_match.group(1).split(',')]
            logger.info(f"INSERT statement has {len(insert_columns)} columns:")
            for i, col in enumerate(insert_columns):
                logger.info(f"{i+1}. {col}")
            
            # Find VALUES statement
            values_match = re.search(r'\)\s*VALUES\s*\(([^)]+)\)', routes_content)
            if values_match:
                placeholders = values_match.group(1).count('?')
                logger.info(f"VALUES statement has {placeholders} placeholders")
                
                # Check the parameter tuple
                param_section = routes_content[routes_content.find("''', ("):routes_content.find("))")]
                param_count = param_section.count(',') + 1
                logger.info(f"Parameter tuple seems to have approximately {param_count} values")
                
                # Compare numbers
                logger.info("\nAnalysis summary:")
                logger.info(f"- Database columns: {len(columns)}")
                logger.info(f"- INSERT statement columns: {len(insert_columns)}")
                logger.info(f"- VALUES placeholders: {placeholders}")
                
                # Identify potential issues
                if len(columns) != placeholders:
                    logger.warning(f"Mismatch: Database has {len(columns)} columns but VALUES has {placeholders} placeholders")
                
                # Check if there's a created_at column with default value
                has_created_at_default = False
                for col in columns:
                    if col[1] == 'created_at' and col[4]:  # col[4] is the default value
                        has_created_at_default = True
                        logger.info(f"Note: 'created_at' column has default value: {col[4]}")
                
                if has_created_at_default:
                    effective_db_columns = len(columns) - 1
                    logger.info(f"Effective columns needing values: {effective_db_columns} (excluding created_at with default)")
                
                # Look at main.js to see how many parameters are being sent
                main_js_file = "static/js/main.js"
                if os.path.exists(main_js_file):
                    with open(main_js_file, 'r') as f:
                        main_js_content = f.read()
                    
                    # Look for the relevant section around line 4215
                    save_project_section = main_js_content[main_js_content.find("saveProjectToDatabase"):main_js_content.find("saveProjectToDatabase") + 3000]
                    logger.info("\nChecking main.js saveProjectToDatabase function:")
                    
                    # Find how many parameters are being prepared for the API call
                    params_match = re.search(r'fans:\s*(\[.+?\])', save_project_section, re.DOTALL)
                    if params_match:
                        logger.info("Found fans array in saveProjectToDatabase")
                        
                # Propose solution
                logger.info("\nPotential solution:")
                logger.info("1. Ensure the VALUES clause in routes.py has exactly 42 placeholders (?).")
                logger.info("2. Ensure the parameter tuple in routes.py has exactly 42 values.")
                logger.info("3. Check if there's a created_at column with DEFAULT value that might be causing confusion.")
        else:
            logger.error("Could not find INSERT INTO ProjectFans statement in routes.py")
        
        return True
    except Exception as e:
        logger.error(f"Error analyzing database: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database analysis...")
    analyze_database_issue() 