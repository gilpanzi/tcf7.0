#!/usr/bin/env python3
"""
Add sample optional items data to the database to demonstrate the functionality.
"""

import sqlite3
import json
import os
import random
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
]

# List of standard optional items with their costs
STANDARD_OPTIONAL_ITEMS = {
    'amca_spark_proof': {'name': 'AMCA Type C Spark Proof Construction', 'cost': 15000},
    'flanges': {'name': 'Flanges', 'cost': 2500},
    'inlet_box': {'name': 'Inlet Box', 'cost': 3500},
    'inlet_guard': {'name': 'Inlet Guard', 'cost': 1800},
    'outlet_guard': {'name': 'Outlet Guard', 'cost': 1800},
    'inspection_door': {'name': 'Inspection Door', 'cost': 2200},
    'weather_cover': {'name': 'Weather Cover', 'cost': 4000},
    'drain_plug': {'name': 'Drain Plug', 'cost': 1000},
    'anti_vibration_mounts': {'name': 'Anti-Vibration Mounts', 'cost': 3000},
    'flexible_connector': {'name': 'Flexible Connector', 'cost': 2500},
    'companion_flanges': {'name': 'Companion Flanges', 'cost': 2000},
    'bellmouth_inlet': {'name': 'Bellmouth Inlet', 'cost': 3200},
    'access_door': {'name': 'Access Door', 'cost': 2200},
    'atex_certification': {'name': 'ATEX Certification', 'cost': 8000},
    'special_paint_finish': {'name': 'Special Paint Finish', 'cost': 4500}
}

def add_sample_optional_items():
    """
    Add sample optional items data to the database.
    """
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            logger.warning(f"Database {db_path} not found, skipping...")
            continue
        
        logger.info(f"Adding sample optional items to {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get a list of existing ProjectFans records
            cursor.execute("SELECT id, enquiry_number, fan_number FROM ProjectFans LIMIT 10")
            fan_records = cursor.fetchall()
            
            if not fan_records:
                logger.warning(f"No fan records found in {db_path}, skipping...")
                continue
            
            # Update each record with sample optional items
            for fan_id, enquiry_number, fan_number in fan_records:
                # Select 3-5 random optional items for each fan
                num_items = random.randint(3, 5)
                selected_items = random.sample(list(STANDARD_OPTIONAL_ITEMS.keys()), num_items)
                
                # Always include AMCA spark proof construction
                if 'amca_spark_proof' not in selected_items:
                    selected_items.append('amca_spark_proof')
                
                # Create JSON objects for optional items
                optional_items = {}
                optional_items_cost = 0
                
                for item_key in selected_items:
                    item = STANDARD_OPTIONAL_ITEMS[item_key]
                    optional_items[item_key] = item['cost']
                    optional_items_cost += item['cost']
                
                # Create a separate dictionary for AMCA spark proof
                amca_item = STANDARD_OPTIONAL_ITEMS['amca_spark_proof']
                
                # Update the database record
                cursor.execute("""
                    UPDATE ProjectFans SET
                    optional_items = ?,
                    optional_items_json = ?,
                    optional_items_cost = ?,
                    amca_spark_proof = 1,
                    amca_spark_proof_cost = ?
                    WHERE id = ?
                """, (
                    json.dumps(optional_items),
                    json.dumps(optional_items),
                    optional_items_cost,
                    amca_item['cost'],
                    fan_id
                ))
                
                logger.info(f"Updated fan ID {fan_id} (Enquiry: {enquiry_number}, Fan: {fan_number}) with {len(selected_items)} optional items")
            
            conn.commit()
            logger.info(f"Successfully added sample optional items to {len(fan_records)} fans in {db_path}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding sample optional items to {db_path}: {str(e)}")

if __name__ == "__main__":
    print("Adding sample optional items to the database...")
    add_sample_optional_items()
    print("Done!") 