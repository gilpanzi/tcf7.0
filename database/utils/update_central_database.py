import sqlite3
import os
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def update_central_database():
    """Update the central database schema with required columns."""
    try:
        # Use data directory for Render's persistent disk
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
        
        # Create Projects table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enquiry_number TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            total_fans INTEGER NOT NULL,
            sales_engineer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create ProjectFans table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ProjectFans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            fan_id TEXT NOT NULL,
            fan_name TEXT,
            fan_type TEXT,
            fan_size TEXT,
            fan_rpm INTEGER,
            fan_airflow REAL,
            fan_pressure REAL,
            fan_power REAL,
            fan_efficiency REAL,
            fan_material TEXT,
            fan_construction TEXT,
            fan_motor_type TEXT,
            fan_motor_power REAL,
            fan_motor_efficiency REAL,
            fan_motor_voltage REAL,
            fan_motor_current REAL,
            fan_motor_frequency REAL,
            fan_motor_phase TEXT,
            fan_motor_insulation TEXT,
            fan_motor_protection TEXT,
            fan_motor_mounting TEXT,
            fan_motor_bearing TEXT,
            fan_motor_cooling TEXT,
            fan_motor_ambient_temp REAL,
            fan_motor_altitude REAL,
            fan_motor_duty TEXT,
            fan_motor_supply TEXT,
            fan_motor_control TEXT,
            fan_motor_starter TEXT,
            fan_motor_cable TEXT,
            fan_motor_other TEXT,
            fan_accessories TEXT,
            fan_notes TEXT,
            fan_price REAL,
            fan_quantity INTEGER,
            fan_total_price REAL,
            material_name_0 TEXT,
            material_weight_0 REAL,
            material_rate_0 REAL,
            material_name_1 TEXT,
            material_weight_1 REAL,
            material_rate_1 REAL,
            material_name_2 TEXT,
            material_weight_2 REAL,
            material_rate_2 REAL,
            material_name_3 TEXT,
            material_weight_3 REAL,
            material_rate_3 REAL,
            material_name_4 TEXT,
            material_weight_4 REAL,
            material_rate_4 REAL,
            FOREIGN KEY (project_id) REFERENCES Projects(id)
        )
        ''')
        
        # Check for missing columns in Projects table and add them
        columns_to_check_projects = [
            "total_weight", 
            "total_fabrication_cost", 
            "total_bought_out_cost", 
            "total_cost", 
            "total_job_margin",
            "total_selling_price"
        ]
        
        for column in columns_to_check_projects:
            try:
                cursor.execute(f"SELECT {column} FROM Projects LIMIT 1")
            except sqlite3.OperationalError:
                logger.info(f"Adding {column} column to Projects table in central database")
                cursor.execute(f"ALTER TABLE Projects ADD COLUMN {column} REAL DEFAULT 0")
                logger.info(f"Added {column} column successfully")
        
        # Check for missing columns in ProjectFans table and add them
        columns_to_check_fans = [
            "total_job_margin",
            "fabrication_selling_price",
            "bought_out_selling_price",
            "total_selling_price",
            "vibration_isolators",
            "drive_pack_kw",
            "custom_accessories",
            "optional_items",
            "custom_option_items",
            "motor_kw",
            "motor_brand",
            "motor_pole",
            "motor_efficiency",
            "motor_discount_rate",
            "bearing_brand",
            "no_of_isolators",
            "fabrication_margin",
            "bought_out_margin",
            "shaft_diameter",
            "created_at"
        ]
        
        for column in columns_to_check_fans:
            try:
                cursor.execute(f"SELECT {column} FROM ProjectFans LIMIT 1")
            except sqlite3.OperationalError:
                logger.info(f"Adding {column} column to ProjectFans table in central database")
                
                # Determine the column type based on the column name
                if column in ["vibration_isolators", "motor_brand", "motor_efficiency", "bearing_brand"]:
                    # String columns
                    cursor.execute(f"ALTER TABLE ProjectFans ADD COLUMN {column} TEXT")
                elif column in ["custom_accessories", "optional_items", "custom_option_items"]:
                    # JSON column
                    cursor.execute(f"ALTER TABLE ProjectFans ADD COLUMN {column} TEXT")
                else:
                    # Numeric columns
                    cursor.execute(f"ALTER TABLE ProjectFans ADD COLUMN {column} REAL DEFAULT 0")
                
                logger.info(f"Added {column} column successfully")
        
        # Commit changes
        conn.commit()
        logger.info("Successfully updated central database schema")
        
        # Close the connection
        conn.close()
        logger.info("Central database connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error updating central database: {str(e)}")
        return False

if __name__ == "__main__":
    if update_central_database():
        print("Central database updated successfully.")
    else:
        print("Failed to update central database.") 