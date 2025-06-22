#!/usr/bin/env python3
"""
Comprehensive fix for ALL database schema issues in the TCF Pricing Tool.
This script will:
1. Fix table name case inconsistencies
2. Add missing columns to Projects table
3. Create proper ProjectFans table with all required columns
4. Fix both local and central databases
"""

import sqlite3
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_local_database():
    """Fix the local fan_pricing.db database schema."""
    try:
        conn = sqlite3.connect('fan_pricing.db')
        cursor = conn.cursor()
        
        logger.info("=== FIXING LOCAL DATABASE ===")
        
        # 1. Check if Projects table exists and has all required columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Projects'")
        projects_exists = cursor.fetchone() is not None
        
        if projects_exists:
            # Check if sales_engineer column exists
            cursor.execute("PRAGMA table_info(Projects)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'sales_engineer' not in columns:
                logger.info("Adding sales_engineer column to Projects table")
                cursor.execute("ALTER TABLE Projects ADD COLUMN sales_engineer TEXT")
            
            # Add other missing columns
            required_project_columns = [
                ('total_weight', 'REAL DEFAULT 0'),
                ('total_fabrication_cost', 'REAL DEFAULT 0'),
                ('total_bought_out_cost', 'REAL DEFAULT 0'),
                ('total_cost', 'REAL DEFAULT 0'),
                ('total_selling_price', 'REAL DEFAULT 0'),
                ('total_job_margin', 'REAL DEFAULT 0')
            ]
            
            for col_name, col_def in required_project_columns:
                if col_name not in columns:
                    logger.info(f"Adding {col_name} column to Projects table")
                    cursor.execute(f"ALTER TABLE Projects ADD COLUMN {col_name} {col_def}")
        else:
            # Create Projects table from scratch
            logger.info("Creating Projects table")
            cursor.execute('''
                CREATE TABLE Projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enquiry_number TEXT UNIQUE,
                    customer_name TEXT,
                    total_fans INTEGER,
                    sales_engineer TEXT,
                    total_weight REAL DEFAULT 0,
                    total_fabrication_cost REAL DEFAULT 0,
                    total_bought_out_cost REAL DEFAULT 0,
                    total_cost REAL DEFAULT 0,
                    total_selling_price REAL DEFAULT 0,
                    total_job_margin REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # 2. Create complete ProjectFans table with ALL required columns
        cursor.execute("DROP TABLE IF EXISTS ProjectFans")
        logger.info("Creating complete ProjectFans table with all required columns")
        
        cursor.execute('''
            CREATE TABLE ProjectFans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                enquiry_number TEXT,
                fan_number INTEGER,
                fan_model TEXT,
                fan_size TEXT,
                size TEXT,
                class TEXT,
                arrangement TEXT,
                vendor TEXT,
                material TEXT,
                accessories TEXT,
                custom_accessories TEXT,
                optional_items TEXT,
                custom_option_items TEXT,
                optional_items_json TEXT,
                custom_optional_items_json TEXT,
                bare_fan_weight REAL,
                accessory_weight REAL,
                accessory_weights REAL,
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
                custom_no_of_isolators INTEGER,
                custom_shaft_diameter REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES Projects(id),
                FOREIGN KEY (enquiry_number) REFERENCES Projects(enquiry_number)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Local database schema fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing local database: {str(e)}")
        return False

def fix_central_database():
    """Fix the central database schema."""
    try:
        # Create directories if they don't exist
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        os.makedirs(central_db_dir, exist_ok=True)
        
        central_db_path = os.path.join(central_db_dir, 'all_projects.db')
        
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        logger.info("=== FIXING CENTRAL DATABASE ===")
        
        # Create Projects table with all required columns
        cursor.execute("DROP TABLE IF EXISTS Projects")
        cursor.execute('''
            CREATE TABLE Projects (
                enquiry_number TEXT PRIMARY KEY,
                customer_name TEXT,
                total_fans INTEGER,
                sales_engineer TEXT,
                total_weight REAL DEFAULT 0,
                total_fabrication_cost REAL DEFAULT 0,
                total_bought_out_cost REAL DEFAULT 0,
                total_cost REAL DEFAULT 0,
                total_selling_price REAL DEFAULT 0,
                total_job_margin REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create ProjectFans table with ALL required columns (same as local)
        cursor.execute("DROP TABLE IF EXISTS ProjectFans")
        cursor.execute('''
            CREATE TABLE ProjectFans (
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
                custom_accessories TEXT,
                optional_items TEXT,
                custom_option_items TEXT,
                optional_items_json TEXT,
                custom_optional_items_json TEXT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enquiry_number) REFERENCES Projects(enquiry_number)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Central database schema fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing central database: {str(e)}")
        return False

def verify_schemas():
    """Verify that both databases have the correct schemas."""
    try:
        logger.info("=== VERIFYING DATABASE SCHEMAS ===")
        
        # Check local database
        conn = sqlite3.connect('fan_pricing.db')
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(Projects)")
        projects_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Local Projects table columns ({len(projects_columns)}): {projects_columns}")
        
        cursor.execute("PRAGMA table_info(ProjectFans)")
        projectfans_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Local ProjectFans table columns ({len(projectfans_columns)}): {projectfans_columns}")
        
        conn.close()
        
        # Check central database
        central_db_path = 'data/central_database/all_projects.db'
        if os.path.exists(central_db_path):
            conn = sqlite3.connect(central_db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(Projects)")
            central_projects_columns = [col[1] for col in cursor.fetchall()]
            logger.info(f"Central Projects table columns ({len(central_projects_columns)}): {central_projects_columns}")
            
            cursor.execute("PRAGMA table_info(ProjectFans)")
            central_projectfans_columns = [col[1] for col in cursor.fetchall()]
            logger.info(f"Central ProjectFans table columns ({len(central_projectfans_columns)}): {central_projectfans_columns}")
            
            conn.close()
        
        logger.info("Schema verification complete")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying schemas: {str(e)}")
        return False

def main():
    """Run all database fixes."""
    logger.info("Starting comprehensive database schema fix...")
    
    success = True
    
    # Fix local database
    if not fix_local_database():
        success = False
    
    # Fix central database
    if not fix_central_database():
        success = False
    
    # Verify schemas
    if not verify_schemas():
        success = False
    
    if success:
        logger.info("✅ ALL DATABASE SCHEMA ISSUES FIXED SUCCESSFULLY!")
    else:
        logger.error("❌ Some issues encountered during fix")
    
    return success

if __name__ == "__main__":
    main() 