import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def identify_database_issue():
    """Identify database schema issues and mismatches."""
    try:
        # Connect to the central database
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        os.makedirs(central_db_dir, exist_ok=True)
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        
        if not os.path.exists(central_db_path):
            logger.error(f"Database not found at {central_db_path}")
            return False
        
        # Get the ProjectFans table schema
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Get the column names
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"ProjectFans table has {len(columns)} columns:")
        for i, col in enumerate(column_names):
            logger.info(f"{i+1}. {col}")
        
        # Check if there's a created_at column that might be missing in the INSERT statement
        if 'created_at' in column_names:
            logger.info("Found 'created_at' column which might require a value in the INSERT statement")
        
        # Identify columns that might need to be added to the INSERT statement
        conn.close()
        
        # Check routes.py for INSERT statement
        routes_file = "routes.py"
        if not os.path.exists(routes_file):
            logger.error(f"Routes file not found at {routes_file}")
            return False
        
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Find the INSERT INTO ProjectFans statements
        import re
        insert_statements = re.findall(r'INSERT INTO ProjectFans\s*\(([^)]+)\)', content)
        
        if not insert_statements:
            logger.error("No INSERT INTO ProjectFans statements found")
            return False
        
        for i, stmt in enumerate(insert_statements):
            # Clean up and split the column names
            cols_in_insert = [c.strip() for c in stmt.split(',')]
            logger.info(f"INSERT statement {i+1} has {len(cols_in_insert)} columns:")
            
            # Check for missing columns
            missing_from_insert = set(column_names) - set(cols_in_insert)
            if missing_from_insert:
                logger.info(f"Columns in database but missing from INSERT statement: {missing_from_insert}")
            
            # Check for extra columns
            extra_in_insert = set(cols_in_insert) - set(column_names)
            if extra_in_insert:
                logger.info(f"Columns in INSERT statement but missing from database: {extra_in_insert}")
        
        # Find the VALUES statements
        values_patterns = re.findall(r'\)\s*VALUES\s*\(([^)]+)\)', content)
        
        for i, pattern in enumerate(values_patterns):
            # Count placeholders
            placeholders = pattern.count('?')
            logger.info(f"VALUES pattern {i+1} has {placeholders} placeholders")
            
            # Compare with column count
            if placeholders != len(columns):
                logger.warning(f"Mismatch: VALUES pattern has {placeholders} placeholders but table has {len(columns)} columns")
                
                # Check if created_at has a default value
                has_created_at_default = False
                for col in columns:
                    if col[1] == 'created_at' and col[4]:  # col[4] is the default value
                        has_created_at_default = True
                        logger.info(f"Column 'created_at' has default value: {col[4]}")
                
                if has_created_at_default:
                    expected_placeholders = len(columns) - 1
                    if placeholders == expected_placeholders:
                        logger.info(f"This is likely correct because 'created_at' has a default value")
                    else:
                        logger.warning(f"Even accounting for 'created_at' default, expected {expected_placeholders} placeholders")
        
        # Suggest a fix
        logger.info("\nSuggested fix:")
        if len(columns) == 43 and 'created_at' in column_names:
            logger.info("The database has 43 columns including 'created_at' with default value.")
            logger.info("If your INSERT statement has 41 placeholders, you need to add one more placeholder to match 42 values.")
            logger.info("Update routes.py to add the missing column(s) and make sure all VALUES statements have 42 placeholders.")
        
        return True
    except Exception as e:
        logger.error(f"Error analyzing database: {str(e)}")
        return False

def update_database_schema():
    """Update database schema to match INSERT statements."""
    try:
        # Add missing column or fix the VALUES statement
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Option 1: Add a default value to a required column
        # cursor.execute("ALTER TABLE ProjectFans ADD COLUMN flex_connectors_cost REAL DEFAULT 0")
        
        # Option 2: Drop and recreate the table with the correct schema
        # This is risky if the table has important data
        
        conn.commit()
        conn.close()
        logger.info("Database schema updated")
        
        return True
    except Exception as e:
        logger.error(f"Error updating database schema: {str(e)}")
        return False

def add_missing_parameter_to_insert():
    """Update the INSERT statement to include a missing column value."""
    try:
        routes_file = "routes.py"
        
        # Read the file
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Add the missing column in the INSERT statement
        # This is just an example, modify as needed
        updated_content = content.replace(
            "enquiry_number, fan_number, fan_model, size, class, arrangement",
            "enquiry_number, fan_number, fan_model, size, class, arrangement, created_at"
        )
        
        # Add the missing placeholder in the VALUES statement
        updated_content = updated_content.replace(
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        
        # Write the updated content
        with open(routes_file, 'w') as f:
            f.write(updated_content)
        
        logger.info("Updated INSERT statement in routes.py")
        return True
    except Exception as e:
        logger.error(f"Error updating routes.py: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database analysis...")
    if identify_database_issue():
        logger.info("Analysis complete. Review the information above.")
        
        # Uncomment to apply fixes
        # update_database_schema()
        # add_missing_parameter_to_insert()
    else:
        logger.error("Failed to analyze database schema.") 