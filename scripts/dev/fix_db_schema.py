import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_schema_issues():
    """Fix database schema issues including the ProjectFans table."""
    try:
        # Update central database
        fix_central_database()
        
        # Also update the main database schema if needed
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, 'fan_pricing.db')
        
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if ProjectFans table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
            if cursor.fetchone():
                # Drop and recreate the table to ensure it has the correct schema
                cursor.execute("DROP TABLE IF EXISTS ProjectFans")
            
            # Create the table with the correct schema
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
            logger.info("Fixed schema issues in main database")
        
        return True
    except Exception as e:
        logger.error(f"Error fixing schema issues: {str(e)}")
        return False

def fix_central_database():
    """Fix central database schema issues."""
    try:
        # Use data directory for central database
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        os.makedirs(central_db_dir, exist_ok=True)
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        
        # If the central database doesn't exist in the data directory but exists in the original location,
        # copy it to the data directory
        original_db_path = 'central_database/all_projects.db'
        if not os.path.exists(central_db_path) and os.path.exists(original_db_path):
            os.makedirs(os.path.dirname(central_db_path), exist_ok=True)
            import shutil
            shutil.copy(original_db_path, central_db_path)
            logger.info(f"Copied central database to {central_db_path}")
        
        # Connect to the central database
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        logger.info(f"Connected to central database at {central_db_path}")
        
        # Check if ProjectFans table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
        if cursor.fetchone():
            # Drop and recreate the table to ensure it has the correct schema
            cursor.execute("DROP TABLE IF EXISTS ProjectFans")
        
        # Create ProjectFans table with the correct schema
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
                FOREIGN KEY (enquiry_number) REFERENCES Projects(id)
            )
        ''')
        
        # Count columns
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        logger.info(f"ProjectFans table has {len(columns)} columns")
        
        conn.commit()
        conn.close()
        logger.info("Fixed schema issues in central database")
        
        # Also fix the routes.py file to have the correct number of placeholders
        fix_routes_file()
        
        return True
    except Exception as e:
        logger.error(f"Error fixing central database: {str(e)}")
        return False

def fix_routes_file():
    """Fix the routes.py file to have the correct number of placeholders."""
    try:
        file_path = "routes.py"
        if not os.path.exists(file_path):
            logger.error(f"routes.py file not found at {file_path}")
            return False
        
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the problematic VALUES line with too many placeholders
        if ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)" in content:
            # Replace with exactly 41 placeholders
            correct_placeholders = ", ".join(["?"] * 41)
            new_content = content.replace(") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", f") VALUES ({correct_placeholders})")
            
            # Write the corrected content back to the file
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            logger.info("Fixed VALUES placeholders in routes.py")
            return True
        else:
            logger.info("No problematic VALUES line found in routes.py")
            return False
    except Exception as e:
        logger.error(f"Error fixing routes.py file: {str(e)}")
        return False

if __name__ == "__main__":
    if fix_schema_issues():
        print("Schema issues fixed successfully.")
    else:
        print("Failed to fix schema issues.") 