#!/usr/bin/env python3
"""
Add sample entries for all optional items shown in the UI dialog box.
This ensures that all optional items from the dropdown are properly represented in the database.
"""

import sqlite3
import json
import os
import random
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
    {'key': 'flex_connectors', 'name': 'Flex Connectors', 'cost': 2500},
    {'key': 'silencer', 'name': 'Silencer', 'cost': 5000},
    {'key': 'testing_charges', 'name': 'Testing Charges', 'cost': 3000},
    {'key': 'freight_charges', 'name': 'Freight Charges', 'cost': 2000},
    {'key': 'warranty_charges', 'name': 'Warranty Charges', 'cost': 1500},
    {'key': 'packing_charges', 'name': 'Packing Charges', 'cost': 1200},
    {'key': 'amca_spark_proof', 'name': 'AMCA Type C Spark Proof Construction', 'cost': 15000},
    {'key': 'accessories_assembly_charges', 'name': 'Accessories Assembly Charges', 'cost': 3000},
    {'key': 'special_paint_specification', 'name': 'Special Paint Specification', 'cost': 4500},
    {'key': 'special_documentation', 'name': 'Special Documentation', 'cost': 2000},
    {'key': 'custom_item', 'name': 'Custom Item Example', 'cost': 5000}
]

def add_dialog_optional_items():
    """
    Add sample entries for all optional items shown in the UI dialog box.
    """
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            logger.warning(f"Database {db_path} not found, skipping...")
            continue
        
        logger.info(f"Adding dialog optional items to {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get a list of existing ProjectFans records
            cursor.execute("SELECT id, enquiry_number, fan_number FROM ProjectFans LIMIT 10")
            fan_records = cursor.fetchall()
            
            if not fan_records:
                logger.warning(f"No fan records found in {db_path}, skipping...")
                continue
            
            # Process each fan record
            for fan_id, enquiry_number, fan_number in fan_records:
                # Select 3-5 random optional items for each fan
                num_items = random.randint(3, 5)
                selected_items = random.sample(DIALOG_OPTIONAL_ITEMS, num_items)
                
                # Create dictionary for optional items
                optional_items = {}
                optional_items_cost = 0
                
                # Always include AMCA Type C Spark Proof Construction
                amca_item = next((item for item in DIALOG_OPTIONAL_ITEMS if item['key'] == 'amca_spark_proof'), None)
                if amca_item and not any(item['key'] == 'amca_spark_proof' for item in selected_items):
                    selected_items.append(amca_item)
                
                # Add all selected items to the dictionary
                for item in selected_items:
                    optional_items[item['key']] = item['cost']
                    optional_items_cost += item['cost']
                
                # Update specific boolean flags
                amca_spark_proof = 1 if any(item['key'] == 'amca_spark_proof' for item in selected_items) else 0
                has_silencer = 1 if any(item['key'] == 'silencer' for item in selected_items) else 0
                has_special_paint = 1 if any(item['key'] == 'special_paint_specification' for item in selected_items) else 0
                
                # Get specific costs
                amca_cost = next((item['cost'] for item in selected_items if item['key'] == 'amca_spark_proof'), 0)
                silencer_cost = next((item['cost'] for item in selected_items if item['key'] == 'silencer'), 0)
                special_paint_cost = next((item['cost'] for item in selected_items if item['key'] == 'special_paint_specification'), 0)
                
                # Update the database record with all required fields
                cursor.execute("""
                    UPDATE ProjectFans SET
                    optional_items = ?,
                    optional_items_json = ?,
                    optional_items_cost = ?,
                    amca_spark_proof = ?,
                    amca_spark_proof_cost = ?,
                    has_silencer = ?,
                    silencer_cost = ?,
                    has_special_paint = ?,
                    special_paint_cost = ?
                    WHERE id = ?
                """, (
                    json.dumps(optional_items),
                    json.dumps(optional_items),
                    optional_items_cost,
                    amca_spark_proof,
                    amca_cost,
                    has_silencer,
                    silencer_cost,
                    has_special_paint,
                    special_paint_cost,
                    fan_id
                ))
                
                # Log the selected items
                item_names = [item['name'] for item in selected_items]
                logger.info(f"Updated fan ID {fan_id} (Enquiry: {enquiry_number}, Fan: {fan_number}) with {len(selected_items)} optional items: {', '.join(item_names)}")
            
            conn.commit()
            logger.info(f"Successfully added dialog optional items to {len(fan_records)} fans in {db_path}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding dialog optional items to {db_path}: {str(e)}")

def verify_dialog_items():
    """
    Verify that all dialog items are properly stored in the database.
    """
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue
        
        logger.info(f"Verifying dialog items in {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check which items are actually used
            cursor.execute("SELECT optional_items FROM ProjectFans WHERE optional_items IS NOT NULL AND optional_items != ''")
            rows = cursor.fetchall()
            
            used_items = set()
            for row in rows:
                try:
                    items = json.loads(row[0])
                    used_items.update(items.keys())
                except json.JSONDecodeError:
                    pass
            
            # Check which dialog items are used
            dialog_item_keys = [item['key'] for item in DIALOG_OPTIONAL_ITEMS]
            used_dialog_items = [key for key in used_items if key in dialog_item_keys]
            
            logger.info(f"Found {len(used_dialog_items)} out of {len(DIALOG_OPTIONAL_ITEMS)} dialog items in use")
            missing_items = [item['name'] for item in DIALOG_OPTIONAL_ITEMS if item['key'] not in used_dialog_items]
            
            if missing_items:
                logger.warning(f"Missing dialog items: {', '.join(missing_items)}")
            else:
                logger.info("All dialog items are represented in the database!")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error verifying dialog items in {db_path}: {str(e)}")

if __name__ == "__main__":
    print("Adding dialog optional items to database...")
    add_dialog_optional_items()
    verify_dialog_items()
    print("Dialog optional items added successfully!") 