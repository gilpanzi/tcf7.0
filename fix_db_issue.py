import sqlite3
import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_routes_file():
    """Fix the routes.py file to address the binding mismatch issue."""
    try:
        routes_file = "routes.py"
        backup_file = "routes.py.bak"
        
        # Create a backup of the routes.py file
        logger.info(f"Creating backup of {routes_file} as {backup_file}")
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Find the relevant INSERT statement
        insert_pattern = r"INSERT INTO ProjectFans \((.*?)\) VALUES \((.*?)\)"
        insert_match = re.search(insert_pattern, content, re.DOTALL)
        
        if not insert_match:
            logger.error("Could not find INSERT INTO ProjectFans statement")
            return False
        
        # Extract column list and placeholders
        columns_text = insert_match.group(1)
        placeholders_text = insert_match.group(2)
        
        # Count columns and placeholders
        column_count = len([col.strip() for col in re.findall(r'[a-zA-Z_]+', columns_text)])
        placeholder_count = placeholders_text.count('?')
        
        logger.info(f"Found {column_count} columns and {placeholder_count} placeholders in INSERT statement")
        
        # Check if created_at is in columns
        if "created_at" in columns_text:
            logger.info("The 'created_at' column is already in the INSERT statement")
            
        # Look for parameter tuple in the save_project_to_database function
        param_pattern = r"VALUES \(.*?\)\s*''',\s*\(\s*(.*?)\s*\)\)"
        param_match = re.search(param_pattern, content, re.DOTALL)
        
        if not param_match:
            logger.error("Could not find parameter tuple")
            return False
        
        param_text = param_match.group(1)
        param_count = param_text.count(',') + 1
        logger.info(f"Found {param_count} parameters in the tuple")
        
        # Now fix the mismatch
        if placeholder_count < param_count:
            logger.info(f"Mismatch detected: {placeholder_count} placeholders but {param_count} parameters")
            
            # Fix the specific pattern where we have an extra parameter at the end
            # This pattern detects any trailing parameter after bought_out_margin
            extra_param_pattern = r"(fan\.get\('bought_out_margin', costs\.get\('bought_out_margin', 0\)),)(.*?)(\s*\)\))"
            match = re.search(extra_param_pattern, content, re.DOTALL)
            
            if match:
                logger.info("Found extra parameter after bought_out_margin")
                # Remove the extra parameter
                modified_content = re.sub(extra_param_pattern, r"\1\3", content)
                
                # Write the modified content back to the file
                with open(routes_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                logger.info("Successfully removed extra parameter")
                return True
            else:
                logger.warning("Could not find the expected pattern to fix. Additional diagnostics needed.")
                return False
        
        elif placeholder_count > param_count:
            logger.info(f"Mismatch detected: {placeholder_count} placeholders but only {param_count} parameters")
            logger.info("This requires adding a parameter. Manual intervention is recommended.")
            return False
        
        else:
            logger.info(f"No mismatch detected: {placeholder_count} placeholders and {param_count} parameters")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing routes file: {str(e)}")
        return False

def check_database_schema():
    """Check the database schema to ensure it matches the code."""
    try:
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Get column info from the table
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"The ProjectFans table has {len(columns)} columns")
        
        # Check if created_at is present
        if 'created_at' in column_names:
            logger.info("The 'created_at' column exists in the database")
        else:
            logger.info("The 'created_at' column does not exist in the database")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking database schema: {str(e)}")

if __name__ == "__main__":
    check_database_schema()
    if fix_routes_file():
        print("Successfully fixed the binding mismatch issue. Please restart the application.")
    else:
        print("Could not fix the binding mismatch issue automatically. Manual intervention required.") 