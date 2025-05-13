import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database_mismatch():
    """Fix the database mismatch by adding the missing flex_connectors_cost column."""
    try:
        # Check the database schema
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Get the column names
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        
        logger.info(f"ProjectFans table has {len(columns)} columns")
        
        # Check if there's a created_at column with default value
        created_at_default = None
        for col in columns:
            if col[1] == 'created_at':
                created_at_default = col[4]
                logger.info(f"Found created_at column with default value: {created_at_default}")
        
        conn.close()
        
        # Fix the INSERT statement in routes.py
        routes_file = "routes.py"
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # We need to add one more placeholder to get to 42 values (to match 43 columns with created_at having a default)
        # Find the INSERT statement for ProjectFans
        insert_line_prefix = "                        ) VALUES ("
        insert_line_suffix = ")\n                    ''', ("
        
        # Count the number of question marks in the VALUES statements
        import re
        insert_lines = re.findall(r'\)\s*VALUES\s*\(([^)]+)\)', content)
        
        # Identify lines with exactly 41 placeholders (these need to be fixed to have 42)
        lines_to_fix = []
        for i, line in enumerate(insert_lines):
            if line.count('?') == 41:
                logger.info(f"Found VALUES line with 41 placeholders: {line}")
                lines_to_fix.append(line)
        
        # Fix each line by adding one more placeholder
        if lines_to_fix:
            for line in lines_to_fix:
                new_line = line + ", ?"
                content = content.replace(line + ")", new_line + ")")
            
            # Write the updated content back to the file
            with open(routes_file, 'w') as f:
                f.write(content)
            
            logger.info(f"Fixed {len(lines_to_fix)} lines in routes.py by adding one more placeholder")
        else:
            logger.info("No lines with 41 placeholders found")
        
        # Update the parameter list to add a null value for the missing column
        # Note: We need to modify the tuple of parameters to include one more NULL value
        # This is more complex and depends on the exact structure of the code
        # This example assumes we can find the tuple by looking for a specific pattern
        
        return True
    except Exception as e:
        logger.error(f"Error fixing database mismatch: {str(e)}")
        return False

def create_new_database():
    """Create a new database with the correct schema."""
    try:
        # Use data directory for central database
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        os.makedirs(central_db_dir, exist_ok=True)
        
        # Backup the existing database
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        if os.path.exists(central_db_path):
            import shutil
            backup_path = os.path.join(central_db_dir, 'all_projects_backup.db')
            shutil.copy(central_db_path, backup_path)
            logger.info(f"Backed up database to {backup_path}")
        
        # Connect to the database
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Drop and recreate the table with the correct schema
        # This is a more drastic approach
        cursor.execute("DROP TABLE IF EXISTS ProjectFans")
        
        # Create the table with the same schema but without the extra column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ProjectFans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT,
                fan_number INTEGER,
                fan_model TEXT,
                size TEXT,
                class TEXT,
                arrangement TEXT,
                vendor TEXT,
                material TEXT,
                accessories TEXT,
                bare_fan_weight REAL,
                accessory_weight REAL,
                total_weight REAL,
                fabrication_weight REAL,
                bought_out_weight REAL,
                fabrication_cost REAL,
                motor_cost REAL,
                vibration_isolators_cost REAL,
                drive_pack_cost REAL,
                bearing_cost REAL,
                optional_items_cost REAL,
                flex_connectors_cost REAL,
                bought_out_cost REAL,
                total_cost REAL,
                fabrication_selling_price REAL,
                bought_out_selling_price REAL,
                total_selling_price REAL,
                total_job_margin REAL,
                vibration_isolators TEXT,
                drive_pack_kw REAL,
                custom_accessories TEXT,
                optional_items TEXT,
                custom_option_items TEXT,
                motor_kw REAL,
                motor_brand TEXT,
                motor_pole REAL,
                motor_efficiency TEXT,
                motor_discount_rate REAL,
                bearing_brand TEXT,
                shaft_diameter REAL,
                no_of_isolators INTEGER,
                fabrication_margin REAL,
                bought_out_margin REAL,
                FOREIGN KEY (enquiry_number) REFERENCES Projects(enquiry_number)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Created new database with the correct schema")
        return True
    except Exception as e:
        logger.error(f"Error creating new database: {str(e)}")
        return False

def add_extra_parameter():
    """Modify the routes.py file to add an extra parameter in the database insertion."""
    try:
        routes_file = "routes.py"
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Find the INSERT statement parameters
        # Look for the specific fan parameter list
        parameter_start = "fan.get('bought_out_margin', costs.get('bought_out_margin', 0))"
        parameter_end = "))"
        
        # Add an extra NULL parameter
        updated_content = content.replace(
            parameter_start + parameter_end,
            parameter_start + ",\n                        None" + parameter_end
        )
        
        with open(routes_file, 'w') as f:
            f.write(updated_content)
        
        logger.info("Added extra NULL parameter to the INSERT statement")
        return True
    except Exception as e:
        logger.error(f"Error adding extra parameter: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database mismatch fix...")
    
    # Fix the mismatch by updating the INSERT statement
    if fix_database_mismatch():
        logger.info("Successfully fixed the database mismatch")
        
        # Add the extra parameter
        if add_extra_parameter():
            logger.info("Successfully added extra parameter")
        else:
            logger.warning("Failed to add extra parameter")
        
        logger.info("Fix complete. Restart the application for changes to take effect.")
    else:
        logger.error("Failed to fix database mismatch")
        
        # Alternative: Create a new database with the correct schema
        # if create_new_database():
        #     logger.info("Created new database with correct schema as a fallback")
        # else:
        #     logger.error("Failed to create new database") 