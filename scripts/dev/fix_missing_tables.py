import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_missing_tables():
    """Create missing Projects table."""
    try:
        # Check all database files in the project
        db_files = [f for f in os.listdir() if f.endswith('.db')]
        logger.info(f"Database files in project: {db_files}")
        
        # Check if database directory exists and contains DB files
        if os.path.exists('database'):
            db_files_in_dir = [f for f in os.listdir('database') if f.endswith('.db')]
            logger.info(f"Database files in 'database' directory: {db_files_in_dir}")
        
        # Connect to the database used in the app
        conn = sqlite3.connect('fan_pricing.db')  # This is the DB used in create_projects_table.py
        cursor = conn.cursor()
        
        logger.info("Connected to database: fan_pricing.db")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Tables before fix: {tables}")
        
        # Check if Projects table exists
        if 'Projects' not in tables:
            logger.info("Creating Projects table...")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                total_fans INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            logger.info("Projects table created")
        else:
            logger.info("Projects table already exists in fan_pricing.db")
        
        # Create ProjectFans table if it doesn't exist
        if 'ProjectFans' not in tables:
            logger.info("Creating ProjectFans table...")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ProjectFans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                fan_number INTEGER NOT NULL,
                fan_model TEXT NOT NULL,
                fan_size TEXT NOT NULL,
                class TEXT NOT NULL,
                arrangement TEXT NOT NULL,
                vendor TEXT NOT NULL,
                material TEXT NOT NULL,
                bare_fan_weight REAL,
                accessory_weights REAL,
                total_weight REAL,
                fabrication_cost REAL,
                bought_out_cost REAL,
                total_cost REAL,
                accessories TEXT,
                bearing_brand TEXT,
                shaft_diameter REAL,
                motor_brand TEXT,
                motor_kw REAL,
                pole TEXT,
                efficiency TEXT,
                optional_items TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES Projects(id)
            )
            ''')
            logger.info("ProjectFans table created")
        else:
            logger.info("ProjectFans table already exists in fan_pricing.db")
            
        # Get all tables after fix
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Tables after fix: {tables}")
        
        # Commit changes
        conn.commit()
        conn.close()
        logger.info("Database connection closed")
        
        # Now also check database/fan_weights.db, as that may be the one used by load_dropdown_options()
        if os.path.exists('database/fan_weights.db'):
            conn_other = sqlite3.connect('database/fan_weights.db')
            cursor_other = conn_other.cursor()
            logger.info("Connected to database: database/fan_weights.db")
            
            # Get all tables
            cursor_other.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables_other = [row[0] for row in cursor_other.fetchall()]
            logger.info(f"Tables in database/fan_weights.db: {tables_other}")
            
            # Check BearingLookup table
            if 'BearingLookup' in tables_other:
                logger.info("BearingLookup exists in database/fan_weights.db")
            
            conn_other.close()
            logger.info("Closed database/fan_weights.db")
        
        return True
    except Exception as e:
        logger.error(f"Error fixing missing tables: {str(e)}")
        return False

if __name__ == "__main__":
    if fix_missing_tables():
        print("Missing tables fixed successfully")
    else:
        print("Failed to fix missing tables") 