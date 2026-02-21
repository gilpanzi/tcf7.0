import os
import logging
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from routes import register_routes
from database import get_db_connection
import create_projects_table  # Import the create_projects_table module
import create_bearing_lookup  # Import create_bearing_lookup module
import update_central_database  # Import the update_central_database module
from datetime import timedelta
from db_admin import register_db_admin_routes  # Import the new db_admin module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    # Configure static files properly for production
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    app = Flask(__name__, 
                static_folder=static_folder)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Flask application...")
    logger.info(f"Static folder: {static_folder}")
    
    # Configure session
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'TCF_Pricing_Tool_Secret_Key_2024_Dev_Only')  # Use env var or dev fallback
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Sessions last 24 hours
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # Secure cookies in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    
    # Enable CORS with more options for production
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    
    # Custom static route with proper MIME types
    @app.route('/static/<path:filename>')
    def custom_static(filename):
        mime_type = None
        if filename.endswith('.css'):
            mime_type = 'text/css'
        elif filename.endswith('.js'):
            mime_type = 'application/javascript'
        return send_from_directory(static_folder, filename, mimetype=mime_type)
    
    # Create database tables if they don't exist
    logger.info("Creating database tables if needed...")
    if create_projects_table.create_projects_tables():
        logger.info("Project tables created or already exist")
    else:
        logger.error("Failed to create project tables")
    
    # Apply schema.sql only if database is empty (safe initialization)
    if os.path.exists('schema.sql'):
        logger.info("Found schema.sql - checking if database needs initialization...")
        try:
            from database import get_db_connection, migrate_to_unified_schema
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if any tables exist with data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()
            
            has_data = False
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                if count > 0:
                    has_data = True
                    logger.info(f"Found {count} records in {table_name} - skipping schema.sql")
                    break
            
            if not has_data:
                logger.info("Database is empty - applying schema.sql for initialization...")
                with open('schema.sql', 'r') as f:
                    conn.executescript(f.read())
                logger.info("Successfully applied schema.sql to database")
            else:
                logger.info("Database has data - skipping schema.sql to preserve existing data")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error checking/applying schema.sql: {str(e)}")
    
    # Create or update BearingLookup table
    logger.info("Creating BearingLookup table if needed...")
    if create_bearing_lookup.create_bearing_lookup_table():
        logger.info("BearingLookup table created or already exists")
    else:
        logger.error("Failed to create BearingLookup table")
    
    # Update central database if needed
    logger.info("Updating central database if needed...")
    if update_central_database.update_central_database():
        logger.info("Central database updated or already up-to-date")
    else:
        logger.error("Failed to update central database")
    
    # Fix database schema first
    logger.info("Fixing database schema...")
    from database import fix_database_schema, migrate_to_unified_schema
    if fix_database_schema():
        logger.info("Database schema fixed successfully")
    else:
        logger.error("Failed to fix database schema")
    
    # Migrate to unified schema
    logger.info("Migrating to unified schema...")
    if migrate_to_unified_schema():
        logger.info("Unified schema migration completed")
    else:
        logger.error("Failed to migrate to unified schema")
    
    # Register routes
    register_routes(app)
    
    # Register database admin routes
    register_db_admin_routes(app)
    
    @app.route('/add_custom_accessory', methods=['POST'])
    def add_custom_accessory():
        try:
            data = request.get_json()
            required_fields = ['fan_model', 'fan_size', 'name', 'weight']
            
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            cursor = get_db_connection().cursor()
            cursor.execute(
                'INSERT INTO AccessoryWeights (fan_model, fan_size, accessory, weight, is_custom) VALUES (?, ?, ?, ?, 1)',
                (data['fan_model'], data['fan_size'], data['name'], data['weight'])
            )
            get_db_connection().commit()
            
            return jsonify({'message': 'Custom accessory added successfully', 'id': cursor.lastrowid})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/get_accessories', methods=['POST'])
    def get_accessories():
        try:
            data = request.get_json()
            if not data or 'fan_model' not in data or 'fan_size' not in data:
                return jsonify({'error': 'Fan model and size are required'}), 400
            
            cursor = get_db_connection().cursor()
            cursor.execute(
                'SELECT id, accessory, weight, is_custom FROM AccessoryWeights WHERE fan_model = ? AND fan_size = ?',
                (data['fan_model'], data['fan_size'])
            )
            accessories = [{'id': row[0], 'name': row[1], 'weight': row[2], 'is_custom': bool(row[3])} for row in cursor.fetchall()]
            return jsonify({'accessories': accessories})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/remove_custom_accessory', methods=['POST'])
    def remove_custom_accessory():
        try:
            data = request.get_json()
            if not data or 'id' not in data:
                return jsonify({'error': 'Accessory ID is required'}), 400
            
            cursor = get_db_connection().cursor()
            cursor.execute(
                'DELETE FROM AccessoryWeights WHERE id = ? AND is_custom = 1',
                (data['id'],)
            )
            get_db_connection().commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Custom accessory not found or cannot be deleted'}), 404
            
            return jsonify({'message': 'Custom accessory removed successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)