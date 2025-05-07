import sqlite3
import os
import logging
import json
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def add_missing_columns():
    """Add missing columns to the ProjectFans table in the database."""
    try:
        # Use the data directory for the central database
        data_dir = 'data'
        central_db_path = os.path.join(data_dir, 'central_database', 'all_projects.db')
        
        # If the database doesn't exist in the data directory, check the original location
        if not os.path.exists(central_db_path):
            if os.path.exists('central_database/all_projects.db'):
                central_db_path = 'central_database/all_projects.db'
            else:
                logger.error("Central database not found")
                return False
        
        logger.info(f"Using central database at: {central_db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Get current columns in ProjectFans table
        cursor.execute("PRAGMA table_info(ProjectFans)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        logger.info(f"Existing columns in ProjectFans: {existing_columns}")
        
        # List of columns to add
        new_columns = [
            ('vibration_isolators', 'TEXT'),
            ('drive_pack_kw', 'REAL'),
            ('custom_accessories', 'TEXT'),
            ('optional_items', 'TEXT'),
            ('custom_option_items', 'TEXT'),
            ('motor_kw', 'REAL'),
            ('motor_brand', 'TEXT'),
            ('motor_pole', 'INTEGER'),
            ('motor_efficiency', 'REAL'),
            ('motor_discount_rate', 'REAL'),
            ('bearing_brand', 'TEXT')
        ]
        
        # Add each missing column
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                logger.info(f"Adding column {column_name} ({column_type}) to ProjectFans table")
                try:
                    cursor.execute(f"ALTER TABLE ProjectFans ADD COLUMN {column_name} {column_type}")
                    logger.info(f"Successfully added column {column_name}")
                except sqlite3.Error as e:
                    logger.error(f"Error adding column {column_name}: {str(e)}")
            else:
                logger.info(f"Column {column_name} already exists in ProjectFans table")
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        logger.info("Successfully updated ProjectFans table with new columns")
        return True
        
    except Exception as e:
        logger.error(f"Error updating ProjectFans table: {str(e)}", exc_info=True)
        return False

# Also modify the main database
def add_missing_columns_to_main_db():
    """Add missing columns to the ProjectFans table in the main database."""
    try:
        # Path to the main database
        db_path = 'fan_pricing.db'
        
        if not os.path.exists(db_path):
            logger.error("Main database not found")
            return False
        
        logger.info(f"Using main database at: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current columns in ProjectFans table
        cursor.execute("PRAGMA table_info(ProjectFans)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        logger.info(f"Existing columns in ProjectFans (main DB): {existing_columns}")
        
        # List of columns to add
        new_columns = [
            ('vibration_isolators', 'TEXT'),
            ('drive_pack_kw', 'REAL'),
            ('custom_accessories', 'TEXT'),
            ('optional_items', 'TEXT'),
            ('custom_option_items', 'TEXT'),
            ('motor_kw', 'REAL'),
            ('motor_brand', 'TEXT'),
            ('motor_pole', 'INTEGER'),
            ('motor_efficiency', 'REAL'),
            ('motor_discount_rate', 'REAL'),
            ('bearing_brand', 'TEXT')
        ]
        
        # Add each missing column
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                logger.info(f"Adding column {column_name} ({column_type}) to ProjectFans table (main DB)")
                try:
                    cursor.execute(f"ALTER TABLE ProjectFans ADD COLUMN {column_name} {column_type}")
                    logger.info(f"Successfully added column {column_name} (main DB)")
                except sqlite3.Error as e:
                    logger.error(f"Error adding column {column_name} (main DB): {str(e)}")
            else:
                logger.info(f"Column {column_name} already exists in ProjectFans table (main DB)")
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        logger.info("Successfully updated ProjectFans table with new columns in main DB")
        return True
        
    except Exception as e:
        logger.error(f"Error updating ProjectFans table in main DB: {str(e)}", exc_info=True)
        return False

# Add a function to copy data from pole/efficiency to motor_pole/motor_efficiency if needed
def sync_column_data():
    """Synchronize data between similarly named columns"""
    try:
        # Path to the main database
        db_path = 'fan_pricing.db'
        
        if not os.path.exists(db_path):
            logger.error("Main database not found")
            return False
        
        logger.info(f"Synchronizing column data in main database at: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if we have both old and new column names
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Sync pole data if needed
        if 'pole' in columns and 'motor_pole' in columns:
            logger.info("Syncing data from 'pole' to 'motor_pole'")
            try:
                # Update motor_pole from pole where motor_pole is null or 0
                cursor.execute("""
                    UPDATE ProjectFans 
                    SET motor_pole = CAST(pole AS INTEGER) 
                    WHERE (motor_pole IS NULL OR motor_pole = 0) AND pole IS NOT NULL AND pole != ''
                """)
                logger.info(f"Synced {cursor.rowcount} rows from pole to motor_pole")
            except sqlite3.Error as e:
                logger.error(f"Error syncing pole data: {str(e)}")
        
        # Sync efficiency data if needed
        if 'efficiency' in columns and 'motor_efficiency' in columns:
            logger.info("Syncing data from 'efficiency' to 'motor_efficiency'")
            try:
                # Update motor_efficiency from efficiency where motor_efficiency is null or 0
                cursor.execute("""
                    UPDATE ProjectFans 
                    SET motor_efficiency = CAST(efficiency AS REAL) 
                    WHERE (motor_efficiency IS NULL OR motor_efficiency = 0) AND efficiency IS NOT NULL AND efficiency != ''
                """)
                logger.info(f"Synced {cursor.rowcount} rows from efficiency to motor_efficiency")
            except sqlite3.Error as e:
                logger.error(f"Error syncing efficiency data: {str(e)}")
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        logger.info("Successfully synchronized column data in main database")
        return True
        
    except Exception as e:
        logger.error(f"Error synchronizing column data: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success_central = add_missing_columns()
    success_main = add_missing_columns_to_main_db()
    success_sync = sync_column_data()
    
    if success_central and success_main and success_sync:
        logger.info("Successfully updated both databases and synchronized data")
        sys.exit(0)
    else:
        logger.error("Failed to update one or both databases or synchronize data")
        sys.exit(1) 