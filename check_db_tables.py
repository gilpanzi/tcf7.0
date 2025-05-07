import sqlite3
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Connect to the database
try:
    conn = sqlite3.connect('fan_pricing.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables in database:", tables)
    
    # Check if BearingLookup exists
    if 'BearingLookup' in tables:
        # Get schema
        cursor.execute("PRAGMA table_info(BearingLookup)")
        columns = cursor.fetchall()
        print("\nBearingLookup schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get sample data
        cursor.execute("SELECT * FROM BearingLookup LIMIT 5")
        rows = cursor.fetchall()
        print("\nSample data (5 rows):")
        for row in rows:
            print(row)
        
        # Get distinct bearing brands
        cursor.execute("SELECT DISTINCT Brand FROM BearingLookup")
        brands = [row[0] for row in cursor.fetchall()]
        print("\nBearing brands:", brands)
    else:
        print("\nBearingLookup table does not exist")
    
    # Check if ProjectFans exists and inspect its schema
    if 'ProjectFans' in tables:
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        print("\nProjectFans schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Expected fields from routes.py
        expected_fields = [
            'project_id', 'fan_number', 'fan_model', 'fan_size', 'class', 'arrangement',
            'vendor', 'material', 'bare_fan_weight', 'accessory_weights', 'total_weight',
            'fabrication_cost', 'bought_out_cost', 'total_cost', 'accessories',
            'bearing_brand', 'shaft_diameter', 'motor_brand', 'motor_kw', 'pole', 'efficiency',
            'optional_items'
        ]
        
        # Get actual fields
        actual_fields = [col[1] for col in columns if col[1] != 'id' and col[1] != 'created_at']
        
        # Check for missing fields
        missing_fields = [field for field in expected_fields if field not in actual_fields]
        if missing_fields:
            print("\nMISSING FIELDS in ProjectFans table:", missing_fields)
            
        # Check for extra fields
        extra_fields = [field for field in actual_fields if field not in expected_fields]
        if extra_fields:
            print("\nEXTRA FIELDS in ProjectFans table:", extra_fields)
            
        print("\nExpected fields from routes.py:", expected_fields)
        print("\nActual fields in database:", actual_fields)
    
    # Check the database file being used
    print("\nDatabase file path:", 'fan_pricing.db')
    
    # Get other database files in the project
    db_files = [f for f in os.listdir() if f.endswith('.db')]
    print("All database files in project:", db_files)
    
    # If there is a database directory, check that too
    if os.path.exists('database'):
        db_files_in_dir = [f for f in os.listdir('database') if f.endswith('.db')]
        print("Database files in 'database' directory:", db_files_in_dir)
    
    conn.close()
    print("\nDatabase check completed successfully")
    
except Exception as e:
    print(f"Error checking database: {str(e)}")

def check_projectfans_schema():
    """Check the schema of the ProjectFans table in fan_pricing.db."""
    try:
        # Connect to database
        conn = sqlite3.connect('fan_pricing.db')
        cursor = conn.cursor()
        
        # Get ProjectFans schema
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        
        logger.info("ProjectFans schema:")
        for col in columns:
            logger.info(f"  {col[1]} ({col[2]})")
        
        # Also check Projects table
        cursor.execute("PRAGMA table_info(Projects)")
        columns = cursor.fetchall()
        
        logger.info("\nProjects schema:")
        for col in columns:
            logger.info(f"  {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")

if __name__ == "__main__":
    check_projectfans_schema() 