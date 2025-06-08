#!/usr/bin/env python3
"""
Verify that all optional items are properly supported in the database.
"""

import sqlite3
import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
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

# List of standard optional items to check for
STANDARD_OPTIONAL_ITEMS = [
    'AMCA Type C Spark Proof Construction',
    'Flanges',
    'Inlet Box',
    'Inlet Guard',
    'Outlet Guard',
    'Inspection Door',
    'Weather Cover',
    'Drain Plug',
    'Anti-Vibration Mounts',
    'Flexible Connector',
    'Companion Flanges',
    'Bellmouth Inlet',
    'Access Door',
    'ATEX Certification',
    'Special Paint Finish'
]

def verify_optional_items_support():
    """
    Verify that all optional items are properly supported in the database.
    """
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            logger.warning(f"Database {db_path} not found, skipping...")
            continue
        
        logger.info(f"Checking optional items support in {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if the ProjectFans table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
            if not cursor.fetchone():
                logger.warning(f"ProjectFans table does not exist in {db_path}")
                continue
            
            # Check for required columns
            cursor.execute("PRAGMA table_info(ProjectFans)")
            columns = [row[1] for row in cursor.fetchall()]
            
            required_columns = [
                'optional_items', 'custom_option_items', 'optional_items_cost',
                'optional_items_json', 'custom_optional_items_json', 'amca_spark_proof'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                logger.warning(f"Missing columns in {db_path}: {missing_columns}")
            else:
                logger.info(f"All required columns exist in {db_path}")
            
            # Check for existing data
            cursor.execute("SELECT COUNT(*) FROM ProjectFans")
            total_rows = cursor.fetchone()[0]
            
            if total_rows == 0:
                logger.info(f"No rows in ProjectFans table in {db_path}")
            else:
                logger.info(f"Found {total_rows} rows in ProjectFans table in {db_path}")
                
                # Check for AMCA Type C Spark Proof Construction (only if column exists)
                if 'amca_spark_proof' in columns:
                    cursor.execute("SELECT COUNT(*) FROM ProjectFans WHERE amca_spark_proof = 1")
                    amca_count = cursor.fetchone()[0]
                    logger.info(f"Found {amca_count} rows with AMCA Type C Spark Proof Construction in {db_path}")
                
                # Check for optional items (only if column exists)
                if 'optional_items' in columns:
                    cursor.execute("SELECT COUNT(*) FROM ProjectFans WHERE optional_items IS NOT NULL AND optional_items != ''")
                    optional_items_count = cursor.fetchone()[0]
                    logger.info(f"Found {optional_items_count} rows with optional items in {db_path}")
                
                # Check for custom optional items (only if column exists)
                if 'custom_option_items' in columns:
                    cursor.execute("SELECT COUNT(*) FROM ProjectFans WHERE custom_option_items IS NOT NULL AND custom_option_items != ''")
                    custom_items_count = cursor.fetchone()[0]
                    logger.info(f"Found {custom_items_count} rows with custom optional items in {db_path}")
                
                # Check for JSON columns (only if column exists)
                if 'optional_items_json' in columns:
                    cursor.execute("SELECT COUNT(*) FROM ProjectFans WHERE optional_items_json IS NOT NULL AND optional_items_json != ''")
                    json_count = cursor.fetchone()[0]
                    logger.info(f"Found {json_count} rows with JSON optional items in {db_path}")
                
                # Sample some data (dynamically build query based on available columns)
                query_columns = ['id', 'enquiry_number', 'fan_number']
                query_where_parts = []
                
                if 'optional_items' in columns:
                    query_columns.append('optional_items')
                    query_where_parts.append("(optional_items IS NOT NULL AND optional_items != '')")
                
                if 'custom_option_items' in columns:
                    query_columns.append('custom_option_items')
                    query_where_parts.append("(custom_option_items IS NOT NULL AND custom_option_items != '')")
                
                if 'optional_items_json' in columns:
                    query_columns.append('optional_items_json')
                
                if 'custom_optional_items_json' in columns:
                    query_columns.append('custom_optional_items_json')
                
                if 'amca_spark_proof' in columns:
                    query_columns.append('amca_spark_proof')
                    query_where_parts.append("amca_spark_proof = 1")
                
                if query_where_parts:
                    query = f"""
                        SELECT {', '.join(query_columns)}
                        FROM ProjectFans 
                        WHERE {' OR '.join(query_where_parts)}
                        LIMIT 5
                    """
                    
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        row_data = dict(zip(query_columns, row))
                        row_id = row_data.get('id')
                        enquiry_number = row_data.get('enquiry_number')
                        fan_number = row_data.get('fan_number')
                        
                        logger.info(f"Row {row_id} (Enquiry: {enquiry_number}, Fan: {fan_number}):")
                        
                        if 'amca_spark_proof' in row_data and row_data['amca_spark_proof']:
                            logger.info(f"  - Has AMCA Type C Spark Proof Construction")
                        
                        # Parse optional items
                        if 'optional_items' in row_data and row_data['optional_items']:
                            try:
                                opt_items = json.loads(row_data['optional_items'])
                                logger.info(f"  - Optional items: {opt_items}")
                            except json.JSONDecodeError:
                                logger.warning(f"  - Could not parse optional_items: {row_data['optional_items']}")
                        
                        # Parse custom items
                        if 'custom_option_items' in row_data and row_data['custom_option_items']:
                            try:
                                cust_items = json.loads(row_data['custom_option_items'])
                                logger.info(f"  - Custom optional items: {cust_items}")
                            except json.JSONDecodeError:
                                logger.warning(f"  - Could not parse custom_option_items: {row_data['custom_option_items']}")
                        
                        # Parse JSON optional items
                        if 'optional_items_json' in row_data and row_data['optional_items_json']:
                            try:
                                opt_json = json.loads(row_data['optional_items_json'])
                                logger.info(f"  - JSON optional items: {opt_json}")
                            except json.JSONDecodeError:
                                logger.warning(f"  - Could not parse optional_items_json: {row_data['optional_items_json']}")
                        
                        # Parse JSON custom items
                        if 'custom_optional_items_json' in row_data and row_data['custom_optional_items_json']:
                            try:
                                cust_json = json.loads(row_data['custom_optional_items_json'])
                                logger.info(f"  - JSON custom optional items: {cust_json}")
                            except json.JSONDecodeError:
                                logger.warning(f"  - Could not parse custom_optional_items_json: {row_data['custom_optional_items_json']}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking optional items in {db_path}: {str(e)}")

def check_standard_items_coverage():
    """
    Check if all standard optional items are covered in the database.
    """
    print("\n=== Checking Standard Optional Items Coverage ===")
    
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            print(f"\nChecking {db_path}:")
            
            # Get column names first
            cursor.execute("PRAGMA table_info(ProjectFans)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Build query based on available columns
            query_columns = []
            
            if 'optional_items' in columns:
                query_columns.append('optional_items')
            
            if 'custom_option_items' in columns:
                query_columns.append('custom_option_items')
            
            if 'optional_items_json' in columns:
                query_columns.append('optional_items_json')
            
            if 'custom_optional_items_json' in columns:
                query_columns.append('custom_optional_items_json')
            
            if not query_columns:
                print(f"No optional items columns found in {db_path}")
                continue
            
            # Build WHERE clause
            where_parts = []
            for col in query_columns:
                where_parts.append(f"({col} IS NOT NULL AND {col} != '')")
            
            query = f"""
                SELECT {', '.join(query_columns)}
                FROM ProjectFans 
                WHERE {' OR '.join(where_parts)}
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Track which standard items have been found
            found_items = set()
            
            for row in rows:
                # Map column names to row values
                row_data = dict(zip(query_columns, row))
                
                # Check in all columns
                for col, items_str in row_data.items():
                    if not items_str:
                        continue
                    
                    try:
                        items_dict = json.loads(items_str)
                        
                        # Check each item key
                        for item_key in items_dict.keys():
                            # Normalize the item key for comparison
                            normalized_key = item_key.replace('_', ' ').lower()
                            
                            # Check against standard items
                            for std_item in STANDARD_OPTIONAL_ITEMS:
                                if std_item.lower() in normalized_key:
                                    found_items.add(std_item)
                    except json.JSONDecodeError:
                        # Handle non-JSON strings (might contain item names)
                        for std_item in STANDARD_OPTIONAL_ITEMS:
                            if std_item.lower() in items_str.lower():
                                found_items.add(std_item)
            
            # Report findings
            missing_items = [item for item in STANDARD_OPTIONAL_ITEMS if item not in found_items]
            
            print(f"Found {len(found_items)} out of {len(STANDARD_OPTIONAL_ITEMS)} standard optional items")
            print(f"Found items: {sorted(found_items)}")
            
            if missing_items:
                print(f"Missing items: {missing_items}")
            else:
                print("All standard optional items are covered!")
            
            conn.close()
            
        except Exception as e:
            print(f"Error checking standard items in {db_path}: {str(e)}")

if __name__ == "__main__":
    print("=== Verifying Optional Items Support in Database ===")
    verify_optional_items_support()
    check_standard_items_coverage()
    print("\nVerification complete!") 