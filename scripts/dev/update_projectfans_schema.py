#!/usr/bin/env python3
"""
Comprehensive script to update the ProjectFans table schema in all databases
to ensure all required columns are present, including support for new features
and optional items like AMCA Type C Spark Proof Construction.
"""

import sqlite3
import os
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"schema_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define database paths
DB_PATHS = [
    'fan_pricing.db',  # Main application database
    os.path.join('data', 'fan_pricing.db'),  # Render path for main database
    os.path.join('data', 'central_database', 'all_projects.db')  # Central database
]

# Define all columns that should be in the ProjectFans table
# Format: (column_name, column_type_with_default)
REQUIRED_COLUMNS = [
    # Basic identification columns
    ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'),
    ('enquiry_number', 'TEXT'),
    ('fan_number', 'INTEGER'),
    
    # Fan specifications
    ('fan_model', 'TEXT'),
    ('size', 'TEXT'),
    ('class', 'TEXT'),
    ('arrangement', 'TEXT'),
    ('vendor', 'TEXT'),
    ('material', 'TEXT'),
    ('accessories', 'TEXT'),
    
    # Weight information
    ('bare_fan_weight', 'REAL DEFAULT 0'),
    ('accessory_weight', 'REAL DEFAULT 0'),
    ('total_weight', 'REAL DEFAULT 0'),
    ('fabrication_weight', 'REAL DEFAULT 0'),
    ('bought_out_weight', 'REAL DEFAULT 0'),
    
    # Cost information
    ('fabrication_cost', 'REAL DEFAULT 0'),
    ('motor_cost', 'REAL DEFAULT 0'),
    ('vibration_isolators_cost', 'REAL DEFAULT 0'),
    ('drive_pack_cost', 'REAL DEFAULT 0'),
    ('bearing_cost', 'REAL DEFAULT 0'),
    ('optional_items_cost', 'REAL DEFAULT 0'),
    ('flex_connectors_cost', 'REAL DEFAULT 0'),
    ('bought_out_cost', 'REAL DEFAULT 0'),
    ('total_cost', 'REAL DEFAULT 0'),
    
    # Price and margin information
    ('fabrication_selling_price', 'REAL DEFAULT 0'),
    ('bought_out_selling_price', 'REAL DEFAULT 0'),
    ('total_selling_price', 'REAL DEFAULT 0'),
    ('total_job_margin', 'REAL DEFAULT 0'),
    ('fabrication_margin', 'REAL DEFAULT 0'),
    ('bought_out_margin', 'REAL DEFAULT 0'),
    
    # Component details
    ('vibration_isolators', 'TEXT'),
    ('drive_pack_kw', 'REAL DEFAULT 0'),
    ('custom_accessories', 'TEXT'),
    ('optional_items', 'TEXT'),
    ('custom_option_items', 'TEXT'),
    
    # Motor information
    ('motor_kw', 'REAL DEFAULT 0'),
    ('motor_brand', 'TEXT'),
    ('motor_pole', 'REAL DEFAULT 0'),
    ('motor_efficiency', 'TEXT'),
    ('motor_discount_rate', 'REAL DEFAULT 0'),
    
    # Bearing information
    ('bearing_brand', 'TEXT'),
    ('shaft_diameter', 'REAL DEFAULT 0'),
    
    # Configuration values
    ('no_of_isolators', 'INTEGER DEFAULT 0'),
    ('custom_no_of_isolators', 'INTEGER DEFAULT 0'),
    ('custom_shaft_diameter', 'REAL DEFAULT 0'),
    
    # Custom material columns (0-4)
    ('material_name_0', 'TEXT'),
    ('material_weight_0', 'REAL DEFAULT 0'),
    ('material_rate_0', 'REAL DEFAULT 0'),
    ('material_name_1', 'TEXT'),
    ('material_weight_1', 'REAL DEFAULT 0'),
    ('material_rate_1', 'REAL DEFAULT 0'),
    ('material_name_2', 'TEXT'),
    ('material_weight_2', 'REAL DEFAULT 0'),
    ('material_rate_2', 'REAL DEFAULT 0'),
    ('material_name_3', 'TEXT'),
    ('material_weight_3', 'REAL DEFAULT 0'),
    ('material_rate_3', 'REAL DEFAULT 0'),
    ('material_name_4', 'TEXT'),
    ('material_weight_4', 'REAL DEFAULT 0'),
    ('material_rate_4', 'REAL DEFAULT 0'),
    
    # Specific optional items
    ('amca_spark_proof', 'BOOLEAN DEFAULT 0'),
    ('amca_spark_proof_cost', 'REAL DEFAULT 0'),
    
    # JSON storage for all optional items
    ('optional_items_json', 'TEXT'),
    ('custom_optional_items_json', 'TEXT')
]

def update_projectfans_schema():
    """
    Update the ProjectFans table schema in all databases.
    """
    success_count = 0
    total_dbs = 0
    
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            logger.warning(f"Database {db_path} not found, skipping...")
            continue
        
        total_dbs += 1
        logger.info(f"Processing database: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if ProjectFans table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
            if not cursor.fetchone():
                logger.warning(f"ProjectFans table does not exist in {db_path}, creating it...")
                create_projectfans_table(cursor)
            else:
                # Add missing columns
                add_missing_columns(cursor, db_path)
            
            conn.commit()
            
            # Verify table schema
            cursor.execute("PRAGMA table_info(ProjectFans)")
            columns = cursor.fetchall()
            logger.info(f"ProjectFans table in {db_path} now has {len(columns)} columns")
            
            conn.close()
            success_count += 1
            logger.info(f"Successfully updated schema in {db_path}")
            
        except Exception as e:
            logger.error(f"Error updating schema in {db_path}: {str(e)}", exc_info=True)
    
    logger.info(f"Schema update completed. Successfully updated {success_count} out of {total_dbs} databases.")
    return success_count == total_dbs

def create_projectfans_table(cursor):
    """
    Create the ProjectFans table with all required columns.
    """
    columns_str = ", ".join([f"{col[0]} {col[1]}" for col in REQUIRED_COLUMNS])
    
    sql = f"""
    CREATE TABLE ProjectFans (
        {columns_str},
        FOREIGN KEY (enquiry_number) REFERENCES Projects(enquiry_number)
    )
    """
    
    cursor.execute(sql)
    logger.info("Created ProjectFans table with all required columns")

def add_missing_columns(cursor, db_path):
    """
    Add missing columns to the ProjectFans table.
    """
    # Get existing columns
    cursor.execute("PRAGMA table_info(ProjectFans)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    # Add missing columns
    added_columns = 0
    for col_name, col_type in REQUIRED_COLUMNS:
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE ProjectFans ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                logger.info(f"Added column {col_name} ({col_type}) to {db_path}")
                added_columns += 1
            except sqlite3.Error as e:
                logger.error(f"Error adding column {col_name}: {str(e)}")
    
    logger.info(f"Added {added_columns} missing columns to {db_path}")

def backup_database(db_path):
    """
    Create a backup of the database before making changes.
    """
    if not os.path.exists(db_path):
        logger.warning(f"Cannot backup {db_path} - file does not exist")
        return False
    
    backup_dir = "database_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = os.path.join(backup_dir, f"{os.path.basename(db_path)}_{timestamp}.bak")
    
    try:
        import shutil
        shutil.copy2(db_path, backup_filename)
        logger.info(f"Created backup of {db_path} at {backup_filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {db_path}: {str(e)}")
        return False

def check_optional_items_data():
    """
    Check if existing optional items data needs migration to the new format.
    """
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if optional_items column has data
            cursor.execute("SELECT COUNT(*) FROM ProjectFans WHERE optional_items IS NOT NULL AND optional_items != ''")
            count = cursor.fetchone()[0]
            
            if count > 0:
                logger.info(f"Found {count} rows with optional_items data in {db_path}")
                
                # Check if we have the JSON columns
                cursor.execute("PRAGMA table_info(ProjectFans)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'optional_items_json' in columns and 'custom_optional_items_json' in columns:
                    # Migrate data to JSON columns
                    cursor.execute("""
                        SELECT id, optional_items, custom_option_items FROM ProjectFans 
                        WHERE (optional_items IS NOT NULL AND optional_items != '')
                        OR (custom_option_items IS NOT NULL AND custom_option_items != '')
                    """)
                    
                    rows = cursor.fetchall()
                    migrated = 0
                    
                    for row in rows:
                        row_id, optional_items, custom_items = row
                        
                        # Parse optional items
                        opt_items_json = {}
                        if optional_items and optional_items.strip():
                            try:
                                opt_items_json = json.loads(optional_items)
                            except json.JSONDecodeError:
                                logger.warning(f"Could not parse optional_items for row {row_id}: {optional_items}")
                        
                        # Parse custom items
                        custom_items_json = {}
                        if custom_items and custom_items.strip():
                            try:
                                custom_items_json = json.loads(custom_items)
                            except json.JSONDecodeError:
                                logger.warning(f"Could not parse custom_option_items for row {row_id}: {custom_items}")
                        
                        # Check for AMCA Spark Proof Construction
                        amca_spark_proof = 0
                        amca_spark_proof_cost = 0
                        
                        for key, value in opt_items_json.items():
                            if 'amca' in key.lower() and 'spark' in key.lower():
                                amca_spark_proof = 1
                                if isinstance(value, (int, float)) and value > 0:
                                    amca_spark_proof_cost = value
                        
                        for key, value in custom_items_json.items():
                            if 'amca' in key.lower() and 'spark' in key.lower():
                                amca_spark_proof = 1
                                if isinstance(value, (int, float)) and value > 0:
                                    amca_spark_proof_cost = value
                        
                        # Update the row
                        cursor.execute("""
                            UPDATE ProjectFans SET 
                            optional_items_json = ?,
                            custom_optional_items_json = ?,
                            amca_spark_proof = ?,
                            amca_spark_proof_cost = ?
                            WHERE id = ?
                        """, (
                            json.dumps(opt_items_json),
                            json.dumps(custom_items_json),
                            amca_spark_proof,
                            amca_spark_proof_cost,
                            row_id
                        ))
                        
                        migrated += 1
                    
                    conn.commit()
                    logger.info(f"Migrated optional items data for {migrated} rows in {db_path}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking optional items in {db_path}: {str(e)}")

if __name__ == "__main__":
    print("Starting ProjectFans schema update...")
    
    # Backup databases first
    for db_path in DB_PATHS:
        if os.path.exists(db_path):
            backup_database(db_path)
    
    # Update schemas
    if update_projectfans_schema():
        print("Schema update successful!")
        
        # Check and migrate optional items data
        check_optional_items_data()
        
        print("All operations completed successfully.")
    else:
        print("Schema update encountered some issues. Check the log file for details.") 