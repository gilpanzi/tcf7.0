#!/usr/bin/env python3
"""
Verify that all optional items from the dialog box are correctly represented in the database.
This script checks both the database schema and the data to ensure everything is properly stored.
"""

import sqlite3
import json
import os
import logging

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
]

# All optional items from the UI dialog box
DIALOG_OPTIONAL_ITEMS = [
    {'key': 'flex_connectors', 'name': 'Flex Connectors'},
    {'key': 'silencer', 'name': 'Silencer'},
    {'key': 'testing_charges', 'name': 'Testing Charges'},
    {'key': 'freight_charges', 'name': 'Freight Charges'},
    {'key': 'warranty_charges', 'name': 'Warranty Charges'},
    {'key': 'packing_charges', 'name': 'Packing Charges'},
    {'key': 'amca_spark_proof', 'name': 'AMCA Type C Spark Proof Construction'},
    {'key': 'accessories_assembly_charges', 'name': 'Accessories Assembly Charges'},
    {'key': 'special_paint_specification', 'name': 'Special Paint Specification'},
    {'key': 'special_documentation', 'name': 'Special Documentation'},
    {'key': 'custom_item', 'name': 'Custom Item'}
]

def verify_database_schema():
    """
    Verify that the database schema includes all necessary columns for storing optional items.
    """
    print("\n=== Verifying Database Schema ===")
    
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            print(f"Database {db_path} not found, skipping...")
            continue
        
        print(f"\nExamining schema in {db_path}:")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if the ProjectFans table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
            if not cursor.fetchone():
                print(f"ProjectFans table does not exist in {db_path}")
                continue
            
            # Check for required columns
            cursor.execute("PRAGMA table_info(ProjectFans)")
            columns = [row[1] for row in cursor.fetchall()]
            
            required_columns = [
                'optional_items', 'optional_items_json', 'optional_items_cost',
                'amca_spark_proof', 'amca_spark_proof_cost',
                'has_silencer', 'silencer_cost',
                'has_special_paint', 'special_paint_cost'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"Missing required columns: {', '.join(missing_columns)}")
            else:
                print("All required columns are present in the schema!")
            
            # Check if the metadata table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='OptionalItemsMetadata'")
            if not cursor.fetchone():
                print(f"OptionalItemsMetadata table does not exist in {db_path}")
            else:
                # Check metadata entries
                cursor.execute("SELECT COUNT(*) FROM OptionalItemsMetadata")
                count = cursor.fetchone()[0]
                print(f"OptionalItemsMetadata table has {count} entries")
                
                # Sample a few entries
                cursor.execute("SELECT item_key, item_name, default_cost FROM OptionalItemsMetadata LIMIT 5")
                print("\nSample metadata entries:")
                for row in cursor.fetchall():
                    print(f"  {row[0]}: {row[1]} (Default cost: {row[2]})")
            
            conn.close()
            
        except Exception as e:
            print(f"Error verifying schema in {db_path}: {str(e)}")

def verify_dialog_items_in_data():
    """
    Verify that all dialog items are present in the actual data.
    """
    print("\n=== Verifying Dialog Items in Data ===")
    
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            print(f"Database {db_path} not found, skipping...")
            continue
        
        print(f"\nExamining data in {db_path}:")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check which items are actually used
            cursor.execute("SELECT optional_items FROM ProjectFans WHERE optional_items IS NOT NULL AND optional_items != ''")
            rows = cursor.fetchall()
            
            if not rows:
                print("No optional items data found")
                continue
            
            used_items = {}
            for row in rows:
                try:
                    items = json.loads(row[0])
                    for key, value in items.items():
                        if key not in used_items:
                            used_items[key] = {'count': 0, 'total_cost': 0}
                        used_items[key]['count'] += 1
                        if isinstance(value, (int, float)):
                            used_items[key]['total_cost'] += value
                except json.JSONDecodeError:
                    print(f"Could not parse optional_items: {row[0]}")
            
            # Check which dialog items are used
            dialog_item_keys = [item['key'] for item in DIALOG_OPTIONAL_ITEMS]
            used_dialog_items = [key for key in used_items.keys() if key in dialog_item_keys]
            
            print(f"Found {len(used_dialog_items)} out of {len(DIALOG_OPTIONAL_ITEMS)} dialog items in use")
            
            # List all used items
            print("\nUsed optional items:")
            for key, data in used_items.items():
                item_name = next((item['name'] for item in DIALOG_OPTIONAL_ITEMS if item['key'] == key), key)
                print(f"  {item_name}: Used in {data['count']} records, Total cost: {data['total_cost']}")
            
            # List missing items
            missing_items = [item['name'] for item in DIALOG_OPTIONAL_ITEMS if item['key'] not in used_dialog_items]
            if missing_items:
                print(f"\nMissing dialog items: {', '.join(missing_items)}")
            else:
                print("\nAll dialog items are represented in the data!")
            
            # Check for special columns with data
            special_columns = [
                ('amca_spark_proof', 'AMCA Type C Spark Proof Construction'),
                ('has_silencer', 'Silencer'),
                ('has_special_paint', 'Special Paint Specification')
            ]
            
            print("\nSpecial column usage:")
            for col_name, item_name in special_columns:
                cursor.execute(f"SELECT COUNT(*) FROM ProjectFans WHERE {col_name} = 1")
                count = cursor.fetchone()[0]
                print(f"  {item_name}: {count} records have this item enabled")
            
            conn.close()
            
        except Exception as e:
            print(f"Error verifying data in {db_path}: {str(e)}")

def show_sample_record():
    """
    Show a sample record with optional items to demonstrate the data structure.
    """
    print("\n=== Sample Record with Optional Items ===")
    
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get a sample record with optional items
            cursor.execute("""
                SELECT id, enquiry_number, fan_number, optional_items, optional_items_json, optional_items_cost,
                       amca_spark_proof, amca_spark_proof_cost, has_silencer, silencer_cost, 
                       has_special_paint, special_paint_cost
                FROM ProjectFans 
                WHERE optional_items IS NOT NULL AND optional_items != ''
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if not row:
                print(f"No records with optional items found in {db_path}")
                continue
            
            print(f"\nSample record from {db_path}:")
            print(f"Fan ID: {row[0]}, Enquiry: {row[1]}, Fan Number: {row[2]}")
            
            # Parse and display optional items
            optional_items = json.loads(row[3])
            print(f"Optional Items Cost: {row[5]}")
            print("\nOptional Items:")
            
            for key, cost in optional_items.items():
                item_name = next((item['name'] for item in DIALOG_OPTIONAL_ITEMS if item['key'] == key), key)
                print(f"  {item_name}: {cost}")
            
            # Display special flags
            print("\nSpecial Flags:")
            print(f"  AMCA Type C Spark Proof Construction: {'Yes' if row[6] == 1 else 'No'} (Cost: {row[7]})")
            print(f"  Silencer: {'Yes' if row[8] == 1 else 'No'} (Cost: {row[9]})")
            print(f"  Special Paint: {'Yes' if row[10] == 1 else 'No'} (Cost: {row[11]})")
            
            conn.close()
            
        except Exception as e:
            print(f"Error showing sample record from {db_path}: {str(e)}")

if __name__ == "__main__":
    print("Verifying dialog items implementation in database...")
    verify_database_schema()
    verify_dialog_items_in_data()
    show_sample_record()
    print("\nVerification complete!") 