import sqlite3
import logging
import os
import json

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
        # Local development path
        base_path = 'data'
    
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
        
        # Create Projects table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT NOT NULL UNIQUE,
                customer_name TEXT NOT NULL,
                total_fans INTEGER NOT NULL,
                sales_engineer TEXT NOT NULL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        # Ensure required columns exist on Projects (for older databases)
        cursor.execute("PRAGMA table_info(Projects)")
        project_columns = {row[1] for row in cursor.fetchall()}
        if 'created_at' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN created_at TIMESTAMP")
        if 'updated_at' not in project_columns:
            cursor.execute("ALTER TABLE Projects ADD COLUMN updated_at TIMESTAMP")
        
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
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
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
        
        # Migrate data from ProjectFans if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
        if cursor.fetchone():
            logger.info("Migrating data from ProjectFans to unified schema...")
            
            # Get all unique projects from Projects table (not ProjectFans)
            cursor.execute('''
                SELECT DISTINCT enquiry_number, customer_name, total_fans, sales_engineer
                FROM Projects
                WHERE enquiry_number IS NOT NULL
            ''')
            projects = cursor.fetchall()
            
            for project in projects:
                enquiry_number, customer_name, total_fans, sales_engineer = project
                
                # Insert or update project (already exists, just ensure it's in new format)
                cursor.execute('''
                    INSERT OR REPLACE INTO Projects (enquiry_number, customer_name, total_fans, sales_engineer)
                    VALUES (?, ?, ?, ?)
                ''', (enquiry_number, customer_name, total_fans, sales_engineer))
                # Get project id reliably
                cursor.execute('SELECT id FROM Projects WHERE enquiry_number = ?', (enquiry_number,))
                pid_row = cursor.fetchone()
                project_id = pid_row['id'] if pid_row else None
                
                # Get fans for this project
                cursor.execute('''
                    SELECT * FROM ProjectFans 
                    WHERE project_id = ?
                    ORDER BY fan_number
                ''', (project_id,))
                
                fans = cursor.fetchall()
                
                for fan in fans:
                    # Convert ProjectFans row to JSON structures
                    specifications = {
                        'fan_model': fan['fan_model'] if 'fan_model' in fan.keys() else None,
                        'size': fan['size'] if 'size' in fan.keys() else None,
                        'class': fan['class'] if 'class' in fan.keys() else None,
                        'arrangement': fan['arrangement'] if 'arrangement' in fan.keys() else None,
                        'vendor': fan['vendor'] if 'vendor' in fan.keys() else None,
                        'material': fan['material'] if 'material' in fan.keys() else None,
                        'accessories': fan['accessories'] if 'accessories' in fan.keys() else None,
                        'custom_accessories': fan['custom_accessories'] if 'custom_accessories' in fan.keys() else None,
                        'optional_items': fan['optional_items'] if 'optional_items' in fan.keys() else None,
                        'custom_option_items': fan['custom_option_items'] if 'custom_option_items' in fan.keys() else None,
                        'vibration_isolators': fan['vibration_isolators'] if 'vibration_isolators' in fan.keys() else None,
                        'drive_pack_kw': fan['drive_pack_kw'] if 'drive_pack_kw' in fan.keys() else None,
                        'fabrication_margin': fan['fabrication_margin'] if 'fabrication_margin' in fan.keys() else None,
                        'bought_out_margin': fan['bought_out_margin'] if 'bought_out_margin' in fan.keys() else None,
                        'vendor_rate': fan['vendor_rate'] if 'vendor_rate' in fan.keys() else None,
                        'ms_percentage': fan['ms_percentage'] if 'ms_percentage' in fan.keys() else None,
                        'custom_no_of_isolators': fan['custom_no_of_isolators'] if 'custom_no_of_isolators' in fan.keys() else None,
                        'custom_shaft_diameter': fan['custom_shaft_diameter'] if 'custom_shaft_diameter' in fan.keys() else None,
                        'material_name_0': fan['material_name_0'] if 'material_name_0' in fan.keys() else None,
                        'material_weight_0': fan['material_weight_0'] if 'material_weight_0' in fan.keys() else None,
                        'material_rate_0': fan['material_rate_0'] if 'material_rate_0' in fan.keys() else None,
                        'material_name_1': fan['material_name_1'] if 'material_name_1' in fan.keys() else None,
                        'material_weight_1': fan['material_weight_1'] if 'material_weight_1' in fan.keys() else None,
                        'material_rate_1': fan['material_rate_1'] if 'material_rate_1' in fan.keys() else None,
                        'material_name_2': fan['material_name_2'] if 'material_name_2' in fan.keys() else None,
                        'material_weight_2': fan['material_weight_2'] if 'material_weight_2' in fan.keys() else None,
                        'material_rate_2': fan['material_rate_2'] if 'material_rate_2' in fan.keys() else None,
                        'material_name_3': fan['material_name_3'] if 'material_name_3' in fan.keys() else None,
                        'material_weight_3': fan['material_weight_3'] if 'material_weight_3' in fan.keys() else None,
                        'material_rate_3': fan['material_rate_3'] if 'material_rate_3' in fan.keys() else None,
                        'material_name_4': fan['material_name_4'] if 'material_name_4' in fan.keys() else None,
                        'material_weight_4': fan['material_weight_4'] if 'material_weight_4' in fan.keys() else None,
                        'material_rate_4': fan['material_rate_4'] if 'material_rate_4' in fan.keys() else None
                    }
                    
                    weights = {
                        'bare_fan_weight': fan['bare_fan_weight'] if 'bare_fan_weight' in fan.keys() else None,
                        'accessory_weight': fan['accessory_weight'] if 'accessory_weight' in fan.keys() else None,
                        'total_weight': fan['total_weight'] if 'total_weight' in fan.keys() else None,
                        'fabrication_weight': fan['fabrication_weight'] if 'fabrication_weight' in fan.keys() else None,
                        'bought_out_weight': fan['bought_out_weight'] if 'bought_out_weight' in fan.keys() else None,
                        'no_of_isolators': fan['no_of_isolators'] if 'no_of_isolators' in fan.keys() else None,
                        'shaft_diameter': fan['shaft_diameter'] if 'shaft_diameter' in fan.keys() else None
                    }
                    
                    costs = {
                        'fabrication_cost': fan['fabrication_cost'] if 'fabrication_cost' in fan.keys() else None,
                        'motor_cost': fan['motor_cost'] if 'motor_cost' in fan.keys() else None,
                        'vibration_isolators_cost': fan['vibration_isolators_cost'] if 'vibration_isolators_cost' in fan.keys() else None,
                        'drive_pack_cost': fan['drive_pack_cost'] if 'drive_pack_cost' in fan.keys() else None,
                        'bearing_cost': fan['bearing_cost'] if 'bearing_cost' in fan.keys() else None,
                        'optional_items_cost': fan['optional_items_cost'] if 'optional_items_cost' in fan.keys() else None,
                        'flex_connectors_cost': fan['flex_connectors_cost'] if 'flex_connectors_cost' in fan.keys() else None,
                        'bought_out_cost': fan['bought_out_cost'] if 'bought_out_cost' in fan.keys() else None,
                        'total_cost': fan['total_cost'] if 'total_cost' in fan.keys() else None,
                        'fabrication_selling_price': fan['fabrication_selling_price'] if 'fabrication_selling_price' in fan.keys() else None,
                        'bought_out_selling_price': fan['bought_out_selling_price'] if 'bought_out_selling_price' in fan.keys() else None,
                        'total_selling_price': fan['total_selling_price'] if 'total_selling_price' in fan.keys() else None,
                        'total_job_margin': fan['total_job_margin'] if 'total_job_margin' in fan.keys() else None
                    }
                    
                    motor = {
                        'motor_kw': fan['motor_kw'] if 'motor_kw' in fan.keys() else None,
                        'motor_brand': fan['motor_brand'] if 'motor_brand' in fan.keys() else None,
                        'motor_pole': fan['motor_pole'] if 'motor_pole' in fan.keys() else None,
                        'motor_efficiency': fan['motor_efficiency'] if 'motor_efficiency' in fan.keys() else None,
                        'motor_discount_rate': fan['motor_discount_rate'] if 'motor_discount_rate' in fan.keys() else None,
                        'bearing_brand': fan['bearing_brand'] if 'bearing_brand' in fan.keys() else None
                    }
                    
                    # Get fan_number from the fan row
                    fan_number = fan['fan_number'] if 'fan_number' in fan.keys() else 1
                    
                    # Check if fan already exists to prevent duplicates
                    cursor.execute('''
                        SELECT id FROM Fans WHERE project_id = ? AND fan_number = ?
                    ''', (project_id, fan_number))
                    existing_fan = cursor.fetchone()
                    
                    if not existing_fan:
                        # Insert fan only if it doesn't exist
                        cursor.execute('''
                            INSERT INTO Fans (project_id, fan_number, status, specifications, weights, costs, motor)
                            VALUES (?, ?, 'added', ?, ?, ?, ?)
                        ''', (
                            project_id, 
                            fan_number,
                            json.dumps(specifications),
                            json.dumps(weights),
                            json.dumps(costs),
                            json.dumps(motor)
                        ))
                        logger.info(f"Migrated fan {fan_number} for project {enquiry_number}")
                    else:
                        logger.info(f"Fan {fan_number} already exists for project {enquiry_number}, skipping")
            
            logger.info("Migration completed successfully")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error migrating to unified schema: {str(e)}")
        return False

# Project/Fan CRUD functions
def create_or_update_project(enquiry_number, customer_name, total_fans, sales_engineer):
    """Create or update a project and ensure fan placeholders exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert or update project (be compatible with older schemas without updated_at)
        if _table_has_column(cursor, 'Projects', 'updated_at'):
            cursor.execute('''
                INSERT OR REPLACE INTO Projects (enquiry_number, customer_name, total_fans, sales_engineer, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (enquiry_number, customer_name, total_fans, sales_engineer))
        else:
            cursor.execute('''
                INSERT OR REPLACE INTO Projects (enquiry_number, customer_name, total_fans, sales_engineer)
                VALUES (?, ?, ?, ?)
            ''', (enquiry_number, customer_name, total_fans, sales_engineer))
        
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
        select_cols = 'enquiry_number, customer_name, total_fans, sales_engineer' + (', updated_at' if select_updated else '')

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
                'sales_engineer': p['sales_engineer']
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
            
            # Ensure the fan row exists (idempotent)
            cursor.execute('''
                INSERT OR IGNORE INTO Fans (project_id, fan_number, status)
                VALUES (?, ?, 'draft')
            ''', (project_id, fan_number))

            # Update fan
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
            
            if cursor.rowcount == 0:
                # As a safety net, try creating the record explicitly, then update again
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
                # No need to run update again; inserted with latest data
            
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