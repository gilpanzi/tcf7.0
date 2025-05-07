#!/usr/bin/env python3
"""
Utility script to update database schema
"""

import sqlite3
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_path():
    """Determine the database path based on environment"""
    # Use 'data/fan_pricing.db' for Render's persistent disk
    db_path = os.path.join('data', 'fan_pricing.db')
    
    # If the data directory doesn't exist or the database doesn't exist there,
    # fall back to the original location
    if not os.path.exists(db_path):
        if os.path.exists('fan_pricing.db'):
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            logger.info(f"Data directory created at {os.path.abspath('data')}")
            db_path = 'fan_pricing.db'
        else:
            db_path = 'fan_pricing.db'
            logger.info(f"Using database at root path: {db_path}")
    
    return db_path 

def update_schema():
    """Apply schema updates to the database."""
    try:
        # Read schema file
        if not os.path.exists('schema.sql'):
            logger.error("schema.sql file not found")
            return False
        
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
        
        logger.info("Schema file read successfully")
        
        # Connect to database
        db_path = get_db_path()
        logger.info(f"Connecting to database at {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_before = [row[0] for row in cursor.fetchall()]
        logger.info(f"Tables before update: {tables_before}")
        
        # Execute schema SQL
        cursor.executescript(schema_sql)
        logger.info("Schema SQL executed")
        
        # Get tables after update
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_after = [row[0] for row in cursor.fetchall()]
        logger.info(f"Tables after update: {tables_after}")
        
        # Check if any new tables were created
        new_tables = [table for table in tables_after if table not in tables_before]
        if new_tables:
            logger.info(f"New tables created: {new_tables}")
        
        # Check for uppercase tables and handle data migration if needed
        if 'Projects' in tables_after and 'projects' in tables_after:
            logger.info("Both 'Projects' and 'projects' tables found - checking data migration")
            
            # Check if Projects has data that needs to be migrated
            cursor.execute("SELECT COUNT(*) FROM Projects")
            projects_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM projects")
            projects_lowercase_count = cursor.fetchone()[0]
            
            if projects_count > 0 and projects_lowercase_count == 0:
                logger.info(f"Migrating {projects_count} records from 'Projects' to 'projects'")
                
                # Get columns from Projects table
                cursor.execute("PRAGMA table_info(Projects)")
                projects_columns = [row[1] for row in cursor.fetchall()]
                
                # Get columns from projects table
                cursor.execute("PRAGMA table_info(projects)")
                lowercase_columns = [row[1] for row in cursor.fetchall()]
                
                # Find common columns
                common_columns = [col for col in projects_columns if col.lower() in [c.lower() for c in lowercase_columns]]
                columns_str = ", ".join(common_columns)
                
                # Insert data from Projects to projects
                cursor.execute(f"INSERT INTO projects ({columns_str}) SELECT {columns_str} FROM Projects")
                logger.info(f"Migrated data from 'Projects' to 'projects'")
                
                # Do the same for Fans tables if they exist
                if 'ProjectFans' in tables_after and 'fans' in tables_after:
                    cursor.execute("SELECT COUNT(*) FROM ProjectFans")
                    fans_count = cursor.fetchone()[0]
                    
                    if fans_count > 0:
                        logger.info("Migrating fan data to new schema")
                        
                        # Get all fans data
                        cursor.execute("""
                            SELECT pf.project_id, pf.fan_number, 
                                   pf.fan_model, pf.fan_size, pf.class, pf.arrangement, pf.vendor, pf.material,
                                   pf.bare_fan_weight, pf.accessory_weights, pf.total_weight,
                                   pf.fabrication_cost, pf.bought_out_cost, pf.total_cost,
                                   pf.accessories, pf.bearing_brand, pf.shaft_diameter,
                                   pf.motor_brand, pf.motor_kw, pf.pole, pf.efficiency, pf.optional_items
                            FROM ProjectFans pf
                        """)
                        fan_data = cursor.fetchall()
                        
                        for fan in fan_data:
                            project_id, fan_number = fan[0], fan[1]
                            
                            # Create JSON structures
                            specs = {
                                'fan_model': fan[2] if fan[2] else '',
                                'fan_size': fan[3] if fan[3] else '',
                                'class': fan[4] if fan[4] else '',
                                'arrangement': fan[5] if fan[5] else '',
                                'vendor': fan[6] if fan[6] else '',
                                'material': fan[7] if fan[7] else '',
                                'accessories': fan[14] if fan[14] else '',
                                'bearing_brand': fan[15] if fan[15] else '',
                                'shaft_diameter': fan[16] if fan[16] else 0,
                                'optional_items': fan[21] if fan[21] else ''
                            }
                            
                            weights = {
                                'bare_fan_weight': fan[8] if fan[8] else 0,
                                'accessory_weight': fan[9] if fan[9] else 0,
                                'total_weight': fan[10] if fan[10] else 0,
                                'fabrication_weight': 0,
                                'bought_out_weight': 0
                            }
                            
                            costs = {
                                'fabrication_cost': fan[11] if fan[11] else 0,
                                'bought_out_cost': fan[12] if fan[12] else 0,
                                'total_cost': fan[13] if fan[13] else 0,
                                'fabrication_selling_price': 0,
                                'bought_out_selling_price': 0,
                                'total_selling_price': 0,
                                'total_job_margin': 0
                            }
                            
                            motor = {
                                'brand': fan[17] if fan[17] else '',
                                'kw': fan[18] if fan[18] else 0,
                                'pole': fan[19] if fan[19] else '',
                                'efficiency': fan[20] if fan[20] else '',
                                'discount_rate': 0
                            }
                            
                            # Convert to JSON
                            specs_json = json.dumps(specs)
                            weights_json = json.dumps(weights)
                            costs_json = json.dumps(costs)
                            motor_json = json.dumps(motor)
                            
                            # Insert into new fans table
                            cursor.execute("""
                                INSERT INTO fans (project_id, fan_number, specifications, weights, costs, motor)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (project_id, fan_number, specs_json, weights_json, costs_json, motor_json))
                        
                        logger.info(f"Migrated {len(fan_data)} fans to new schema")
        
        # Commit changes
        conn.commit()
        logger.info("Schema update committed to database")
        
        # Close connection
        conn.close()
        logger.info("Database connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error updating schema: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if update_schema():
        print("Schema updated successfully")
    else:
        print("Schema update failed") 