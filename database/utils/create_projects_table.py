import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def create_projects_tables():
    """Create tables for storing projects and fans data."""
    try:
        # Use relative path that matches database/__init__.py local default
        import os
        db_path = os.path.join('data', 'fan_pricing.db')
        os.makedirs('data', exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Connected to database")
        
        # Create Projects table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enquiry_number TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            total_fans INTEGER NOT NULL,
            sales_engineer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        logger.info("Created or confirmed Projects table exists")
        
        # Create ProjectFans table to store fan data for each project
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
            fabrication_selling_price REAL,
            bought_out_selling_price REAL,
            total_selling_price REAL,
            accessories TEXT,
            bearing_brand TEXT,
            shaft_diameter REAL,
            motor_brand TEXT,
            motor_kw REAL,
            pole TEXT,
            efficiency TEXT,
            optional_items TEXT,
            total_job_margin REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES Projects(id)
        )
        ''')
        
        # Check for missing columns in both tables
        # For ProjectFans table
        columns_to_check_fans = [
            "total_job_margin",
            "fabrication_selling_price",
            "bought_out_selling_price",
            "total_selling_price"
        ]
        
        for column in columns_to_check_fans:
            try:
                cursor.execute(f"SELECT {column} FROM ProjectFans LIMIT 1")
            except sqlite3.OperationalError:
                logger.info(f"Adding {column} column to ProjectFans table")
                cursor.execute(f"ALTER TABLE ProjectFans ADD COLUMN {column} REAL DEFAULT 0")
                logger.info(f"Added {column} column successfully")
            
        # For Projects table
        columns_to_check_projects = [
            "total_job_margin",
            "total_weight",
            "total_fabrication_cost",
            "total_bought_out_cost",
            "total_cost",
            "total_selling_price"
        ]
        
        for column in columns_to_check_projects:
            try:
                cursor.execute(f"SELECT {column} FROM Projects LIMIT 1")
            except sqlite3.OperationalError:
                logger.info(f"Adding {column} column to Projects table")
                cursor.execute(f"ALTER TABLE Projects ADD COLUMN {column} REAL DEFAULT 0")
                logger.info(f"Added {column} column successfully")
        
        logger.info("Created or confirmed ProjectFans table exists with all required columns")
        
        # Commit changes
        conn.commit()
        logger.info("Successfully created projects tables")
        
        # Close the connection
        conn.close()
        logger.info("Database connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error creating projects tables: {str(e)}")
        return False

def create_users_table():
    """Create the users table and insert default users if not present."""
    try:
        # Use relative path that matches database/__init__.py local default
        import os
        db_path = os.path.join('data', 'fan_pricing.db')
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, full_name, is_admin) VALUES
                ('abdul', 'tcfsales', 'Abdul Basidh', 1),
                ('pradeep', 'tcfsales', 'Pradeep', 0),
                ('satish', 'tcfsales', 'Satish', 0),
                ('franklin', 'tcfsales', 'Franklin', 0),
                ('muthu', 'tcfsales', 'Muthu', 0),
                ('raghul', 'tcfsales', 'Raghul', 0)
        ''')
        conn.commit()
        conn.close()
        logger.info("Users table created or already exists.")
    except Exception as e:
        logger.error(f"Error creating users table: {e}")

# Ensure users table is created on import
create_users_table()

if __name__ == "__main__":
    if create_projects_tables():
        print("Projects tables created successfully.")
    else:
        print("Failed to create projects tables.") 