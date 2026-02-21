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

def get_all_vendor_rates():
    """Get all vendor rates from the database structured for frontend use."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT Vendor, "Material Type", WeightStart, WeightEnd, MSPrice, SS304Price FROM VendorWeightDetails')
        rows = cursor.fetchall()
        conn.close()
        
        # Structure: rates[vendor][material] = [{min, max, rate}, ...]
        rates = {}
        
        for row in rows:
            vendor = row['Vendor']
            material_type = row['Material Type'] # 'ms' or 'ss304' usually, but DB schema might differ
            weight_start = float(row['WeightStart'])
            weight_end = float(row['WeightEnd'])
            ms_price = float(row['MSPrice'])
            ss304_price = float(row['SS304Price'])
            
            if vendor not in rates:
                rates[vendor] = {
                    'ms': [],
                    'ss304': []
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
        
        # Create Projects table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT NOT NULL UNIQUE,
                customer_name TEXT NOT NULL,
                total_fans INTEGER NOT NULL,
                sales_engineer TEXT NOT NULL,
                status TEXT DEFAULT 'Live',
                probability INTEGER DEFAULT 50,
                remarks TEXT DEFAULT '',
                month TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
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
        
        # Create Orders table for the Order Details Dashboard
        # Only create if it doesn't exist to preserve data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_ref TEXT,
                year TEXT,
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
                remarks TEXT
            )
        ''')
        
        # Create EnquiryRegister table for the Enquiry Tracking Dashboard
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EnquiryRegister (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT UNIQUE,
                year TEXT,
                month TEXT,
                sales_engineer TEXT,
                customer_name TEXT,
                region TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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

def update_project_status(enquiry_number, status, probability, remarks=None):
    """Update just the status, probability, and optionally remarks of a project."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Safely determine updated_at and remarks columns
        update_clause = "status = ?, probability = ?"
        params = [status, probability]
        
        if remarks is not None and _table_has_column(cursor, 'Projects', 'remarks'):
            update_clause += ", remarks = ?"
            params.append(remarks)
            
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
        
        # Select and rename columns
        df = df[list(col_map.keys())].rename(columns=col_map)
        
        # Clean data: drop rows without JOB REF
        df = df.dropna(subset=['job_ref'])
        df['job_ref'] = df['job_ref'].astype(str).str.strip()
        df = df[df['job_ref'] != '']
        df = df[df['job_ref'] != 'nan']
        
        # Convert numerical columns
        num_cols = ['order_value', 'our_cost', 'contribution_value', 'contribution_percentage', 'qty']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Replace NaN with None for SQLite
        df = df.replace({np.nan: None})
        
        records = df.to_dict('records')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing orders to rely entirely on the Excel sheet as truth
        cursor.execute("DELETE FROM Orders")
        
        # Insert new records
        cursor.executemany('''
            INSERT INTO Orders (
                job_ref, year, customer_name, sales_engineer, region, 
                order_value, our_cost, warranty, contribution_value, 
                contribution_percentage, qty, month, rep, type_of_customer, 
                sector, po_number, end_user, remarks
            ) VALUES (
                :job_ref, :year, :customer_name, :sales_engineer, :region,
                :order_value, :our_cost, :warranty, :contribution_value,
                :contribution_percentage, :qty, :month, :rep, :type_of_customer,
                :sector, :po_number, :end_user, :remarks
            )
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
        cols = [c for c in mapping.keys() if c in df.columns]
        df = df[cols].rename(columns=mapping)
        if 'enquiry_number' not in df.columns: return False
        df = df.dropna(subset=['enquiry_number'])
        df['enquiry_number'] = df['enquiry_number'].astype(str).str.strip()
        df = df.drop_duplicates(subset=['enquiry_number'], keep='first')
        def get_m(enq):
            if len(enq) >= 6 and enq.startswith('EQ'):
                m = {'01':'January','02':'February','03':'March','04':'April','05':'May','06':'June','07':'July','08':'August','09':'September','10':'October','11':'November','12':'December'}
                return m.get(enq[4:6], 'Unknown')
            return 'Unknown'
        df['month'] = df['enquiry_number'].apply(get_m)
        df = df.replace({np.nan: None})
        recs = df.to_dict('records')
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("DELETE FROM EnquiryRegister")
        cursor.executemany('INSERT OR REPLACE INTO EnquiryRegister (enquiry_number, year, month, sales_engineer, customer_name, region) VALUES (:enquiry_number, :year, :month, :sales_engineer, :customer_name, :region)', recs)
        conn.commit(); conn.close()
        return True
    except Exception as e:
        logger.error(f"Error importing enquiries: {e}")
        return False

def bulk_import_from_excel(file) -> dict:
    """Import both Orders and Enquiries from a single Excel file."""
    results = {"orders": False, "enquiries": False, "messages": []}
    try:
        import pandas as pd
        # Load the Excel file once
        xlsx = pd.ExcelFile(file)
        sheet_names = xlsx.sheet_names
        
        # Import Orders if sheet exists
        if "Order Register - From 2019" in sheet_names:
            try:
                # We need to pass the file-like object or the xlsx object? 
                # pandas read_excel can take the xlsx object.
                success = import_orders_from_excel(file)
                results["orders"] = success
                if success: results["messages"].append("Successfully imported Orders.")
                else: results["messages"].append("Failed to import Orders.")
            except Exception as e:
                results["messages"].append(f"Order import error: {str(e)}")
        else:
            results["messages"].append("'Order Register - From 2019' sheet not found.")

        # Import Enquiries if sheet exists
        # Reset file pointer for the second read if we passed the file
        if hasattr(file, 'seek'):
            file.seek(0)
            
        if "Enquiry Register - From 2019" in sheet_names:
            try:
                success = import_enquiries_from_excel(file)
                results["enquiries"] = success
                if success: results["messages"].append("Successfully imported Enquiry Register.")
                else: results["messages"].append("Failed to import Enquiry Register.")
            except Exception as e:
                results["messages"].append(f"Enquiry import error: {str(e)}")
        else:
            results["messages"].append("'Enquiry Register - From 2019' sheet not found.")
            
        return results
    except Exception as e:
        logger.error(f"Bulk import failed: {str(e)}")
        results["messages"].append(f"Critical error: {str(e)}")
        return results

def get_combined_enquiry_data(sales_engineer=None, month=None, region=None, customer=None, search=None, year=None):
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        query = 'SELECT r.*, p.status as pricing_status, p.probability, p.remarks, (SELECT SUM(CAST(json_extract(f.costs, "$.total_selling_price") AS REAL)) FROM Fans f WHERE f.project_id = p.id) as total_value, (SELECT COUNT(*) FROM Fans f WHERE f.project_id = p.id) as fan_count FROM EnquiryRegister r LEFT JOIN Projects p ON r.enquiry_number = p.enquiry_number WHERE 1=1'
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
