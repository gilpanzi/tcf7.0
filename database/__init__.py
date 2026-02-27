import sqlite3
import logging
import os
import json
import datetime
import re

logger = logging.getLogger(__name__)

def _table_has_column(cursor, table: str, column: str) -> bool:
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())
    except Exception:
        return False

def get_render_db_path():
    """Get the appropriate database path for Render environment."""
    # Check if we're on Render (Render sets this environment variable)
    if os.environ.get('RENDER'):
        # Use the mounted disk path on Render
        base_path = '/opt/render/project/src/data'
    else:
        # Local development path - standardize to data/ directory
        base_path = os.environ.get('DB_PATH', 'data')
    
    # Ensure the data directory exists
    os.makedirs(base_path, exist_ok=True)
    
    return os.path.join(base_path, 'fan_pricing.db')

def get_db_connection():
    """Connect to the SQLite database with row factory."""
    try:
        db_path = get_render_db_path()
        
        # If database doesn't exist in the new location but exists in the old location
        if not os.path.exists(db_path) and os.path.exists('fan_pricing.db'):
            # Copy existing database to new location
            import shutil
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            shutil.copy('fan_pricing.db', db_path)
            logger.info(f"Copied database to {db_path}")
        
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        logger.info(f"Connected to database at: {db_path}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def _safe_json_load(json_string):
    """Safely load JSON string, returning empty dict if parsing fails."""
    if not json_string:
        return {}
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {json_string}, error: {str(e)}")
        return {}

def get_unique_values(cursor, table, column):
    """Get unique values from a specific column in a table."""
    try:
        cursor.execute(f'SELECT DISTINCT "{column}" FROM {table} ORDER BY "{column}"')
        return [str(row[0]) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting unique values from {table}.{column}: {str(e)}")
        raise

def load_dropdown_options():
    """Load all dropdown options from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        options = {
            'fan_models': get_unique_values(cursor, 'FanWeights', 'Fan Model'),
            'fan_sizes': get_unique_values(cursor, 'FanWeights', 'Fan Size'),
            'classes': get_unique_values(cursor, 'FanWeights', 'Class'),
            'arrangements': get_unique_values(cursor, 'FanWeights', 'Arrangement'),
            'vendors': get_unique_values(cursor, 'VendorWeightDetails', 'Vendor'),
            'bearing_brands': get_unique_values(cursor, 'BearingLookup', 'Brand'),
            'motor_brands': get_unique_values(cursor, 'MotorPrices', 'Brand'),
            'drive_pack_options': get_unique_values(cursor, 'DrivePackLookup', 'Motor kW'),
            'motor_kw_options': get_unique_values(cursor, 'MotorPrices', 'Motor kW'),
            'poles': get_unique_values(cursor, 'MotorPrices', 'Pole'),
            'efficiencies': get_unique_values(cursor, 'MotorPrices', 'Efficiency')
        }
        
        conn.close()
        return options
    except Exception as e:
        logger.error(f"Error loading dropdown options: {str(e)}")
        raise

def get_all_vendor_rates():
    """Get all vendor rates from the database structured for frontend use."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT Vendor, "Material Type", WeightStart, WeightEnd, MSPrice, SS304Price, SS316Price, AluminiumPrice FROM VendorWeightDetails')
        rows = cursor.fetchall()
        conn.close()
        
        # Structure: rates[vendor][material] = [{min, max, rate}, ...]
        rates = {}
        
        for row in rows:
            vendor = row['Vendor']
            weight_start = float(row['WeightStart'])
            weight_end = float(row['WeightEnd'])
            ms_price = float(row['MSPrice']) if row['MSPrice'] is not None else 0
            ss304_price = float(row['SS304Price']) if row['SS304Price'] is not None else 0
            ss316_price = float(row['SS316Price']) if row['SS316Price'] is not None else 800.0
            aluminium_price = float(row['AluminiumPrice']) if row['AluminiumPrice'] is not None else 1000.0
            
            if vendor not in rates:
                rates[vendor] = {
                    'ms': [],
                    'ss304': [],
                    'ss316': [],
                    'aluminium': []
                }
            
            # MS Entry
            rates[vendor]['ms'].append({
                'min': weight_start,
                'max': weight_end,
                'rate': ms_price
            })
            
            # SS304 Entry
            rates[vendor]['ss304'].append({
                'min': weight_start,
                'max': weight_end,
                'rate': ss304_price
            })
            
            # SS316 Entry
            rates[vendor]['ss316'].append({
                'min': weight_start,
                'max': weight_end,
                'rate': ss316_price
            })
            
            # Aluminium Entry
            rates[vendor]['aluminium'].append({
                'min': weight_start,
                'max': weight_end,
                'rate': aluminium_price
            })
            
        # Sort ranges by min weight
        for vendor in rates:
            for mat in rates[vendor]:
                rates[vendor][mat].sort(key=lambda x: x['min'])
                
        return rates
    except Exception as e:
        logger.error(f"Error loading vendor rates: {str(e)}")
        return {}

def get_sales_engineers(limit: int = 100):
    """Return a list of sales engineer names. Prefer Users table; fallback to distinct from Projects."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sales_engineers = []
        # Try Users table (if it exists)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            try:
                cursor.execute("SELECT DISTINCT full_name FROM users WHERE TRIM(IFNULL(full_name,'')) != '' ORDER BY full_name LIMIT ?", (limit,))
                rows = cursor.fetchall()
                sales_engineers = [row[0] for row in rows if row and row[0]]
            except Exception:
                pass

        # Fallback to Projects table distinct values
        if not sales_engineers:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Projects'")
            if cursor.fetchone():
                cursor.execute("SELECT DISTINCT sales_engineer FROM Projects WHERE TRIM(IFNULL(sales_engineer,'')) != '' ORDER BY sales_engineer LIMIT ?", (limit,))
                rows = cursor.fetchall()
                sales_engineers = [row[0] for row in rows if row and row[0]]

        conn.close()
        return sales_engineers
    except Exception as e:
        logger.error(f"Error getting sales engineers: {str(e)}")
        raise

def fix_database_schema():
    """Fix database schema issues - add missing columns."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if Projects table exists and has required columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Projects'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(Projects)")
            project_columns = {row[1] for row in cursor.fetchall()}

            if 'status' not in project_columns:
                cursor.execute("ALTER TABLE Projects ADD COLUMN status TEXT DEFAULT 'Live'")
                logger.info("Added status column to Projects table")
                
            if 'probability' not in project_columns:
                cursor.execute("ALTER TABLE Projects ADD COLUMN probability INTEGER DEFAULT 50")
                logger.info("Added probability column to Projects table")

            if 'remarks' not in project_columns:
                cursor.execute("ALTER TABLE Projects ADD COLUMN remarks TEXT DEFAULT ''")
                logger.info("Added remarks column to Projects table")
                
            if 'month' not in project_columns:
                cursor.execute("ALTER TABLE Projects ADD COLUMN month TEXT")
                logger.info("Added month column to Projects table")

        # Check if Fans table exists and has required columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Fans'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(Fans)")
            fan_columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns one by one
            if 'status' not in fan_columns:
                cursor.execute("ALTER TABLE Fans ADD COLUMN status TEXT DEFAULT 'draft'")
                logger.info("Added status column to Fans table")
            
            if 'specifications' not in fan_columns:
                cursor.execute("ALTER TABLE Fans ADD COLUMN specifications TEXT")
                logger.info("Added specifications column to Fans table")
                
            if 'weights' not in fan_columns:
                cursor.execute("ALTER TABLE Fans ADD COLUMN weights TEXT")
                logger.info("Added weights column to Fans table")
                
            if 'costs' not in fan_columns:
                cursor.execute("ALTER TABLE Fans ADD COLUMN costs TEXT")
                logger.info("Added costs column to Fans table")
                
            if 'motor' not in fan_columns:
                cursor.execute("ALTER TABLE Fans ADD COLUMN motor TEXT")
                logger.info("Added motor column to Fans table")
        
        conn.commit()
        logger.info("Database schema fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def migrate_to_unified_schema():
    """Migrate to unified Projects/Fans schema and deprecate ProjectFans."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_name TEXT NOT NULL UNIQUE,
                last_visit_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create CustomerYearBindings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CustomerYearBindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                year TEXT NOT NULL,
                region TEXT,
                sales_engineer TEXT,
                UNIQUE(customer_id, year),
                FOREIGN KEY (customer_id) REFERENCES Customers(id)
            )
        ''')
        
        # Create CustomerAliases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CustomerAliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                alias_name TEXT NOT NULL UNIQUE,
                FOREIGN KEY (customer_id) REFERENCES Customers(id)
            )
        ''')

        # Create Projects table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT NOT NULL UNIQUE,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                total_fans INTEGER NOT NULL,
                sales_engineer TEXT NOT NULL,
                status TEXT DEFAULT 'Live',
                probability INTEGER DEFAULT 50,
                remarks TEXT DEFAULT '',
                month TEXT,
                source TEXT DEFAULT 'manual',
                lost_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES Customers(id)
            )
        ''')

        # Ensure required columns exist on Projects (for older databases)
        cursor.execute("PRAGMA table_info(Projects)")
        project_columns = {row[1] for row in cursor.fetchall()}
        if 'status' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN status TEXT DEFAULT 'Live'")
        if 'probability' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN probability INTEGER DEFAULT 50")
        if 'remarks' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN remarks TEXT DEFAULT ''")
        if 'month' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN month TEXT")
        if 'created_at' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN created_at TIMESTAMP")
        if 'updated_at' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN updated_at TIMESTAMP")
        if 'source' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN source TEXT DEFAULT 'manual'")
        if 'lost_reason' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN lost_reason TEXT")
        if 'customer_id' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN customer_id INTEGER")
        
        # Create Fans table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Fans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                fan_number INTEGER NOT NULL,
                status TEXT DEFAULT 'draft',
                specifications TEXT,
                weights TEXT,
                costs TEXT,
                motor TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES Projects(id),
                UNIQUE(project_id, fan_number)
            )
        ''')

        # Ensure required columns exist on Fans (for older databases)
        cursor.execute("PRAGMA table_info(Fans)")
        fan_columns = {row[1] for row in cursor.fetchall()}
        if 'status' not in fan_columns:
            cursor.execute("ALTER TABLE Fans ADD COLUMN status TEXT DEFAULT 'draft'")
        if 'specifications' not in fan_columns:
            cursor.execute("ALTER TABLE Fans ADD COLUMN specifications TEXT")
        if 'weights' not in fan_columns:
            cursor.execute("ALTER TABLE Fans ADD COLUMN weights TEXT")
        if 'costs' not in fan_columns:
            cursor.execute("ALTER TABLE Fans ADD COLUMN costs TEXT")
        if 'motor' not in fan_columns:
            cursor.execute("ALTER TABLE Fans ADD COLUMN motor TEXT")
        if 'created_at' not in fan_columns:
            cursor.execute("ALTER TABLE Fans ADD COLUMN created_at TIMESTAMP")
        if 'updated_at' not in fan_columns:
            cursor.execute("ALTER TABLE Fans ADD COLUMN updated_at TIMESTAMP")
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_enquiry ON Projects(enquiry_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fans_project_id ON Fans(project_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fans_status ON Fans(status)')
        
        # Create Orders table for the Order Details Dashboard
        # Only create if it doesn't exist to preserve data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_ref TEXT,
                year TEXT,
                customer_id INTEGER,
                customer_name TEXT,
                sales_engineer TEXT,
                region TEXT,
                order_value REAL,
                our_cost REAL,
                warranty TEXT,
                contribution_value REAL,
                contribution_percentage REAL,
                qty INTEGER,
                month TEXT,
                rep TEXT,
                type_of_customer TEXT,
                sector TEXT,
                po_number TEXT,
                end_user TEXT,
                remarks TEXT,
                source TEXT DEFAULT 'excel',
                FOREIGN KEY (customer_id) REFERENCES Customers(id)
            )
        ''')
        
        cursor.execute("PRAGMA table_info(Orders)")
        order_columns = {row[1] for row in cursor.fetchall()}
        if 'customer_id' not in order_columns:
            cursor.execute("ALTER TABLE Orders ADD COLUMN customer_id INTEGER")
        if 'source' not in order_columns:
            cursor.execute("ALTER TABLE Orders ADD COLUMN source TEXT DEFAULT 'excel'")
            
        # Deduplicate Orders table just to be safe before creating unique index
        cursor.execute('''
            DELETE FROM Orders
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM Orders
                GROUP BY job_ref
            )
        ''')
            
        # Ensure job_ref is UNIQUE to allow UPSERT operations
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_job_ref ON Orders(job_ref)')
        
        # Create EnquiryRegister table for the Enquiry Tracking Dashboard
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EnquiryRegister (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT UNIQUE,
                year TEXT,
                month TEXT,
                sales_engineer TEXT,
                customer_id INTEGER,
                customer_name TEXT,
                region TEXT,
                source TEXT DEFAULT 'excel',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES Customers(id)
            )
        ''')
        
        cursor.execute("PRAGMA table_info(EnquiryRegister)")
        enquiry_reg_columns = {row[1] for row in cursor.fetchall()}
        if 'customer_id' not in enquiry_reg_columns:
            cursor.execute("ALTER TABLE EnquiryRegister ADD COLUMN customer_id INTEGER")
        if 'source' not in enquiry_reg_columns:
            cursor.execute("ALTER TABLE EnquiryRegister ADD COLUMN source TEXT DEFAULT 'excel'")
        
        # Skip ProjectFans migration for now to avoid errors
        # TODO: Fix ProjectFans migration later
        logger.info("Skipping ProjectFans migration to avoid errors")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error migrating to unified schema: {str(e)}")
        return False

def create_or_update_project(enquiry_number, customer_name, total_fans, sales_engineer, month=None):
    """Create or update a project and ensure fan placeholders exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if project exists by enquiry_number
        cursor.execute("SELECT id FROM Projects WHERE enquiry_number = ?", (enquiry_number,))
        existing_row = cursor.fetchone()
        
        # Determine schema capabilities
        has_updated_at = _table_has_column(cursor, 'Projects', 'updated_at')
        has_month = _table_has_column(cursor, 'Projects', 'month')
        
        if existing_row:
            update_clause = "customer_name = ?, total_fans = ?, sales_engineer = ?"
            params = [customer_name, total_fans, sales_engineer]
            
            if has_month and month:
                update_clause += ", month = ?"
                params.append(month)
                
            if has_updated_at:
                update_clause += ", updated_at = CURRENT_TIMESTAMP"
                
            params.append(enquiry_number)
            
            cursor.execute(f'''
                UPDATE Projects SET {update_clause} WHERE enquiry_number = ?
            ''', params)
        else:
            cols = "enquiry_number, customer_name, total_fans, sales_engineer, status, probability"
            vals = "?, ?, ?, ?, 'Live', 50"
            params = [enquiry_number, customer_name, total_fans, sales_engineer]
            
            if has_month and month:
                cols += ", month"
                vals += ", ?"
                params.append(month)
                
            if has_updated_at:
                cols += ", updated_at"
                vals += ", CURRENT_TIMESTAMP"
                
            cursor.execute(f"INSERT INTO Projects ({cols}) VALUES ({vals})", params)
        
        # Get reliable project_id regardless of INSERT OR REPLACE semantics
        cursor.execute('SELECT id FROM Projects WHERE enquiry_number = ?', (enquiry_number,))
        row = cursor.fetchone()
        project_id = row['id'] if row else None
        
        # Ensure fan placeholders exist for 1..total_fans
        for fan_number in range(1, total_fans + 1):
            cursor.execute('''
                INSERT OR IGNORE INTO Fans (project_id, fan_number, status)
                VALUES (?, ?, 'draft')
            ''', (project_id, fan_number))
        
        # Mark extra fans as removed if total_fans decreased
        cursor.execute('''
            UPDATE Fans SET status = 'removed' 
            WHERE project_id = ? AND fan_number > ?
        ''', (project_id, total_fans))
        
        conn.commit()
        conn.close()
        return project_id
        
    except Exception as e:
        logger.error(f"Error creating/updating project: {str(e)}")
        raise

def get_project(enquiry_number):
    """Get project by enquiry number."""
    try:
        logger.info(f"Getting project for enquiry: {enquiry_number}")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM Projects WHERE enquiry_number = ?', (enquiry_number,))
        project = cursor.fetchone()
        
        if project:
            logger.info(f"Found project: {project['enquiry_number']}, ID: {project['id']}")
            # Get fans for this project
            cursor.execute('''
                SELECT fan_number, status, specifications, weights, costs, motor, updated_at
                FROM Fans 
                WHERE project_id = ? AND status != 'removed'
                ORDER BY fan_number
            ''', (project['id'],))
            
            fans = cursor.fetchall()
            logger.info(f"Found {len(fans)} fans for project {enquiry_number}")
            
            conn.close()
            return {
                'id': project['id'],
                'enquiry_number': project['enquiry_number'],
                'customer_name': project['customer_name'],
                'total_fans': project['total_fans'],
                'sales_engineer': project['sales_engineer'],
                'status': project['status'] if 'status' in project.keys() else 'Live',
                'probability': project['probability'] if 'probability' in project.keys() else 50,
                'remarks': project['remarks'] if 'remarks' in project.keys() else '',
                'month': project['month'] if 'month' in project.keys() else None,
                'created_at': project['created_at'] if 'created_at' in project.keys() else None,
                'updated_at': project['updated_at'] if 'updated_at' in project.keys() else None,
                'fans': [
                    {
                        'fan_number': fan['fan_number'],
                        'status': fan['status'],
                        'specifications': _safe_json_load(fan['specifications']),
                        'weights': _safe_json_load(fan['weights']),
                        'costs': _safe_json_load(fan['costs']),
                        'motor': _safe_json_load(fan['motor']),
                        'updated_at': fan['updated_at']
                    }
                    for fan in fans
                ]
            }
        
        conn.close()
        return None
        
    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        raise

def search_projects(query=None, limit=50):
    """Search projects by enquiry number or customer name."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine available ordering column
        order_col = 'updated_at'
        if not _table_has_column(cursor, 'Projects', 'updated_at'):
            order_col = 'created_at' if _table_has_column(cursor, 'Projects', 'created_at') else 'enquiry_number'

        select_updated = _table_has_column(cursor, 'Projects', 'updated_at')
        has_status = _table_has_column(cursor, 'Projects', 'status')
        has_probability = _table_has_column(cursor, 'Projects', 'probability')
        has_remarks = _table_has_column(cursor, 'Projects', 'remarks')
        has_month = _table_has_column(cursor, 'Projects', 'month')
        
        select_cols = 'enquiry_number, customer_name, total_fans, sales_engineer' 
        select_cols += (', updated_at' if select_updated else '')
        select_cols += (', status' if has_status else '')
        select_cols += (', probability' if has_probability else '')
        select_cols += (', remarks' if has_remarks else '')
        select_cols += (', month' if has_month else '')

        if query:
            cursor.execute(f'''
                SELECT {select_cols}
                FROM Projects 
                WHERE enquiry_number LIKE ? OR customer_name LIKE ?
                ORDER BY {order_col} DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
        else:
            cursor.execute(f'''
                SELECT {select_cols}
                FROM Projects 
                ORDER BY {order_col} DESC
                LIMIT ?
            ''', (limit,))
        
        projects = cursor.fetchall()
        conn.close()
        
        result = []
        for p in projects:
            item = {
                'enquiry_number': p['enquiry_number'],
                'customer_name': p['customer_name'],
                'total_fans': p['total_fans'],
                'sales_engineer': p['sales_engineer'],
                'status': p['status'] if 'status' in p.keys() else 'Live',
                'probability': p['probability'] if 'probability' in p.keys() else 50,
                'remarks': p['remarks'] if 'remarks' in p.keys() else '',
                'month': p['month'] if 'month' in p.keys() else None
            }
            if 'updated_at' in p.keys():
                item['updated_at'] = p['updated_at']
            result.append(item)
        return result
        
    except Exception as e:
        logger.error(f"Error searching projects: {str(e)}")
        raise

def get_fan(enquiry_number, fan_number):
    """Get a specific fan by enquiry number and fan number."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT f.*, p.enquiry_number, p.customer_name, p.total_fans, p.sales_engineer
            FROM Fans f
            JOIN Projects p ON f.project_id = p.id
            WHERE p.enquiry_number = ? AND f.fan_number = ? AND f.status != 'removed'
        ''', (enquiry_number, fan_number))
        
        fan = cursor.fetchone()
        
        if fan:
            conn.close()
            return {
                'id': fan['id'],
                'project_id': fan['project_id'],
                'fan_number': fan['fan_number'],
                'status': fan['status'],
                'specifications': _safe_json_load(fan['specifications']),
                'weights': _safe_json_load(fan['weights']),
                'costs': _safe_json_load(fan['costs']),
                'motor': _safe_json_load(fan['motor']),
                'created_at': fan['created_at'],
                'updated_at': fan['updated_at'],
                'project': {
                    'enquiry_number': fan['enquiry_number'],
                    'customer_name': fan['customer_name'],
                    'total_fans': fan['total_fans'],
                    'sales_engineer': fan['sales_engineer']
                }
            }
        
        conn.close()
        return None
        
    except Exception as e:
        logger.error(f"Error getting fan: {str(e)}")
        raise

def save_fan(enquiry_number, fan_number, specifications, weights=None, costs=None, motor=None, status='draft'):
    """Save fan data."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get project_id
            cursor.execute('SELECT id FROM Projects WHERE enquiry_number = ?', (enquiry_number,))
            project = cursor.fetchone()
            
            if not project:
                raise ValueError(f"Project not found: {enquiry_number}")
            
            project_id = project['id']
            
            # Check if fan already exists
            cursor.execute('''
                SELECT id FROM Fans WHERE project_id = ? AND fan_number = ?
            ''', (project_id, fan_number))
            existing_fan = cursor.fetchone()
            
            if existing_fan:
                # Update existing fan
                cursor.execute('''
                    UPDATE Fans 
                    SET specifications = ?, weights = ?, costs = ?, motor = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = ? AND fan_number = ?
                ''', (
                    json.dumps(specifications),
                    json.dumps(weights) if weights else None,
                    json.dumps(costs) if costs else None,
                    json.dumps(motor) if motor else None,
                    status,
                    project_id,
                    fan_number
                ))
                logger.info(f"Updated existing fan {fan_number} for project {enquiry_number}")
            else:
                # Create new fan
                cursor.execute('''
                    INSERT INTO Fans (project_id, fan_number, status, specifications, weights, costs, motor)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    fan_number,
                    status,
                    json.dumps(specifications),
                    json.dumps(weights) if weights else None,
                    json.dumps(costs) if costs else None,
                    json.dumps(motor) if motor else None
                ))
                logger.info(f"Created new fan {fan_number} for project {enquiry_number}")
            
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error saving fan: {str(e)}")
        raise

def init_db():
    """Initialize the database with schema.sql."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if schema.sql exists
        if os.path.exists('schema.sql'):
            logger.info("Initializing database with schema.sql")
            with open('schema.sql', 'r') as f:
                schema_sql = f.read()
                cursor.executescript(schema_sql)
            logger.info("Database initialized successfully")
        else:
            logger.warning("schema.sql not found - database not initialized")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def get_dashboard_stats(sales_engineer=None, status=None, month=None, search=None):
    """Calculate and return dashboard statistics, with optional filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for new columns
        has_remarks = _table_has_column(cursor, 'Projects', 'remarks')
        has_month = _table_has_column(cursor, 'Projects', 'month')
        
        cols = "p.id, p.enquiry_number, p.customer_name, p.sales_engineer, p.status, p.probability, p.updated_at, p.created_at, f.costs"
        if has_remarks:
            cols += ", p.remarks"
        if has_month:
            cols += ", p.month"
            
        # Build query dynamically based on filters
        query = f'''
        SELECT {cols}
        FROM Projects p
        LEFT JOIN Fans f ON p.id = f.project_id
        WHERE p.status != 'removed'
        '''
        
        params = []
        if sales_engineer:
            query += " AND p.sales_engineer = ?"
            params.append(sales_engineer)
        if status:
            query += " AND p.status = ?"
            params.append(status)
        if month:
            query += " AND p.month = ?"
            params.append(month)
        if search:
            query += " AND (p.enquiry_number LIKE ? OR p.customer_name LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
            
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        
        # Process rows into project summaries
        projects_dict = {}
        for row in rows:
            p_id = int(row['id'])
            if p_id not in projects_dict:
                projects_dict[p_id] = {
                    'enquiry_number': str(row['enquiry_number']),
                    'customer_name': str(row['customer_name']),
                    'sales_engineer': str(row['sales_engineer']),
                    'status': str(row['status']) if row['status'] else 'Live',
                    'probability': int(row['probability']) if row['probability'] is not None else 50,
                    'remarks': str(row['remarks']) if 'remarks' in row.keys() and row['remarks'] is not None else '',
                    'month': str(row['month']) if 'month' in row.keys() and row['month'] is not None else '',
                    'updated_at': str(row['updated_at']) if 'updated_at' in row.keys() else str(row['created_at']),
                    'total_value': 0.0,
                    'fan_count': 0
                }
            
            # extract cost
            costs_json = _safe_json_load(row['costs'])
            if costs_json and 'total_selling_price' in costs_json:
                projects_dict[p_id]['total_value'] += float(costs_json['total_selling_price'])
                projects_dict[p_id]['fan_count'] += 1
                
        # Now aggregate stats
        all_projects = list(projects_dict.values())
        all_projects.sort(key=lambda x: str(x['updated_at']), reverse=True)
        
        stats = {
            'total_live_value': sum(float(p['total_value']) for p in all_projects if p['status'] == 'Live'),
            'total_ordered_value': sum(float(p['total_value']) for p in all_projects if p['status'] == 'Ordered'),
            'active_enquiries': sum(1 for p in all_projects if p['status'] == 'Live'),
            'avg_conversion': 0.0,
            
            # Sales Engineer breakdown
            'engineers': {},
            
            # List of all recent projects
            'recent_projects': all_projects[:100] # Cap for UI performance
        }
        
        # Calculate Average Conversion across active
        live_projects = [p for p in all_projects if p['status'] == 'Live']
        if live_projects:
            stats['avg_conversion'] = float(sum(int(p['probability']) for p in live_projects)) / len(live_projects)
            
        # Group by Sales Engineer
        for p in all_projects:
            se = str(p['sales_engineer'])
            if not se: continue
            
            if se not in stats['engineers']:
                stats['engineers'][se] = {'live_enquiries': 0, 'live_value': 0.0, 'ordered_value': 0.0}
            
            if p['status'] == 'Live':
                stats['engineers'][se]['live_enquiries'] += 1
                stats['engineers'][se]['live_value'] += float(p['total_value'])
            elif p['status'] == 'Ordered':
                stats['engineers'][se]['ordered_value'] += float(p['total_value'])
                
        conn.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise

def update_project_status(enquiry_number, status, probability, remarks=None, lost_reason=None):
    """Update just the status, probability, optionally remarks, and lost_reason of a project."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Safely determine updated_at, remarks and lost_reason columns
        update_clause = "status = ?, probability = ?"
        params = [status, probability]
        
        if remarks is not None and _table_has_column(cursor, 'Projects', 'remarks'):
            update_clause += ", remarks = ?"
            params.append(remarks)
            
        if status == 'Lost' and lost_reason is not None and _table_has_column(cursor, 'Projects', 'lost_reason'):
            update_clause += ", lost_reason = ?"
            params.append(lost_reason)
            
        if _table_has_column(cursor, 'Projects', 'updated_at'):
            update_clause += ", updated_at = CURRENT_TIMESTAMP"
            
        params.append(enquiry_number)
            
        cursor.execute(f'''
            UPDATE Projects 
            SET {update_clause}
            WHERE enquiry_number = ?
        ''', params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    except Exception as e:
        logger.error(f"Error updating project status: {str(e)}")
        raise 

def import_orders_from_excel(file) -> bool:
    """Import orders from the uploaded Excel file using pandas."""
    try:
        import pandas as pd
        import numpy as np
        
        logger.info("Starting order import from Excel")
        # Read the "Order Register - From 2019" sheet
        df = pd.read_excel(file, sheet_name="Order Register - From 2019")
        
        # Clean column names first
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping Excel columns to DB columns
        col_map = {
            'JOB REF': 'job_ref',
            'YEAR': 'year',
            'Customer Name': 'customer_name',
            'Sales Engineer': 'sales_engineer',
            'Region': 'region',
            'Order Value, INR': 'order_value',
            'Our Cost, INR': 'our_cost',
            'Warranty': 'warranty',
            'Contribution Value, INR': 'contribution_value',
            'Contribution Value, %': 'contribution_percentage',
            'QTY': 'qty',
            'Month': 'month',
            'REP': 'rep',
            'TYPE OF CUSTOMER': 'type_of_customer',
            'SECTOR': 'sector',
            'CUSTOMER PO NUMBER': 'po_number',
            'END USER': 'end_user',
            'REMARKS': 'remarks'
        }
        
        # Case insensitive mapping fallback
        actual_cols = df.columns.tolist()
        final_map = {}
        for expected_col, db_col in col_map.items():
            # Find the closest match (ignoring case and extra spaces)
            match = next((c for c in actual_cols if str(c).lower().strip() == expected_col.lower().strip()), None)
            if match:
                final_map[match] = db_col
        
        # Select and rename columns
        df = df[list(final_map.keys())].rename(columns=final_map)
        
        # Clean data: drop rows without JOB REF
        if 'job_ref' not in df.columns: return False
        df = df.dropna(subset=['job_ref'])
        df['job_ref'] = df['job_ref'].astype(str).str.strip()
        df = df[df['job_ref'] != '']
        df = df[df['job_ref'] != 'nan']
        
        # Drop duplicates, keeping the LAST occurrence (which usually represents the most recent update)
        df = df.drop_duplicates(subset=['job_ref'], keep='last')
        
        # Convert numerical columns
        num_cols = ['order_value', 'our_cost', 'contribution_value', 'contribution_percentage', 'qty']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Replace NaN with None for SQLite
        df = df.replace({np.nan: None})
        
        records = df.to_dict('records')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Keep track of job refs in Excel
        excel_job_refs = df['job_ref'].tolist()
        
        # Delete orders that are no longer in the Excel file
        if excel_job_refs:
            # We delete any order originating from excel that is not in the current excel file
            # SQLite IN clause limits at 999 parameters typically, so we delete in batches
            batch_size = 900
            
            # First get all excel source orders
            cursor.execute("SELECT job_ref FROM Orders WHERE source = 'excel'")
            existing_excel_orders = {row[0] for row in cursor.fetchall()}
            
            # Find which ones to delete
            excel_job_refs_set = set(excel_job_refs)
            refs_to_delete = list(existing_excel_orders - excel_job_refs_set)
            
            for i in range(0, len(refs_to_delete), batch_size):
                batch = refs_to_delete[i:i + batch_size]
                placeholders = ','.join(['?'] * len(batch))
                cursor.execute(f"DELETE FROM Orders WHERE job_ref IN ({placeholders}) AND source = 'excel'", batch)
                logger.info(f"Deleted {len(batch)} old orders not in current Excel.")
        
        # Use UPSERT (INSERT ON CONFLICT DO UPDATE)
        # This preserves manual entries/edits (since the primary unique key is job_ref)
        cursor.executemany('''
            INSERT INTO Orders (
                job_ref, year, customer_name, sales_engineer, region, 
                order_value, our_cost, warranty, contribution_value, 
                contribution_percentage, qty, month, rep, type_of_customer, 
                sector, po_number, end_user, remarks, source
            ) VALUES (
                :job_ref, :year, :customer_name, :sales_engineer, :region,
                :order_value, :our_cost, :warranty, :contribution_value,
                :contribution_percentage, :qty, :month, :rep, :type_of_customer,
                :sector, :po_number, :end_user, :remarks, 'excel'
            ) ON CONFLICT(job_ref) DO UPDATE SET
                year=excluded.year,
                customer_name=excluded.customer_name,
                sales_engineer=excluded.sales_engineer,
                region=excluded.region,
                order_value=excluded.order_value,
                our_cost=excluded.our_cost,
                warranty=excluded.warranty,
                contribution_value=excluded.contribution_value,
                contribution_percentage=excluded.contribution_percentage,
                qty=excluded.qty,
                month=excluded.month,
                rep=excluded.rep,
                type_of_customer=excluded.type_of_customer,
                sector=excluded.sector,
                po_number=excluded.po_number,
                end_user=excluded.end_user,
                remarks=excluded.remarks
        ''', records)
        
        conn.commit()
        conn.close()
        logger.info(f"Successfully imported {len(records)} orders")
        return True
        
    except Exception as e:
        logger.error(f"Error importing sequences from Excel: {str(e)}")
        return False

def get_orders():
    """Retrieve all order data for the dashboard."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Orders ORDER BY year DESC, month DESC, job_ref DESC")
        rows = cursor.fetchall()
        
        orders = []
        for row in rows:
            orders.append(dict(row))
            
        conn.close()
        return orders
    except Exception as e:
        logger.error(f"Error retrieving orders: {str(e)}")
        return []

def import_enquiries_from_excel(file) -> bool:
    """Import enquiry register from Excel."""
    try:
        import pandas as pd
        import numpy as np
        df = pd.read_excel(file, sheet_name='Enquiry Register - From 2019')
        df.columns = [str(c).strip() for c in df.columns]
        mapping = {'ENQ NO': 'enquiry_number', 'YEAR': 'year', 'SALES ENGINEER': 'sales_engineer', 'CUSTOMER NAME': 'customer_name', 'Region': 'region'}
        
        # Case insensitive mapping fallback
        actual_cols = df.columns.tolist()
        final_map = {}
        for expected_col, db_col in mapping.items():
            match = next((c for c in actual_cols if str(c).lower().strip() == expected_col.lower().strip()), None)
            if match:
                final_map[match] = db_col
                
        df = df[list(final_map.keys())].rename(columns=final_map)
        if 'enquiry_number' not in df.columns: return False
        df = df.dropna(subset=['enquiry_number'])
        df['enquiry_number'] = df['enquiry_number'].astype(str).str.strip()
        df = df.drop_duplicates(subset=['enquiry_number'], keep='last')
        def get_m(enq):
            if len(enq) >= 6 and enq.startswith('EQ'):
                m = {'01':'January','02':'February','03':'March','04':'April','05':'May','06':'June','07':'July','08':'August','09':'September','10':'October','11':'November','12':'December'}
                return m.get(enq[4:6], 'Unknown')
            return 'Unknown'
        df['month'] = df['enquiry_number'].apply(get_m)
        df = df.replace({np.nan: None})
        recs = df.to_dict('records')
        conn = get_db_connection(); cursor = conn.cursor()
        
        # Clear out enquiries that are no longer in Excel
        excel_enq_numbers = df['enquiry_number'].tolist()
        if excel_enq_numbers:
            batch_size = 900
            cursor.execute("SELECT enquiry_number FROM EnquiryRegister WHERE source = 'excel'")
            existing_excel_enqs = {row[0] for row in cursor.fetchall()}
            
            excel_enq_set = set(excel_enq_numbers)
            enqs_to_delete = list(existing_excel_enqs - excel_enq_set)
            
            for i in range(0, len(enqs_to_delete), batch_size):
                batch = enqs_to_delete[i:i + batch_size]
                placeholders = ','.join(['?'] * len(batch))
                cursor.execute(f"DELETE FROM EnquiryRegister WHERE enquiry_number IN ({placeholders}) AND source = 'excel'", batch)
                logger.info(f"Deleted {len(batch)} old enquiries not in current Excel.")
        
        cursor.executemany('''
            INSERT INTO EnquiryRegister (
                enquiry_number, year, month, sales_engineer, customer_name, region, source
            ) VALUES (
                :enquiry_number, :year, :month, :sales_engineer, :customer_name, :region, "excel"
            ) ON CONFLICT(enquiry_number) DO UPDATE SET
                year=excluded.year,
                month=excluded.month,
                sales_engineer=excluded.sales_engineer,
                customer_name=excluded.customer_name,
                region=excluded.region
        ''', recs)
        conn.commit(); conn.close()
        return True
    except Exception as e:
        logger.error(f"Error importing enquiries: {e}")
        return False

def bulk_import_from_excel(file) -> dict:
    """Import both Orders and Enquiries from a single Excel file."""
    results: dict = {"orders": False, "enquiries": False, "messages": []}
    try:
        import pandas as pd
        # Load the Excel file once
        xlsx = pd.ExcelFile(file)
        sheet_names = xlsx.sheet_names
        
        # Import Orders if sheet exists
        if "Order Register - From 2019" in sheet_names:
            try:
                if hasattr(file, 'seek'): file.seek(0)
                success = import_orders_from_excel(file)
                results["orders"] = success
                if success: results["messages"].append("Successfully imported Orders.")
                else: results["messages"].append("Failed to import Orders.")
            except Exception as e:
                results["messages"].append(f"Order import error: {str(e)}")
        else:
            results["messages"].append("'Order Register - From 2019' sheet not found.")

        # Import Enquiries if sheet exists
        if "Enquiry Register - From 2019" in sheet_names:
            try:
                if hasattr(file, 'seek'): file.seek(0)
                success = import_enquiries_from_excel(file)
                results["enquiries"] = success
                if success: results["messages"].append("Successfully imported Enquiry Register.")
                else: results["messages"].append("Failed to import Enquiry Register.")
            except Exception as e:
                results["messages"].append(f"Enquiry import error: {str(e)}")
        else:
            results["messages"].append("'Enquiry Register - From 2019' sheet not found.")
            
        # Run ML engine to link customers and remove duplicates
        try:
            from scripts.run_customer_matcher import deduplicate_and_link_customers
            deduplicate_and_link_customers()
            results["messages"].append("Successfully linked and deduplicated customers using ML engine.")
        except Exception as e:
            logger.error(f"Error running ML Customer matching: {str(e)}")
            results["messages"].append(f"Customer deduplication error: {str(e)}")

        return results
    except Exception as e:
        logger.error(f"Bulk import failed: {str(e)}")
        results["messages"].append(f"Critical error: {str(e)}")
        return results

def get_combined_enquiry_data(sales_engineer=None, month=None, region=None, customer=None, search=None, year=None):
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        query = 'SELECT r.*, p.status as pricing_status, p.probability, p.remarks, p.lost_reason, (SELECT SUM(CAST(json_extract(f.costs, "$.total_selling_price") AS REAL)) FROM Fans f WHERE f.project_id = p.id) as total_value, (SELECT COUNT(*) FROM Fans f WHERE f.project_id = p.id) as fan_count FROM EnquiryRegister r LEFT JOIN Projects p ON r.enquiry_number = p.enquiry_number WHERE 1=1'
        params = []
        if sales_engineer: query += " AND r.sales_engineer = ?"; params.append(sales_engineer)
        if month: query += " AND r.month = ?"; params.append(month)
        if region: query += " AND r.region = ?"; params.append(region)
        if customer: query += " AND r.customer_name = ?"; params.append(customer)
        if year and year != 'All': query += " AND r.year = ?"; params.append(year)
        if search: query += " AND (r.enquiry_number LIKE ? OR r.customer_name LIKE ?)"; params.append(f'%{search}%'); params.append(f'%{search}%')
        query += " ORDER BY r.year DESC, r.enquiry_number DESC"
        cursor.execute(query, params); rows = cursor.fetchall()
        res = [dict(r) for r in rows]
        for r in res:
            if not r['pricing_status']: r['pricing_status'] = 'Not Started'
        conn.close(); return res
    except Exception as e:
        logger.error(f"Error: {e}"); return []

def get_ai_insights():
    """Generate rule-based AI insights from historical data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insights = []
        
        # 1. Lead Prioritization (Hot Leads)
        cursor.execute('''
            SELECT enquiry_number, customer_name, probability 
            FROM Projects 
            WHERE status = 'Live' 
            ORDER BY probability DESC, id DESC 
            LIMIT 3
        ''')
        hot_leads = cursor.fetchall()
        if hot_leads:
            enqs = ", ".join([row['enquiry_number'] for row in hot_leads])
            insights.append({
                'type': 'hot_lead',
                'title': 'Lead Prioritization',
                'text': f"Focus on these leads—they have the highest win chance: {enqs}.",
                'icon': 'trending_up',
                'color': '#10b981'
            })

        # 2. Stale Alerts (Enquiries)
        has_updated_at = _table_has_column(cursor, 'Projects', 'updated_at')
        if has_updated_at:
            cursor.execute('''
                SELECT enquiry_number, total_fans 
                FROM Projects 
                WHERE status = 'Live' AND updated_at < datetime('now', '-15 days')
                LIMIT 2
            ''')
            stale_leads = cursor.fetchall()
            for lead in stale_leads:
                insights.append({
                    'type': 'stale',
                    'title': 'Stale Enquiry Alert',
                    'text': f"Enquiry {lead['enquiry_number']} hasn't been updated in 15 days. Don't let it go cold!",
                    'icon': 'timer',
                    'color': '#f59e0b'
                })

        # 2.b. Predictive Churn (Customer Stale Alerts)
        try:
            from datetime import datetime
            cursor.execute("SELECT customer_name, month FROM Orders WHERE customer_name IS NOT NULL AND month IS NOT NULL")
            all_orders = cursor.fetchall()
            
            customer_dates = {}
            for row in all_orders:
                c_name = row['customer_name'].strip().upper()
                month_str = row['month'].strip() # format: "Jan-26"
                try:
                    dt = datetime.strptime(month_str, '%b-%y')
                    if c_name not in customer_dates:
                        customer_dates[c_name] = []
                    customer_dates[c_name].append(dt)
                except ValueError:
                    pass

            churn_risks = []
            now = datetime.now()
            for c_name, dates in customer_dates.items():
                if len(dates) >= 3:
                    dates.sort()
                    # Calculate average days between orders
                    intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                    avg_interval = sum(intervals) / len(intervals) if intervals else 0
                    
                    if avg_interval > 0:
                        days_since_last = (now - dates[-1]).days
                        # If it's been 1.5x longer than their usual order interval
                        if days_since_last > (avg_interval * 1.5) and days_since_last > 45:
                            churn_risks.append((c_name, days_since_last))

            # Pick top 2 churn risks 
            churn_risks.sort(key=lambda x: x[1], reverse=True)
            for c_name, days in churn_risks[:2]:
                insights.append({
                    'type': 'churn_risk',
                    'title': 'Predictive Churn Alert',
                    'text': f"Customer {c_name.title()} usually orders more frequently but hasn't placed an order in {days} days.",
                    'icon': 'warning',
                    'color': '#ef4444'
                })
        except Exception as e:
            logger.error(f"Error calculating predictive churn: {str(e)}")

        # 3. Revenue Forecasting
        cursor.execute('''
            SELECT SUM((SELECT SUM(CAST(json_extract(f.costs, "$.total_selling_price") AS REAL)) 
                        FROM Fans f WHERE f.project_id = p.id) * p.probability / 100.0) as forecast
            FROM Projects p
            WHERE p.status = 'Live'
        ''')
        forecast = cursor.fetchone()['forecast'] or 0
        if forecast > 0:
            insights.append({
                'type': 'forecast',
                'title': 'Revenue Forecast',
                'text': f"High confidence of hitting ₹{(forecast/10000000):.2f}Cr in orders based on current 'Live' pipeline.",
                'icon': 'insights',
                'color': '#3b82f6'
            })

        # 4. Market Intelligence (Region Trends)
        cursor.execute('''
            SELECT region, COUNT(*) as count 
            FROM Orders 
            WHERE year = strftime('%Y', 'now')
            GROUP BY region 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        top_region = cursor.fetchone()
        if top_region:
            insights.append({
                'type': 'market',
                'title': 'Market Intelligence',
                'text': f"{top_region['region']} is your most active region this year. Ensure material pricing is competitive there!",
                'icon': 'public',
                'color': '#8b5cf6'
            })

        # 5. Team Performance
        cursor.execute("SELECT COUNT(*) as count FROM Orders WHERE month = strftime('%m', 'now')")
        this_month_orders = cursor.fetchone()['count'] or 0
        insights.append({
            'type': 'team',
            'title': 'Team Performance',
            'text': f"The team has closed {this_month_orders} orders so far this month. Keep the momentum going!",
            'icon': 'groups',
            'color': '#6366f1'
        })
        
        conn.close()
        return insights
        
    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        return []

def derive_enquiry_date(enq_num):
    if not enq_num or not isinstance(enq_num, str):
        return None
    import re
    # Match EQYYMM format
    match = re.search(r'EQ(\d{2})(\d{2})', enq_num)
    if match:
        year = "20" + match.group(1)
        month = match.group(2)
        return f"{year}-{month}-01"
    # Match TCF-YYYY format
    match_tcf = re.search(r'TCF-(\d{4})', enq_num)
    if match_tcf:
        return f"{match_tcf.group(1)}-01-01"
    return None

def derive_order_date(year, month):
    if not year: return None
    month_map = {
        'January':'01','February':'02','March':'03','April':'04','May':'05','June':'06',
        'July':'07','August':'08','September':'09','October':'10','November':'11','December':'12'
    }
    m = month_map.get(str(month).strip(), '01')
    # Use the year value directly, handle potential strings like '2024-25'
    y = str(year).split('-')[0][:4]
    return f"{y}-{m}-01"

def get_all_customers_with_metrics():
    """Get all customers with aggregate metrics for the directory listing."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.id, c.primary_name, c.last_visit_date, c.created_at,
                (SELECT region FROM CustomerYearBindings WHERE customer_id = c.id ORDER BY year DESC LIMIT 1) as region,
                (SELECT sales_engineer FROM CustomerYearBindings WHERE customer_id = c.id ORDER BY year DESC LIMIT 1) as latest_sales_engineer,
                (SELECT COUNT(*) FROM Orders o WHERE o.customer_id = c.id) as total_orders,
                (SELECT SUM(order_value) FROM Orders o WHERE o.customer_id = c.id) as total_order_value,
                (SELECT COUNT(*) FROM EnquiryRegister e WHERE e.customer_id = c.id) as total_enquiries,
                (SELECT enquiry_number FROM EnquiryRegister e WHERE e.customer_id = c.id ORDER BY year DESC, month DESC LIMIT 1) as latest_enquiry_num,
                (SELECT year FROM Orders o WHERE o.customer_id = c.id ORDER BY year DESC, 
                    CASE month 
                        WHEN 'December' THEN 12 WHEN 'November' THEN 11 WHEN 'October' THEN 10 
                        WHEN 'September' THEN 9 WHEN 'August' THEN 8 WHEN 'July' THEN 7 
                        WHEN 'June' THEN 6 WHEN 'May' THEN 5 WHEN 'April' THEN 4 
                        WHEN 'March' THEN 3 WHEN 'February' THEN 2 WHEN 'January' THEN 1 
                        ELSE 0 END DESC LIMIT 1) as latest_order_year,
                (SELECT month FROM Orders o WHERE o.customer_id = c.id ORDER BY year DESC, 
                    CASE month 
                        WHEN 'December' THEN 12 WHEN 'November' THEN 11 WHEN 'October' THEN 10 
                        WHEN 'September' THEN 9 WHEN 'August' THEN 8 WHEN 'July' THEN 7 
                        WHEN 'June' THEN 6 WHEN 'May' THEN 5 WHEN 'April' THEN 4 
                        WHEN 'March' THEN 3 WHEN 'February' THEN 2 WHEN 'January' THEN 1 
                        ELSE 0 END DESC LIMIT 1) as latest_order_month
            FROM Customers c
            ORDER BY c.primary_name ASC
        ''')
        rows = cursor.fetchall()
        customers = []
        for row in rows:
            c = dict(row)
            # Derive real dates
            enq_date = derive_enquiry_date(c.get('latest_enquiry_num'))
            ord_date = derive_order_date(c.get('latest_order_year'), c.get('latest_order_month'))
            
            c['last_enquiry_date'] = enq_date
            c['last_order_date'] = ord_date
            
            # Find max for last activity
            dates = [d for d in [c.get('last_visit_date'), enq_date, ord_date] if d]
            c['last_activity'] = max(dates) if dates else None
            
            customers.append(c)
        
        conn.close()
        return customers
    except Exception as e:
        logger.error(f"Error fetching all customers: {str(e)}")
        return []

def get_customer_summary_stats():
    """Get high-level summary stats for the customer dashboard."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total Customers
        cursor.execute("SELECT COUNT(*) FROM Customers")
        stats['total_customers'] = cursor.fetchone()[0]
        
        # Active This Year (Enquiries or Orders in current year)
        current_year = datetime.datetime.now().strftime('%Y')
        cursor.execute('''
            SELECT COUNT(DISTINCT customer_id) FROM (
                SELECT customer_id FROM Orders WHERE year = ?
                UNION
                SELECT customer_id FROM EnquiryRegister WHERE year = ?
            )
        ''', (current_year, current_year))
        stats['active_this_year'] = cursor.fetchone()[0]
        
        # New This Month: Customers whose FIRST activity (Enquiry or Order) is in the current month.
        # This is more accurate than relying on the created_at timestamp which often reflects bulk imports.
        current_year_str = datetime.datetime.now().strftime('%Y')
        current_month_name = datetime.datetime.now().strftime('%B')
        
        cursor.execute('''
            SELECT COUNT(DISTINCT customer_id) FROM (
                SELECT customer_id, year, month FROM EnquiryRegister
                UNION ALL
                SELECT customer_id, year, month FROM Orders
            ) t1
            WHERE year = ? AND month = ?
            AND customer_id NOT IN (
                SELECT customer_id FROM (
                    SELECT customer_id, year, month FROM EnquiryRegister
                    UNION ALL
                    SELECT customer_id, year, month FROM Orders
                ) t2
                WHERE CAST(year AS INTEGER) < ? OR (CAST(year AS INTEGER) = ? AND 
                    CASE month 
                        WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 
                        WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 
                        WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 
                        WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 
                        ELSE 0 END < (CASE ? WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 
                                            WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 
                                            WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 
                                            WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 ELSE 0 END)
                )
            )
        ''', (current_year_str, current_month_name, int(current_year_str), int(current_year_str), current_month_name))
        stats['new_this_month'] = cursor.fetchone()[0]
        
        # Regions
        cursor.execute("SELECT COUNT(DISTINCT region) FROM CustomerYearBindings WHERE region IS NOT NULL AND region != ''")
        stats['total_regions'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Error fetching customer summary stats: {str(e)}")
        return {
            'total_customers': 0,
            'active_this_year': 0,
            'new_this_month': 0,
            'total_regions': 0
        }

def get_customer_360(customer_id):
    """Get comprehensive 360 degree profile data for a specific customer."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Basic Info
        cursor.execute("SELECT * FROM Customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        if not row: return None
        customer = dict(row)
        
        # 1.5 Year Bindings (Region & Sales Engineer context)
        cursor.execute("SELECT year, region, sales_engineer FROM CustomerYearBindings WHERE customer_id = ? ORDER BY year DESC", (customer_id,))
        bindings = [dict(row) for row in cursor.fetchall()]
        customer['year_bindings'] = bindings
        if bindings:
            customer['region'] = bindings[0].get('region')
            customer['sales_engineer'] = bindings[0].get('sales_engineer')
        
        # 2. Aliases
        cursor.execute("SELECT alias_name FROM CustomerAliases WHERE customer_id = ?", (customer_id,))
        aliases = [row['alias_name'] for row in cursor.fetchall()]
        customer['aliases'] = aliases
        
        # 3. YOY Orders & Enquiries
        # Group by year
        cursor.execute('''
            SELECT year, COUNT(*) as count, SUM(order_value) as total_value
            FROM Orders 
            WHERE customer_id = ? 
            GROUP BY year
            ORDER BY year DESC
        ''', (customer_id,))
        customer['orders_by_year'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT year, COUNT(*) as count
            FROM EnquiryRegister
            WHERE customer_id = ?
            GROUP BY year
            ORDER BY year DESC
        ''', (customer_id,))
        customer['enquiries_by_year'] = [dict(row) for row in cursor.fetchall()]
        
        # 4. Activity Timeline
        timeline = []
        
        cursor.execute('''
            SELECT enquiry_number as ref, 'Enquiry' as type, created_at as original_date, sales_engineer, region, year, month
            FROM EnquiryRegister WHERE customer_id = ?
        ''', (customer_id,))
        for row in cursor.fetchall():
            item = dict(row)
            # Try to derive date from enquiry number
            derived = derive_enquiry_date(item.get('ref'))
            item['date'] = derived if derived else item.get('original_date')
            timeline.append(item)
            
        cursor.execute('''
            SELECT job_ref as ref, 'Order' as type, year, month, sales_engineer, order_value
            FROM Orders WHERE customer_id = ?
        ''', (customer_id,))
        for row in cursor.fetchall():
            item = dict(row)
            item['date'] = derive_order_date(item.get('year'), item.get('month'))
            timeline.append(item)
            
        timeline.sort(key=lambda x: str(x.get('date', '')), reverse=True)
        customer['timeline'] = timeline[:50] # Last 50 activities
        
        # 5. Conversion Metrics
        total_enq = sum(y['count'] for y in customer['enquiries_by_year'])
        total_ord = sum(y['count'] for y in customer['orders_by_year'])
        customer['total_enquiries'] = total_enq
        customer['total_orders'] = total_ord
        customer['conversion_rate'] = round((total_ord / total_enq * 100), 1) if total_enq > 0 else 0
        customer['total_order_value'] = sum(y['total_value'] for y in customer['orders_by_year'] if y['total_value'])
        
        conn.close()
        return customer
    except Exception as e:
        logger.error(f"Error fetching customer 360 profile: {str(e)}")
        return None

def update_customer_visit(customer_id, visit_date):
    """Update the last in-person visit date for a customer."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Customers SET last_visit_date = ? WHERE id = ?", (visit_date, customer_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating customer visit date: {str(e)}")
        return False

def get_suggested_merges():
    """Find pairs of customers with highly similar names to suggest merges."""
    try:
        from services.customer_matcher import similarity_score, clean_company_name
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, primary_name FROM Customers ORDER BY id DESC")
        customers = cursor.fetchall()
        
        # Pre-clean names to save time in the O(N^2) loop
        cleaned_customers = []
        for c in customers:
            cleaned_customers.append({
                'id': c['id'],
                'primary_name': c['primary_name'],
                'cleaned_name': clean_company_name(c['primary_name'])
            })
        
        suggestions = []
        # O(N^2) but fine for a small dataset.
        for i in range(len(cleaned_customers)):
            name1 = cleaned_customers[i]['cleaned_name']
            if len(name1) < 3: continue
            
            for j in range(i + 1, len(cleaned_customers)):
                name2 = cleaned_customers[j]['cleaned_name']
                if len(name2) < 3: continue
                
                score = similarity_score(name1, name2)
                if 0.85 <= score < 0.99: # Highly similar but not identical
                    suggestions.append({
                        'primary_customer': {
                            'id': cleaned_customers[i]['id'],
                            'primary_name': cleaned_customers[i]['primary_name']
                        },
                        'secondary_customer': {
                            'id': cleaned_customers[j]['id'],
                            'primary_name': cleaned_customers[j]['primary_name']
                        },
                        'score': score
                    })
                    
        conn.close()
        # Sort by highest score first
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:20] # Return top 20 suggestions
    except Exception as e:
        logger.error(f"Error getting suggested merges: {str(e)}")
        return []

def merge_customers(primary_id, secondary_id):
    """Merge secondary customer into primary, reassigning all related records."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Get secondary name to add as an alias
        cursor.execute("SELECT primary_name FROM Customers WHERE id = ?", (secondary_id,))
        sec_row = cursor.fetchone()
        if not sec_row:
            return False
        sec_name = sec_row['primary_name']
        
        # 2. Add alias to primary
        cursor.execute('''
            INSERT OR IGNORE INTO CustomerAliases (customer_id, alias_name) 
            VALUES (?, ?)
        ''', (primary_id, sec_name))
        
        # 3. Update all foreign keys
        cursor.execute("UPDATE Projects SET customer_id = ? WHERE customer_id = ?", (primary_id, secondary_id))
        cursor.execute("UPDATE Orders SET customer_id = ? WHERE customer_id = ?", (primary_id, secondary_id))
        cursor.execute("UPDATE EnquiryRegister SET customer_id = ? WHERE customer_id = ?", (primary_id, secondary_id))
        
        # 3.5 Reassign CustomerYearBindings, ignore if primary already has a binding for that year
        cursor.execute("UPDATE OR IGNORE CustomerYearBindings SET customer_id = ? WHERE customer_id = ?", (primary_id, secondary_id))
        
        # 4. Delete old aliases and left-over bindings
        cursor.execute("UPDATE CustomerAliases SET customer_id = ? WHERE customer_id = ?", (primary_id, secondary_id))
        cursor.execute("DELETE FROM CustomerYearBindings WHERE customer_id = ?", (secondary_id,))
        
        # 5. Delete secondary customer
        cursor.execute("DELETE FROM Customers WHERE id = ?", (secondary_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error merging customers: {str(e)}")
        return False

def add_manual_enquiry(data):
    """Add a manually entered enquiry to the database."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        customer_id = data.get('customer_id')
        if not customer_id and data.get('customer_name'):
            cursor.execute("SELECT id FROM Customers WHERE primary_name = ?", (data['customer_name'],))
            row = cursor.fetchone()
            if row:
                customer_id = row['id']
            else:
                cursor.execute("INSERT INTO Customers (primary_name) VALUES (?)", 
                               (data['customer_name'],))
                customer_id = cursor.lastrowid
                
        # Update Year Bindings        
        if data.get('year'):
            cursor.execute('''
                INSERT OR REPLACE INTO CustomerYearBindings (id, customer_id, year, region, sales_engineer)
                VALUES (
                    (SELECT id FROM CustomerYearBindings WHERE customer_id = ? AND year = ?),
                    ?, ?, ?, ?
                )
            ''', (customer_id, data.get('year'), customer_id, data.get('year'), data.get('region'), data.get('sales_engineer')))
                
        cursor.execute('''
            INSERT INTO EnquiryRegister (enquiry_number, year, month, sales_engineer, customer_id, customer_name, region, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'manual')
        ''', (
            data.get('enquiry_number'),
            data.get('year'),
            data.get('month'),
            data.get('sales_engineer'),
            customer_id,
            data.get('customer_name'),
            data.get('region')
        ))
        
        # Ensure project exists
        cursor.execute('''
            INSERT INTO Projects (enquiry_number, customer_name, sales_engineer, total_fans, status, year, month, source, customer_id)
            VALUES (?, ?, ?, 1, 'Live', ?, ?, 'manual', ?)
        ''', (
            data.get('enquiry_number'),
            data.get('customer_name'),
            data.get('sales_engineer'),
            data.get('year'),
            data.get('month'),
            customer_id
        ))
        
        conn.commit()
        conn.close()
        return True, "Enquiry saved successfully"
    except Exception as e:
        logger.error(f"Error saving manual enquiry: {str(e)}")
        return False, str(e)

def add_manual_order(data):
    """Add a manually entered order to the database."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        customer_id = data.get('customer_id')
        if not customer_id and data.get('customer_name'):
            cursor.execute("SELECT id FROM Customers WHERE primary_name = ?", (data['customer_name'],))
            row = cursor.fetchone()
            if row:
                customer_id = row['id']
            else:
                cursor.execute("INSERT INTO Customers (primary_name) VALUES (?)", 
                               (data['customer_name'],))
                customer_id = cursor.lastrowid
                
        # Update Year Bindings        
        if data.get('year'):
            cursor.execute('''
                INSERT OR REPLACE INTO CustomerYearBindings (id, customer_id, year, region, sales_engineer)
                VALUES (
                    (SELECT id FROM CustomerYearBindings WHERE customer_id = ? AND year = ?),
                    ?, ?, ?, ?
                )
            ''', (customer_id, data.get('year'), customer_id, data.get('year'), data.get('region'), data.get('sales_engineer')))
                
        cursor.execute('''
            INSERT INTO Orders (job_ref, year, month, customer_id, customer_name, sales_engineer, region, order_value, qty, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual')
        ''', (
            data.get('job_ref'),
            data.get('year'),
            data.get('month'),
            customer_id,
            data.get('customer_name'),
            data.get('sales_engineer'),
            data.get('region'),
            data.get('order_value', 0),
            data.get('qty', 1)
        ))
        
        conn.commit()
        conn.close()
        return True, "Order saved successfully"
    except Exception as e:
        logger.error(f"Error saving manual order: {str(e)}")
        return False, str(e)

def create_users_table():
    """Create the users table and insert default users if not present."""
    try:
        conn = get_db_connection()
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
        logger.info("Users table created or already exists in unified database.")
        return True
    except Exception as e:
        logger.error(f"Error creating users table: {e}")
        return False

def search_customers(query):
    """Search customers by name for autocomplete."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, primary_name, (SELECT region FROM CustomerYearBindings WHERE customer_id = c.id ORDER BY year DESC LIMIT 1) as region FROM Customers c WHERE primary_name LIKE ? LIMIT 10", (f'%{query}%',))
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return customers
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        return []
