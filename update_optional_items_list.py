#!/usr/bin/env python3
"""
Update the database to include all optional items shown in the UI dialog box.
This script ensures all optional items from the Add Optional Item dialog 
are properly represented in the database.
"""

import sqlite3
import json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define database paths
DB_PATHS = [
    'fan_pricing.db',  # Main application database
    os.path.join('data', 'fan_pricing.db'),  # Render path for main database
    os.path.join('data', 'central_database', 'all_projects.db')  # Central database
]

# Complete list of optional items from the UI dialog box
OPTIONAL_ITEMS = {
    'flex_connectors': {'name': 'Flex Connectors', 'cost': 2500},
    'silencer': {'name': 'Silencer', 'cost': 5000},
    'testing_charges': {'name': 'Testing Charges', 'cost': 3000},
    'freight_charges': {'name': 'Freight Charges', 'cost': 2000},
    'warranty_charges': {'name': 'Warranty Charges', 'cost': 1500},
    'packing_charges': {'name': 'Packing Charges', 'cost': 1200},
    'amca_spark_proof': {'name': 'AMCA Type C Spark Proof Construction', 'cost': 15000},
    'accessories_assembly_charges': {'name': 'Accessories Assembly Charges', 'cost': 3000},
    'special_paint_specification': {'name': 'Special Paint Specification', 'cost': 4500},
    'special_documentation': {'name': 'Special Documentation', 'cost': 2000},
    
    # Additional items from previous implementation that might still be relevant
    'flanges': {'name': 'Flanges', 'cost': 2500},
    'inlet_box': {'name': 'Inlet Box', 'cost': 3500},
    'inlet_guard': {'name': 'Inlet Guard', 'cost': 1800},
    'outlet_guard': {'name': 'Outlet Guard', 'cost': 1800},
    'inspection_door': {'name': 'Inspection Door', 'cost': 2200},
    'weather_cover': {'name': 'Weather Cover', 'cost': 4000},
    'drain_plug': {'name': 'Drain Plug', 'cost': 1000},
    'anti_vibration_mounts': {'name': 'Anti-Vibration Mounts', 'cost': 3000},
    'companion_flanges': {'name': 'Companion Flanges', 'cost': 2000},
    'bellmouth_inlet': {'name': 'Bellmouth Inlet', 'cost': 3200},
    'access_door': {'name': 'Access Door', 'cost': 2200},
    'atex_certification': {'name': 'ATEX Certification', 'cost': 8000}
}

# Check if we need to add specific columns for each optional item
def add_specific_columns():
    """
    Add specific columns for optional items that need individual tracking.
    """
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            logger.warning(f"Database {db_path} not found, skipping...")
            continue
        
        logger.info(f"Adding specific optional item columns to {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get current columns
            cursor.execute("PRAGMA table_info(ProjectFans)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Items that need specific columns
            special_items = {
                'amca_spark_proof': [
                    ('amca_spark_proof', 'BOOLEAN DEFAULT 0'),
                    ('amca_spark_proof_cost', 'REAL DEFAULT 0')
                ],
                'silencer': [
                    ('has_silencer', 'BOOLEAN DEFAULT 0'),
                    ('silencer_cost', 'REAL DEFAULT 0')
                ],
                'special_paint_specification': [
                    ('has_special_paint', 'BOOLEAN DEFAULT 0'),
                    ('special_paint_cost', 'REAL DEFAULT 0')
                ]
            }
            
            added_columns = 0
            for item_key, columns in special_items.items():
                for col_name, col_type in columns:
                    if col_name not in existing_columns:
                        try:
                            sql = f"ALTER TABLE ProjectFans ADD COLUMN {col_name} {col_type}"
                            cursor.execute(sql)
                            logger.info(f"Added column {col_name} ({col_type}) to {db_path}")
                            added_columns += 1
                        except sqlite3.Error as e:
                            logger.error(f"Error adding column {col_name}: {str(e)}")
            
            # Always ensure we have JSON columns for storing all optional items
            json_columns = [
                ('optional_items_json', 'TEXT'),
                ('custom_optional_items_json', 'TEXT')
            ]
            
            for col_name, col_type in json_columns:
                if col_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE ProjectFans ADD COLUMN {col_name} {col_type}"
                        cursor.execute(sql)
                        logger.info(f"Added column {col_name} ({col_type}) to {db_path}")
                        added_columns += 1
                    except sqlite3.Error as e:
                        logger.error(f"Error adding column {col_name}: {str(e)}")
            
            conn.commit()
            logger.info(f"Added {added_columns} specific optional item columns to {db_path}")
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating specific columns in {db_path}: {str(e)}")

def add_optional_items_metadata():
    """
    Store the complete list of optional items in a metadata table for reference.
    """
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            logger.warning(f"Database {db_path} not found, skipping...")
            continue
        
        logger.info(f"Adding optional items metadata to {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if the metadata table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='OptionalItemsMetadata'")
            if not cursor.fetchone():
                # Create the metadata table
                cursor.execute("""
                    CREATE TABLE OptionalItemsMetadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_key TEXT UNIQUE,
                        item_name TEXT,
                        default_cost REAL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info(f"Created OptionalItemsMetadata table in {db_path}")
            
            # Store or update each optional item
            for item_key, item_data in OPTIONAL_ITEMS.items():
                # Check if the item already exists
                cursor.execute("SELECT id FROM OptionalItemsMetadata WHERE item_key = ?", (item_key,))
                if cursor.fetchone():
                    # Update the existing item
                    cursor.execute("""
                        UPDATE OptionalItemsMetadata 
                        SET item_name = ?, default_cost = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE item_key = ?
                    """, (item_data['name'], item_data['cost'], item_key))
                else:
                    # Insert a new item
                    cursor.execute("""
                        INSERT INTO OptionalItemsMetadata (item_key, item_name, default_cost)
                        VALUES (?, ?, ?)
                    """, (item_key, item_data['name'], item_data['cost']))
                
            conn.commit()
            
            # Verify the data
            cursor.execute("SELECT COUNT(*) FROM OptionalItemsMetadata")
            count = cursor.fetchone()[0]
            logger.info(f"OptionalItemsMetadata table now has {count} items in {db_path}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding optional items metadata to {db_path}: {str(e)}")

def check_optional_items_count():
    """
    Check how many optional items are being used in existing records.
    """
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            logger.warning(f"Database {db_path} not found, skipping...")
            continue
        
        logger.info(f"Checking optional items usage in {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
            if not cursor.fetchone():
                logger.warning(f"ProjectFans table does not exist in {db_path}")
                continue
            
            # Get column names
            cursor.execute("PRAGMA table_info(ProjectFans)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Check for optional items in JSON format
            if 'optional_items' in columns:
                cursor.execute("SELECT id, optional_items FROM ProjectFans WHERE optional_items IS NOT NULL AND optional_items != ''")
                rows = cursor.fetchall()
                
                # Track which optional items are being used
                used_items = {}
                
                for row_id, optional_items in rows:
                    try:
                        items = json.loads(optional_items)
                        for item_key, item_cost in items.items():
                            if item_key not in used_items:
                                used_items[item_key] = 0
                            used_items[item_key] += 1
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse optional_items for row {row_id}")
                
                # Report usage
                logger.info(f"Found {len(used_items)} unique optional items in use in {db_path}")
                for item_key, count in used_items.items():
                    logger.info(f"  - '{item_key}' is used in {count} records")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking optional items count in {db_path}: {str(e)}")

if __name__ == "__main__":
    print("Updating optional items in database...")
    add_specific_columns()
    add_optional_items_metadata()
    check_optional_items_count()
    print("Optional items update completed successfully!") 