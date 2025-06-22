from flask import render_template, request, jsonify, redirect, url_for, session, flash, send_file
import logging
from database import get_db_connection, load_dropdown_options
from calculations import calculate_fan_weight, calculate_fabrication_cost, calculate_bought_out_components, ACCESSORY_NAME_MAP
import json
import os
from datetime import datetime
import sqlite3
import pandas as pd
from functools import wraps
import hashlib
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook
from openpyxl.styles.borders import Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Run migration immediately when module is loaded
def migrate_database():
    """Migrate the database schema."""
    try:
        # Create a base directory for data and a subdirectory for the central database
        data_dir = 'data'
        central_db_dir = os.path.join(data_dir, 'central_database')
        os.makedirs(central_db_dir, exist_ok=True)
        central_db_name = os.path.join(central_db_dir, 'all_projects.db')
        
        # If the central database doesn't exist in the data directory but exists in the original location,
        # copy it to the data directory
        original_db_path = 'central_database/all_projects.db'
        if not os.path.exists(central_db_name) and os.path.exists(original_db_path):
            import shutil
            shutil.copy(original_db_path, central_db_name)
            logger.info(f"Copied central database to {central_db_name}")
        
        # Connect to the central database
        conn = sqlite3.connect(central_db_name)
        cursor = conn.cursor()
        
        # Drop and recreate ProjectFans table with all required columns
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
                custom_accessories TEXT,
                optional_items TEXT,
                custom_option_items TEXT,
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
                FOREIGN KEY (enquiry_number) REFERENCES Projects(enquiry_number)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projectfans_enquiry ON ProjectFans(enquiry_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projectfans_fan_number ON ProjectFans(fan_number)')
        
        conn.commit()
        conn.close()
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        if 'conn' in locals():
            conn.close()

# Run migration immediately
migrate_database()

def register_routes(app):
    """Register all routes for the application."""
    
    # Run database migration first
    migrate_database()
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, username, password, full_name, is_admin FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()
                
                if user and user[2] == password:  # Simple password comparison
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['full_name'] = user[3]
                    session['is_admin'] = user[4]
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error='Invalid username or password')
        
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/')
    @login_required
    def index():
        """Render the main page with all dropdown options."""
        try:
            options = load_dropdown_options()
            return render_template('index.html', **options)
        except Exception as e:
            logger.error(f"Error loading index page: {str(e)}")
            return "An error occurred while loading the page", 500

    @app.route('/calculate_fan', methods=['POST'])
    def calculate_fan():
        """Calculate weight and cost based on form data."""
        try:
            data = request.json
            logger.info("Calculating fan data")
            logger.info(f"Received data: {data}")
            
            fan_data = {
                'Fan Model': data['Fan_Model'],
                'Fan Size': data['Fan_Size'],
                'Class': data['Class'],
                'Arrangement': data['Arrangement'],
                'vendor': data.get('vendor', 'TCF Factory'),
                'material': data.get('material', 'ms'),
                'vibration_isolators': data.get('vibration_isolators', 'not_required'),
                'fabrication_margin': float(data.get('fabrication_margin', 25)),
                'bought_out_margin': float(data.get('bought_out_margin', 25)),
                'motor_brand': data.get('motor_brand', ''),
                'motor_kw': data.get('motor_kw', ''),
                'pole': data.get('pole', ''),
                'efficiency': data.get('efficiency', ''),
                'motor_discount': float(data.get('motor_discount', 0)),
                'drive_pack': data.get('drive_pack'),  # Add drive pack value
                'customAccessories': data.get('customAccessories', {}),  # Add custom accessories
                'optional_items': data.get('optional_items', {})  # <-- Add this line
            }
            
            # Log the drive pack value for debugging
            logger.info(f"Drive pack value from frontend: {fan_data['drive_pack']}")
            
            # Get selected accessories - handle both object and array formats
            selected_accessories = []
            if 'accessories' in data:
                if isinstance(data['accessories'], dict):
                    selected_accessories = [key for key, value in data['accessories'].items() if value]
                elif isinstance(data['accessories'], list):
                    selected_accessories = data['accessories']
            
            # Add custom material data if present
            if fan_data['material'] == 'others':
                for i in range(5):
                    weight_key = f'material_weight_{i}'
                    name_key = f'material_name_{i}'
                    rate_key = f'material_rate_{i}'
                    if weight_key in data:
                        fan_data[weight_key] = float(data[weight_key])
                    if name_key in data:
                        fan_data[name_key] = data[name_key]
                    if rate_key in data:
                        fan_data[rate_key] = float(data[rate_key])
                # Use no_of_isolators and shaft_diameter from request if present
                no_of_isolators = data.get('no_of_isolators')
                shaft_diameter = data.get('shaft_diameter')
            else:
                no_of_isolators = None
                shaft_diameter = None
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get fan weight data
                bare_fan_weight, db_no_of_isolators, db_shaft_diameter, total_weight, fan_error, accessory_details = calculate_fan_weight(
                    cursor, fan_data, selected_accessories
                )
                # For 'others', override with user input if provided
                if fan_data['material'] == 'others':
                    if no_of_isolators is None:
                        no_of_isolators = db_no_of_isolators
                    if shaft_diameter is None:
                        shaft_diameter = db_shaft_diameter
                else:
                    no_of_isolators = db_no_of_isolators
                    shaft_diameter = db_shaft_diameter
                
                if fan_error:
                    logger.error(f"Error in fan weight calculation: {fan_error}")
                    return jsonify({'success': False, 'message': fan_error}), 400
                
                # Calculate fabrication cost
                fabrication_cost, total_weight, custom_weights, fab_error = calculate_fabrication_cost(cursor, fan_data, total_weight)
                if fab_error:
                    logger.error(f"Error in fabrication cost calculation: {fab_error}")
                    return jsonify({'success': False, 'message': fab_error}), 400

                # Calculate bought out components cost
                bought_out_result, error = calculate_bought_out_components(cursor, fan_data, no_of_isolators, shaft_diameter)
                if error:
                    logger.error(f"Error in bought out components calculation: {error}")
                    return jsonify({'success': False, 'message': error}), 400
                
                # Extract individual component costs
                bought_out_cost = bought_out_result['total_cost']
                vibration_isolators_price = bought_out_result['vibration_isolators_price']
                bearing_price = bought_out_result['bearing_price']
                drive_pack_price = bought_out_result['drive_pack_price']
                motor_list_price = bought_out_result['motor_list_price']
                motor_discount = bought_out_result['motor_discount']
                discounted_motor_price = bought_out_result['discounted_motor_price']
                
                # Add optional items to bought out cost
                optional_items_cost = 0
                optional_items_detail = {}
                
                # Process optional items from request
                if 'optional_items' in fan_data:
                    for item_name, item_price in fan_data['optional_items'].items():
                        if item_price and float(item_price) > 0:
                            optional_items_cost += float(item_price)
                            optional_items_detail[item_name] = float(item_price)
                
                # Add optional items cost to bought out cost
                bought_out_cost += optional_items_cost
                
                # Calculate total costs and margins
                fabrication_selling_price = fabrication_cost / (1 - fan_data['fabrication_margin'] / 100)
                bought_out_selling_price = bought_out_cost / (1 - fan_data['bought_out_margin'] / 100)
                total_selling_price = fabrication_selling_price + bought_out_selling_price + optional_items_cost
                
                # Calculate total job margin
                total_raw_cost = fabrication_cost + bought_out_cost
                if total_raw_cost > 0:
                    # Calculate the effective margin percentage
                    total_job_margin = (1 - (total_raw_cost / total_selling_price)) * 100
                else:
                    total_job_margin = 0
                
                # Calculate standard accessories weight
                standard_accessory_weight = sum(weight for name, weight in accessory_details.items() 
                                             if name in ACCESSORY_NAME_MAP.values())
                
                # Calculate custom accessories weight
                custom_accessory_weight = sum(weight for name, weight in accessory_details.items() 
                                           if name not in ACCESSORY_NAME_MAP.values())
                
                # Prepare response data
                response_data = {
                    'success': True,
                    'bare_fan_weight': bare_fan_weight,
                    'accessory_weights': standard_accessory_weight + custom_accessory_weight,
                    'total_weight': total_weight,
                    'fabrication_cost': fabrication_cost,
                    'bought_out_cost': bought_out_cost,
                    'optional_items_cost': optional_items_cost,
                    'optional_items_detail': optional_items_detail,
                    'total_raw_cost': total_raw_cost,
                    'fabrication_selling_price': fabrication_selling_price,
                    'bought_out_selling_price': bought_out_selling_price,
                    'total_selling_price': total_selling_price,
                    'total_job_margin': total_job_margin,
                    'custom_accessories': {
                        'weights': {name: weight for name, weight in accessory_details.items() 
                                  if name not in ACCESSORY_NAME_MAP.values()}
                    },
                    # Add individual bought-out component prices
                    'vibration_isolators_price': vibration_isolators_price,
                    'bearing_price': bearing_price,
                    'drive_pack_price': drive_pack_price,
                    'motor_list_price': motor_list_price,
                    'discounted_motor_price': discounted_motor_price,
                    'motor_discount': motor_discount,
                    'no_of_isolators': no_of_isolators,
                    'shaft_diameter': shaft_diameter
                }
                
                logger.info(f"Calculation response: {response_data}")
                return jsonify(response_data)
                
        except Exception as e:
            logger.error(f"Error in calculate_fan: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/add_fan_model', methods=['POST'])
    def add_fan_model():
        """Add a new fan model to the database."""
        data = request.json
        logger.info(f"Adding new fan model: {data}")

        # Validate mandatory fields
        if not all(key in data for key in ['new_fan_model', 'new_fan_size', 'new_class', 'new_arrangement', 'new_bare_fan_weight']):
            logger.error("Missing mandatory fields for new fan model")
            return jsonify({'success': False, 'message': 'Missing mandatory fields.'})

        # Validate Shaft Diameter for non-Arrangement 4
        if data['new_arrangement'] != '4' and 'new_shaft_diameter' not in data:
            logger.error("Shaft Diameter is mandatory for non-Arrangement 4")
            return jsonify({'success': False, 'message': 'Shaft Diameter is mandatory for arrangements other than 4.'})

        # Prepare data for insertion
        fan_data = {
            'fan_model': data['new_fan_model'],
            'fan_size': data['new_fan_size'],
            'class_': data['new_class'],
            'arrangement': data['new_arrangement'],
            'bare_fan_weight': float(data['new_bare_fan_weight']),
            'shaft_diameter': float(data.get('new_shaft_diameter', 0)) if data['new_arrangement'] != '4' else None,
            'no_of_isolators': int(data.get('new_no_of_isolators', 0)) if data.get('new_no_of_isolators') else 0,
            'accessories': data.get('new_accessories', {})
        }

        # Insert into the database
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if this combination already exists
                cursor.execute('''
                    SELECT COUNT(*) FROM FanWeights 
                    WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
                ''', (
                    fan_data['fan_model'], 
                    fan_data['fan_size'], 
                    fan_data['class_'], 
                    fan_data['arrangement']
                ))
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # Update existing entry
                    logger.info(f"Updating existing fan model: {fan_data['fan_model']}/{fan_data['fan_size']}/{fan_data['class_']}/{fan_data['arrangement']}")
                    cursor.execute('''
                        UPDATE FanWeights SET 
                        "Bare Fan Weight" = ?, 
                        "Shaft Diameter" = ?,
                        "No. of Isolators" = ?,
                        "Unitary Base Frame" = ?,
                        "Isolation Base Frame" = ?,
                        "Split Casing" = ?,
                        "Inlet Companion Flange" = ?,
                        "Outlet Companion Flange" = ?,
                        "Inlet Butterfly Damper" = ?
                        WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
                    ''', (
                        fan_data['bare_fan_weight'], 
                        fan_data['shaft_diameter'],
                        fan_data['no_of_isolators'],
                        fan_data['accessories'].get('Unitary Base Frame', 0),
                        fan_data['accessories'].get('Isolation Base Frame', 0),
                        fan_data['accessories'].get('Split Casing', 0),
                        fan_data['accessories'].get('Inlet Companion Flange', 0),
                        fan_data['accessories'].get('Outlet Companion Flange', 0),
                        fan_data['accessories'].get('Inlet Butterfly Damper', 0),
                        fan_data['fan_model'], 
                        fan_data['fan_size'], 
                        fan_data['class_'], 
                        fan_data['arrangement']
                    ))
                    
                    message = 'Fan model updated successfully!'
                else:
                    # Insert new entry
                    logger.info(f"Inserting new fan model: {fan_data['fan_model']}/{fan_data['fan_size']}/{fan_data['class_']}/{fan_data['arrangement']}")
                    cursor.execute('''
                        INSERT INTO FanWeights (
                            "Fan Model", "Fan Size", "Class", "Arrangement", "Bare Fan Weight", "Shaft Diameter",
                            "No. of Isolators", "Unitary Base Frame", "Isolation Base Frame", "Split Casing", 
                            "Inlet Companion Flange", "Outlet Companion Flange", "Inlet Butterfly Damper"
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        fan_data['fan_model'], 
                        fan_data['fan_size'], 
                        fan_data['class_'], 
                        fan_data['arrangement'],
                        fan_data['bare_fan_weight'], 
                        fan_data['shaft_diameter'],
                        fan_data['no_of_isolators'],
                        fan_data['accessories'].get('Unitary Base Frame', 0),
                        fan_data['accessories'].get('Isolation Base Frame', 0),
                        fan_data['accessories'].get('Split Casing', 0),
                        fan_data['accessories'].get('Inlet Companion Flange', 0),
                        fan_data['accessories'].get('Outlet Companion Flange', 0),
                        fan_data['accessories'].get('Inlet Butterfly Damper', 0)
                    ))
                    
                    message = 'New fan model added successfully!'
                
                conn.commit()
                logger.info(message)
                return jsonify({'success': True, 'message': message})
                
        except Exception as e:
            logger.error(f"Error adding/updating fan model: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': f'Error with fan model: {str(e)}'})

    @app.route('/get_motor_options')
    def get_motor_options():
        """Get all available motor kW values."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT "Motor kW" FROM MotorPrices ORDER BY CAST("Motor kW" AS FLOAT)')
            options = [str(row[0]) for row in cursor.fetchall()]
            conn.close()
            return jsonify(options)
        except Exception as e:
            logger.error(f"Error getting motor options: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/get_pole_options/<motor_kw>')
    def get_pole_options(motor_kw):
        """Get available pole options for a given motor kW."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT Pole FROM MotorPrices WHERE "Motor kW" = ? ORDER BY Pole', (motor_kw,))
            options = [str(row[0]) for row in cursor.fetchall()]
            conn.close()
            return jsonify(options)
        except Exception as e:
            logger.error(f"Error getting pole options: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/get_efficiency_options/<motor_kw>/<pole>')
    def get_efficiency_options(motor_kw, pole):
        """Get available efficiency options for a given motor kW and pole."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT DISTINCT Efficiency FROM MotorPrices WHERE "Motor kW" = ? AND Pole = ? ORDER BY Efficiency',
                (motor_kw, pole)
            )
            options = [str(row[0]) for row in cursor.fetchall()]
            conn.close()
            return jsonify(options)
        except Exception as e:
            logger.error(f"Error getting efficiency options: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/get_accessory_weight', methods=['POST'])
    def get_accessory_weight():
        """Get weight for a specific accessory."""
        try:
            data = request.json
            logger.info(f"Getting accessory weight for: {data}")
            
            # First check session for custom/manual weight
            session_key = f"accessory_weight_{data['fan_model']}_{data['fan_size']}_{data['class_']}_{data['arrangement']}_{data['accessory']}"
            if session_key in session:
                return jsonify({
                    'success': True,
                    'weight': session[session_key],
                    'source': 'session'
                })
            
            # If not in session, check database for standard weight
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Map frontend accessory name to database column name
                db_column = ACCESSORY_NAME_MAP.get(data['accessory'])
                if not db_column:
                    return jsonify({
                        'success': False, 
                        'error': f'Invalid accessory type: {data["accessory"]}'
                    })
                
                cursor.execute(f'''
                    SELECT "{db_column}"
                    FROM FanWeights
                    WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
                ''', (
                    data['fan_model'],
                    data['fan_size'],
                    data['class_'],
                    data['arrangement']
                ))
                
                result = cursor.fetchone()
                if not result or result[0] is None:
                    return jsonify({
                        'success': False, 
                        'error': 'No accessory weight found'
                    })
                
                return jsonify({
                    'success': True,
                    'weight': result[0],
                    'source': 'database'
                })
                
        except Exception as e:
            logger.error(f"Error getting accessory weight: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/save_accessory_weight', methods=['POST'])
    def save_accessory_weight():
        try:
            data = request.get_json()
            logger.info(f"Received accessory weight data: {data}")
            
            fan_model = data.get('fan_model')
            fan_size = data.get('fan_size')
            class_ = data.get('class') or data.get('class_')  # Handle both class and class_
            arrangement = data.get('arrangement')
            accessory = data.get('accessory')
            weight = data.get('weight')

            if not all([fan_model, fan_size, class_, arrangement, accessory, weight]):
                return jsonify({
                    'success': False,
                    'message': 'Missing required fields'
                }), 400

            # Map frontend accessory name to database column name
            accessory_column = ACCESSORY_NAME_MAP.get(accessory, accessory)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if column exists in FanWeights table
                cursor.execute("PRAGMA table_info(FanWeights)")
                columns = [col[1] for col in cursor.fetchall()]
                if accessory_column not in columns:
                    return jsonify({
                        'success': False,
                        'message': f'Column {accessory_column} does not exist in FanWeights table'
                    }), 400

                # Update the accessory weight in the existing row
                cursor.execute(f"""
                    UPDATE FanWeights
                    SET "{accessory_column}" = ?
                    WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
                """, (weight, fan_model, fan_size, class_, arrangement))

                if cursor.rowcount == 0:
                    logger.error(f"No matching fan found for: {fan_model}, {fan_size}, {class_}, {arrangement}")
                    return jsonify({
                        'success': False,
                        'message': 'No matching fan found in database'
                    }), 404
                
                conn.commit()
                logger.info(f"Successfully updated {accessory_column} weight to {weight} kg")
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully saved {accessory_column} weight'
                })
                
        except Exception as e:
            logger.error(f"Error saving accessory weight: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Error saving accessory weight: {str(e)}'
            }), 500

    @app.route('/get_available_sizes/<fan_model>')
    def get_available_sizes(fan_model):
        """Get available sizes for a given fan model."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT "Fan Size"
                FROM FanWeights
                WHERE "Fan Model" = ?
                ORDER BY CAST("Fan Size" AS INTEGER)
            ''', (fan_model,))
            sizes = [str(row[0]) for row in cursor.fetchall()]
            logger.debug(f"Retrieved sizes for fan model {fan_model}: {sizes}")
            return jsonify({'sizes': sizes})
        except Exception as e:
            logger.error(f"Error getting available sizes for {fan_model}: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                conn.close()

    @app.route('/get_available_classes/<fan_model>/<fan_size>')
    def get_available_classes(fan_model, fan_size):
        """Get available classes for a given fan model and size."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT "Class"
                FROM FanWeights
                WHERE "Fan Model" = ? AND "Fan Size" = ?
                ORDER BY "Class"
            ''', (fan_model, fan_size))
            classes = [row[0] for row in cursor.fetchall()]
            return jsonify({'classes': classes})

    @app.route('/get_available_arrangements/<fan_model>/<fan_size>/<class_>')
    def get_available_arrangements(fan_model, fan_size, class_):
        """Get available arrangements for a given fan model, size, and class."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT "Arrangement"
                FROM FanWeights
                WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ?
                ORDER BY "Arrangement"
            ''', (fan_model, fan_size, class_))
            arrangements = [str(row[0]) for row in cursor.fetchall()]
            conn.close()
            return jsonify({"arrangements": arrangements})
        except Exception as e:
            logger.error(f"Error getting available arrangements: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
    @app.route('/get_bearing_data/<fan_model>/<fan_size>/<class_>/<arrangement>/<bearing_brand>')
    def get_bearing_data(fan_model, fan_size, class_, arrangement, bearing_brand):
        """Get bearing data based on fan details and bearing brand."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # First, get the shaft diameter from the fan specifications
            cursor.execute('''
                SELECT "Shaft Diameter"
                FROM FanWeights
                WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
            ''', (fan_model, fan_size, class_, arrangement))
            
            result = cursor.fetchone()
            if not result or result[0] is None:
                conn.close()
                return jsonify({
                    "success": False,
                    "message": f"No shaft diameter found for the specified fan configuration"
                })
            
            shaft_diameter = result[0]
            logger.info(f"Found shaft diameter {shaft_diameter} for {fan_model}/{fan_size}/{class_}/{arrangement}")
            
            # Now, get the bearing details from BearingLookup
            cursor.execute('''
                SELECT Brand, ShaftDiameter, Description, Bearing, PlummerBlock, Sleeve, Total
                FROM BearingLookup
                WHERE Brand = ? AND ShaftDiameter = ?
            ''', (bearing_brand, shaft_diameter))
            
            bearing_result = cursor.fetchone()
            
            # If no exact match, find the next suitable size
            if not bearing_result:
                cursor.execute('''
                    SELECT Brand, ShaftDiameter, Description, Bearing, PlummerBlock, Sleeve, Total
                    FROM BearingLookup
                    WHERE Brand = ? AND ShaftDiameter > ?
                    ORDER BY ShaftDiameter ASC
                    LIMIT 1
                ''', (bearing_brand, shaft_diameter))
                bearing_result = cursor.fetchone()
                if bearing_result:
                    logger.info(f"No exact match found for shaft diameter {shaft_diameter}, using next available size: {bearing_result[1]}")
            
            conn.close()
            
            if not bearing_result:
                return jsonify({
                    "success": False,
                    "message": f"No bearing found for brand {bearing_brand} and shaft diameter {shaft_diameter}"
                })
            
            # Return the bearing data
            return jsonify({
                "success": True,
                "shaft_diameter": shaft_diameter,
                "bearing_diameter": bearing_result[1],
                "description": bearing_result[2],
                "bearing_cost": bearing_result[3],
                "plummer_block_cost": bearing_result[4],
                "sleeve_cost": bearing_result[5],
                "price": bearing_result[6]
            })
            
        except Exception as e:
            logger.error(f"Error getting bearing data: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route('/calculate_motor_price', methods=['POST'])
    def calculate_motor_price():
        """Calculate motor price based on specifications."""
        try:
            data = request.json
            if not all(key in data for key in ['motor_kw', 'pole', 'brand', 'efficiency']):
                return jsonify({
                    'success': False,
                    'message': 'Missing required fields'
                }), 400

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Price 
                FROM MotorPrices 
                WHERE "Motor kW" = ? AND Pole = ? AND Brand = ? AND Efficiency = ?
            ''', (data['motor_kw'], data['pole'], data['brand'], data['efficiency']))
            
            result = cursor.fetchone()
            conn.close()

            if result:
                return jsonify({
                    'success': True,
                    'price': float(result[0])
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No price found for the specified configuration'
                }), 404

        except Exception as e:
            logger.error(f"Error calculating motor price: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    def save_to_database(fan_data, enquiry_number, customer_name, total_fans, sales_engineer):
        """Save fan data to the local database."""
        try:
            conn = sqlite3.connect('fan_pricing.db')
            cursor = conn.cursor()
            
            # Create Projects table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enquiry_number TEXT UNIQUE,
                    customer_name TEXT,
                    total_fans INTEGER,
                    sales_engineer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert or get existing project
            cursor.execute('''
                INSERT OR IGNORE INTO Projects (enquiry_number, customer_name, total_fans, sales_engineer)
                VALUES (?, ?, ?, ?)
            ''', (enquiry_number, customer_name, total_fans, sales_engineer))
            
            # Get the project ID
            cursor.execute('SELECT id FROM Projects WHERE enquiry_number = ?', (enquiry_number,))
            project_id = cursor.fetchone()[0]
            
            # Insert fan data with project_id
            cursor.execute('''
                INSERT INTO ProjectFans (
                    project_id, enquiry_number, fan_number, fan_model, size, class, arrangement, vendor, material,
                    accessories, custom_accessories, optional_items, custom_option_items,
                    bare_fan_weight, accessory_weight, total_weight, fabrication_weight, bought_out_weight,
                    fabrication_cost, motor_cost, vibration_isolators_cost, drive_pack_cost, bearing_cost,
                    optional_items_cost, flex_connectors_cost, bought_out_cost, total_cost,
                    fabrication_selling_price, bought_out_selling_price, total_selling_price, total_job_margin,
                    vibration_isolators, drive_pack_kw, motor_kw, motor_brand, motor_pole, motor_efficiency,
                    motor_discount_rate, bearing_brand, shaft_diameter, no_of_isolators, fabrication_margin,
                    bought_out_margin, material_name_0, material_weight_0, material_rate_0,
                    material_name_1, material_weight_1, material_rate_1, material_name_2, material_weight_2,
                    material_rate_2, material_name_3, material_weight_3, material_rate_3,
                    material_name_4, material_weight_4, material_rate_4, custom_no_of_isolators, custom_shaft_diameter
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_id, fan_data['enquiry_number'], fan_data['fan_number'], fan_data['fan_model'],
                fan_data['fan_size'], fan_data['class_'], fan_data['arrangement'], fan_data['vendor'],
                fan_data['material'], fan_data['accessories'], fan_data['custom_accessories'],
                fan_data['optional_items'], fan_data['custom_option_items'],
                fan_data['bare_fan_weight'], fan_data['accessory_weights'], fan_data['total_weight'],
                fan_data['fabrication_weight'], fan_data['bought_out_weight'], fan_data['fabrication_cost'],
                fan_data['motor_cost'], fan_data['vibration_isolators_cost'], fan_data['drive_pack_cost'],
                fan_data['bearing_cost'], fan_data['optional_items_cost'], fan_data['flex_connectors_cost'],
                fan_data['bought_out_cost'], fan_data['total_cost'], fan_data['fabrication_selling_price'],
                fan_data['bought_out_selling_price'], fan_data['total_selling_price'], fan_data['total_job_margin'],
                fan_data['vibration_isolators'], fan_data['drive_pack_kw'], fan_data['motor_kw'],
                fan_data['motor_brand'], fan_data['motor_pole'], fan_data['motor_efficiency'],
                fan_data['motor_discount_rate'], fan_data['bearing_brand'], fan_data['shaft_diameter'],
                fan_data.get('custom_no_of_isolators', 0), fan_data.get('fabrication_margin', 0),
                fan_data.get('bought_out_margin', 0), fan_data['material_name_0'], fan_data['material_weight_0'],
                fan_data['material_rate_0'], fan_data['material_name_1'], fan_data['material_weight_1'],
                fan_data['material_rate_1'], fan_data['material_name_2'], fan_data['material_weight_2'],
                fan_data['material_rate_2'], fan_data['material_name_3'], fan_data['material_weight_3'],
                fan_data['material_rate_3'], fan_data['material_name_4'], fan_data['material_weight_4'],
                fan_data['material_rate_4'], fan_data['custom_no_of_isolators'], fan_data['custom_shaft_diameter']
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Successfully saved fan data for project {enquiry_number}, fan #{fan_data['fan_number']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to local database: {str(e)}", exc_info=True)
            return False
    
    def sync_to_central_database(project_data):
        """Sync project data to the central database."""
        try:
            # Create a base directory for data and a subdirectory for the central database
            data_dir = 'data'
            central_db_dir = os.path.join(data_dir, 'central_database')
            os.makedirs(central_db_dir, exist_ok=True)
            central_db_name = os.path.join(central_db_dir, 'all_projects.db')
            
            # If the central database doesn't exist in the data directory but exists in the original location,
            # copy it to the data directory
            original_db_path = 'central_database/all_projects.db'
            if not os.path.exists(central_db_name) and os.path.exists(original_db_path):
                import shutil
                shutil.copy(original_db_path, central_db_name)
                logger.info(f"Copied central database to {central_db_name}")
            
            conn = sqlite3.connect(central_db_name)
            cursor = conn.cursor()
            
            # Create tables with the same schema as the main save_project_to_database function
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Projects (
                    enquiry_number TEXT PRIMARY KEY,
                    customer_name TEXT,
                    total_fans INTEGER,
                    sales_engineer TEXT,
                    total_weight REAL,
                    total_fabrication_cost REAL,
                    total_bought_out_cost REAL,
                    total_cost REAL,
                    total_selling_price REAL,
                    total_job_margin REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ProjectFans (
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
                    custom_accessories TEXT,
                    optional_items TEXT,
                    custom_option_items TEXT,
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
                    FOREIGN KEY (enquiry_number) REFERENCES Projects(enquiry_number)
                )
            ''')
            
            enquiry_number = project_data['enquiry_number']
            
            # Check if project exists and update/insert
            cursor.execute('SELECT enquiry_number FROM Projects WHERE enquiry_number = ?', (enquiry_number,))
            existing_project = cursor.fetchone()
            
            if existing_project:
                # Update existing project
                cursor.execute('''
                    UPDATE Projects 
                    SET customer_name = ?, total_fans = ?, sales_engineer = ?
                    WHERE enquiry_number = ?
                ''', (project_data['customer_name'], project_data['total_fans'], project_data['sales_engineer'], enquiry_number))
            else:
                # Insert new project
                cursor.execute('''
                    INSERT INTO Projects (enquiry_number, customer_name, total_fans, sales_engineer)
                    VALUES (?, ?, ?, ?)
                ''', (enquiry_number, project_data['customer_name'], project_data['total_fans'], project_data['sales_engineer']))
            
            # Process each fan in the project data
            for fan_data in project_data['fans']:
                # Convert nested fan data structure to flat database format
                fan_db_data = {
                    'enquiry_number': enquiry_number,
                    'fan_number': fan_data.get('fan_number', 1),
                    'fan_model': fan_data['specifications']['fan_model'],
                    'size': fan_data['specifications']['size'],
                    'class': fan_data['specifications']['class'],
                    'arrangement': fan_data['specifications']['arrangement'],
                    'vendor': fan_data['specifications']['vendor'],
                    'material': fan_data['specifications']['material'],
                    'accessories': json.dumps(fan_data['specifications'].get('accessories', {})),
                    'custom_accessories': json.dumps(fan_data['specifications'].get('custom_accessories', {})),
                    'optional_items': json.dumps(fan_data['specifications'].get('optional_items', {})),
                    'custom_option_items': json.dumps(fan_data['specifications'].get('custom_optional_items', {})),
                    'optional_items_json': json.dumps(fan_data['specifications'].get('optional_items', {})),
                    'custom_optional_items_json': json.dumps(fan_data['specifications'].get('custom_option_items', {})),
                    'bare_fan_weight': fan_data['weights']['bare_fan_weight'],
                    'accessory_weight': fan_data['weights']['accessory_weight'],
                    'total_weight': fan_data['weights']['total_weight'],
                    'fabrication_weight': fan_data['weights']['fabrication_weight'],
                    'bought_out_weight': fan_data['weights']['bought_out_weight'],
                    'fabrication_cost': fan_data['costs']['fabrication_cost'],
                    'motor_cost': fan_data['costs']['motor_cost'],
                    'vibration_isolators_cost': fan_data['costs']['vibration_isolators_cost'],
                    'drive_pack_cost': fan_data['costs']['drive_pack_cost'],
                    'bearing_cost': fan_data['costs']['bearing_cost'],
                    'optional_items_cost': fan_data['costs']['optional_items_cost'],
                    'flex_connectors_cost': fan_data['costs']['flex_connectors_cost'],
                    'bought_out_cost': fan_data['costs']['bought_out_cost'],
                    'total_cost': fan_data['costs']['total_cost'],
                    'fabrication_selling_price': fan_data['costs']['fabrication_selling_price'],
                    'bought_out_selling_price': fan_data['costs']['bought_out_selling_price'],
                    'total_selling_price': fan_data['costs']['total_selling_price'],
                    'total_job_margin': fan_data['costs']['total_job_margin'],
                    'vibration_isolators': fan_data['specifications']['vibration_isolators'],
                    'drive_pack_kw': fan_data['specifications'].get('drive_pack_kw', 0),
                    'motor_kw': fan_data['motor']['motor_kw'],
                    'motor_brand': fan_data['motor']['motor_brand'],
                    'motor_pole': fan_data['motor']['motor_pole'],
                    'motor_efficiency': fan_data['motor']['motor_efficiency'],
                    'motor_discount_rate': fan_data['motor'].get('motor_discount_rate', 0),
                    'bearing_brand': fan_data['specifications']['bearing_brand'],
                    'shaft_diameter': fan_data['specifications']['shaft_diameter'],
                    'no_of_isolators': fan_data['specifications'].get('no_of_isolators', 0),
                    'fabrication_margin': fan_data['specifications'].get('fabrication_margin', 25),
                    'bought_out_margin': fan_data['specifications'].get('bought_out_margin', 25),
                }
                
                # Handle material data
                for i in range(5):
                    for key in ['material_name', 'material_weight', 'material_rate']:
                        field_key = f'{key}_{i}'
                        fan_db_data[field_key] = fan_data['specifications'].get(field_key, '')
                
                # Delete existing fan records for this enquiry and fan number
                cursor.execute('DELETE FROM ProjectFans WHERE enquiry_number = ? AND fan_number = ?', 
                             (enquiry_number, fan_db_data['fan_number']))
                
                # Insert the fan data
                columns = list(fan_db_data.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = list(fan_db_data.values())
                
                cursor.execute(f'''
                    INSERT INTO ProjectFans ({', '.join(columns)})
                    VALUES ({placeholders})
                ''', values)
                
            conn.commit()
            conn.close()
            logger.info(f"Successfully synced project {enquiry_number} to central database")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing to central database: {str(e)}", exc_info=True)
            if 'conn' in locals():
                conn.close()
            return False

    # Add route to get drive pack options for the dropdown
    @app.route('/get_drive_pack_options', methods=['GET'])
    def get_drive_pack_options():
        logger.info("==== DRIVE PACK OPTIONS DEBUG ====")
        logger.info("Received request for drive pack options")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Log available tables for debugging
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"Available tables in database: {[table[0] for table in tables]}")
            
            # Get schema for DrivePackLookup
            cursor.execute("PRAGMA table_info(DrivePackLookup);")
            columns = cursor.fetchall()
            logger.info(f"DrivePackLookup table columns: {[col[1] for col in columns]}")
            
            # Get unique Motor kW values from DrivePackLookup table
            query = 'SELECT DISTINCT "Motor kW" FROM DrivePackLookup ORDER BY "Motor kW"'
            logger.info(f"Executing query: {query}")
            cursor.execute(query)
            
            # Fetch all and log raw data
            raw_results = cursor.fetchall()
            logger.info(f"Raw query results: {raw_results}")
            
            drive_pack_options = [float(row[0]) for row in raw_results]
            
            logger.info(f"Processed drive pack options: {drive_pack_options}")
            logger.info(f"Returning {len(drive_pack_options)} drive pack options for dropdown")
            
            conn.close()
            response = {
                'success': True, 
                'options': drive_pack_options
            }
            logger.info(f"Final response: {response}")
            logger.info("==== END DRIVE PACK OPTIONS DEBUG ====")
            return jsonify(response)
        except Exception as e:
            logger.error(f"==== DRIVE PACK ERROR ====")
            logger.error(f"Error getting drive pack options: {str(e)}")
            logger.error(f"Exception details:", exc_info=True)
            logger.error(f"==== END DRIVE PACK ERROR ====")
            return jsonify({
                'success': False,
                'message': f"Error getting options: {str(e)}"
            }), 500

    @app.route('/export_project', methods=['GET', 'POST'])
    @login_required
    def export_project():
        """Export project details to Excel with fan specifications, costs, and all optional items and accessories."""
        try:
            # Get parameters from request
            enquiry_number = request.args.get('enquiry_number') or request.form.get('enquiry_number')
            customer_name = request.args.get('customer_name') or request.form.get('customer_name')
            total_fans = request.args.get('total_fans') or request.form.get('total_fans')
            fans_data_json = request.args.get('fans_data') or request.form.get('fans_data')
            
            if not enquiry_number or not fans_data_json:
                return jsonify({'error': 'Missing required parameters'}), 400
            
            # Helper function to clean numbers for Excel
            def clean_number(value):
                if isinstance(value, (int, float)):
                    return value
                try:
                    # Remove non-numeric characters (except decimal point)
                    if isinstance(value, str):
                        value = value.replace('₹', '').replace(',', '').strip()
                    return float(value)
                except (ValueError, TypeError):
                    return 0
                    
            # Parse fans data JSON
            fans_data = json.loads(fans_data_json)
            
            # Helper function to build exportable fan data
            def build_exportable_fan(fan):
                # Basic specifications
                result = {
                    'Fan Number': fan.get('fan_number', ''),
                    'Model': fan.get('model', ''),
                    'Size': fan.get('size', ''),
                    'Class': fan.get('class', ''),
                    'Arrangement': fan.get('arrangement', ''),
                    'Material': fan.get('material', ''),
                    'Custom Shaft Diameter': fan.get('custom_shaft_diameter', ''),
                    'Custom No. of Isolators': fan.get('custom_no_of_isolators', ''),
                    'Vibration Isolators': fan.get('vibration_isolators', ''),
                    'Bearing Brand': fan.get('bearing_brand', ''),
                }
                
                # Motor details
                result.update({
                    'Motor Brand': fan.get('motor_brand', ''),
                    'Motor Power (kW)': fan.get('motor_power', ''),
                    'Poles': fan.get('poles', ''),
                    'Efficiency': fan.get('efficiency', ''),
                })
                
                # Weight details
                result.update({
                    'Fan Weight (kg)': clean_number(fan.get('fan_weight', 0)),
                    'Accessory Weight (kg)': clean_number(fan.get('accessory_weight', 0)),
                    'Total Weight (kg)': clean_number(fan.get('total_weight', 0)),
                })
                
                # Cost breakdown
                result.update({
                    'Fabrication Cost (₹)': clean_number(fan.get('fabrication_cost', 0)),
                    'Fabrication Selling Price (₹)': clean_number(fan.get('fabrication_selling_price', 0)),
                    'Motor Cost (₹)': clean_number(fan.get('motor_cost', 0)),
                    'Vibration Isolators Cost (₹)': clean_number(fan.get('vibration_isolators_cost', 0)),
                    'Drive Pack Cost (₹)': clean_number(fan.get('drive_pack_cost', 0)),
                    'Bearing Cost (₹)': clean_number(fan.get('bearing_cost', 0)),
                    'Optional Items Cost (₹)': clean_number(fan.get('optional_items_cost', 0)),
                    'Bought Out Cost (₹)': clean_number(fan.get('bought_out_cost', 0)),
                    'Bought Out Selling Price (₹)': clean_number(fan.get('bought_out_selling_price', 0)),
                    'Total Cost (₹)': clean_number(fan.get('total_cost', 0)),
                    'Selling Price (₹)': clean_number(fan.get('selling_price', 0)),
                    'Margin (%)': clean_number(fan.get('margin', 0)),
                })
                
                # Add custom accessories if present
                if fan.get('custom_accessories'):
                    result['Custom Accessories'] = fan.get('custom_accessories')
                    
                # Process accessories section - mark as 'Included' if present
                accessories = fan.get('accessories', {})
                if accessories:
                    # Standard accessory names mapping
                    accessory_names = {
                        'unitary_base_frame': 'Unitary Base Frame',
                        'isolation_base_frame': 'Isolation Base Frame',
                        'split_casing': 'Split Casing',
                        'inlet_guard': 'Inlet Guard',
                        'outlet_guard': 'Outlet Guard',
                        'inlet_flange': 'Inlet Flange',
                        'outlet_flange': 'Outlet Flange',
                        'outlet_companion_flange': 'Outlet Companion Flange',
                        'inlet_butterfly_damper': 'Inlet Butterfly Damper',
                        'inlet_bell': 'Inlet Bell',
                        'inlet_cone': 'Inlet Cone',
                        'drain_plug': 'Drain Plug',
                        'companion_flanges': 'Companion Flanges',
                        'access_door': 'Access Door',
                        'shaft_extension': 'Shaft Extension',
                        'custom_paintwork': 'Custom Paintwork',
                        'mounting_feet': 'Mounting Feet',
                        'flexible_connector': 'Flexible Connector',
                        'inlet_silencer': 'Inlet Silencer',
                        'outlet_silencer': 'Outlet Silencer',
                        'anti_vibration_mounts': 'Anti-Vibration Mounts',
                        'weather_cover': 'Weather Cover',
                        'shaft_seal': 'Shaft Seal',
                        'spark_resistant_construction': 'Spark Resistant Construction',
                        'inspection_door': 'Inspection Door',
                        'roof_curb': 'Roof Curb',
                        'backdraft_damper': 'Backdraft Damper',
                        'cooling_wheel': 'Cooling Wheel',
                        'belt_guard': 'Belt Guard',
                        'extended_lubrication': 'Extended Lubrication',
                        'special_coating': 'Special Coating'
                    }
                    
                    for key, value in accessories.items():
                        if value:
                            display_name = accessory_names.get(key, key.replace('_', ' ').title())
                            result[f"Accessory: {display_name}"] = "Included"
                
                # Process optional items section - include the cost
                optional_items = fan.get('optional_items', {})
                if optional_items:
                    # Standard optional item names mapping
                    optional_item_names = {
                        'flex_connectors': 'Flex Connectors',
                        'silencer': 'Silencer',
                        'testing_charges': 'Testing Charges',
                        'freight_charges': 'Freight Charges',
                        'warranty_charges': 'Warranty Charges',
                        'packing_charges': 'Packing Charges',
                        'amca_sparkproof': 'AMCA Type C Spark Proof Construction',
                        'accessories_assembly': 'Accessories Assembly Charges',
                        'paint_specification': 'Special Paint Specification',
                        'documentation': 'Special Documentation'
                    }
                    
                    for key, price in optional_items.items():
                        price = clean_number(price)
                        if price > 0:
                            # For custom items, extract just the name part
                            if key.startswith('custom_'):
                                # Extract the custom name without the timestamp
                                name_parts = key.replace('custom_', '').split('_')
                                # If the last part is numeric (timestamp), remove it
                                if name_parts and name_parts[-1].isdigit():
                                    name_parts.pop()
                                display_name = ' '.join(name_parts).title()
                            else:
                                display_name = optional_item_names.get(key, key.replace('_', ' ').title())
                            
                            result[f"Optional Item: {display_name}"] = price
                
                # Also check standard_optional_items[] format
                if fan.get("standard_optional_items[]"):
                    items = fan.get("standard_optional_items[]")
                    if not isinstance(items, list):
                        items = [items]
                        
                    for item in items:
                        # Get the price from optionalItemPrices if not already in optional_items
                        if not optional_items.get(item) and fan.get("optionalItemPrices", {}).get(item):
                            price = clean_number(fan["optionalItemPrices"][item])
                            if price > 0:
                                display_name = optional_item_names.get(item, item.replace('_', ' ').title())
                                result[f"Optional Item: {display_name}"] = price
                
                # Process custom materials if present
                for i in range(5):  # Assuming maximum 5 custom materials
                    name_key = f'material_name_{i}'
                    weight_key = f'material_weight_{i}'
                    rate_key = f'material_rate_{i}'
                    
                    if fan.get(name_key) and fan.get(weight_key) and fan.get(rate_key):
                        result[f"Custom Material {i+1}: Name"] = fan.get(name_key)
                        result[f"Custom Material {i+1}: Weight"] = clean_number(fan.get(weight_key))
                        result[f"Custom Material {i+1}: Rate"] = clean_number(fan.get(rate_key))
                
                return result
            
            # Build exportable data for all fans
            exportable_fans = [build_exportable_fan(fan) for fan in fans_data]
            
            # Create a DataFrame with all fans data
            df = pd.DataFrame(exportable_fans)
            
            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write Fan Specifications to Excel
                df.to_excel(writer, sheet_name='Fan Specifications', index=False)
                
                # Get the worksheet to apply formatting
                workbook = writer.book
                worksheet = writer.sheets['Fan Specifications']
                
                # Add formats
                header_format = workbook.add_format({
                    'bold': True, 
                    'font_color': 'white',
                    'bg_color': '#4a90e2',
                    'border': 1,
                    'text_wrap': True,
                    'valign': 'vcenter',
                    'align': 'center'
                })
                
                # Format for currency cells
                currency_format = workbook.add_format({
                    'num_format': '₹#,##0.00',
                    'border': 1
                })
                
                # Format for weight cells
                weight_format = workbook.add_format({
                    'num_format': '#,##0.00" kg"',
                    'border': 1
                })
                
                # Format for percentage cells
                percent_format = workbook.add_format({
                    'num_format': '0.00"%"',
                    'border': 1
                })
                
                # Format for regular cells
                regular_format = workbook.add_format({
                    'border': 1
                })
                
                # Format header row
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    # Set column width based on content type
                    if 'Cost' in value or 'Price' in value:
                        worksheet.set_column(col_num, col_num, 20, currency_format)
                    elif 'Weight' in value:
                        worksheet.set_column(col_num, col_num, 18, weight_format)
                    elif 'Margin' in value:
                        worksheet.set_column(col_num, col_num, 15, percent_format)
                    elif 'Optional Item:' in value:
                        worksheet.set_column(col_num, col_num, 22, currency_format)
                    else:
                        worksheet.set_column(col_num, col_num, 20, regular_format)
                
                # Add project information sheet
                info_sheet = workbook.add_worksheet('Project Information')
                info_sheet.write(0, 0, 'Project Details', header_format)
                info_sheet.merge_range('A1:B1', 'Project Details', header_format)
                
                # Add project details
                info_sheet.write(2, 0, 'Enquiry Number:', regular_format)
                info_sheet.write(2, 1, enquiry_number, regular_format)
                info_sheet.write(3, 0, 'Customer Name:', regular_format)
                info_sheet.write(3, 1, customer_name, regular_format)
                info_sheet.write(4, 0, 'Total Fans:', regular_format)
                info_sheet.write(4, 1, total_fans, regular_format)
                info_sheet.write(5, 0, 'Export Date:', regular_format)
                info_sheet.write(5, 1, datetime.now().strftime('%d-%m-%Y'), regular_format)
                
                # Set column width
                info_sheet.set_column(0, 0, 20)
                info_sheet.set_column(1, 1, 30)
            
            # Save to file and send to user
            output.seek(0)
            filename = f"{enquiry_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            logger.info(f"Excel file created successfully: {filename}")
            return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        except Exception as e:
            logger.error(f"Error exporting project: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/get_project_id/<enquiry_number>')
    @login_required
    def get_project_id(enquiry_number):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM projects WHERE enquiry_number = ?', (enquiry_number,))
                project = cursor.fetchone()
                
                if project:
                    return jsonify({'project_id': project[0]})
                else:
                    return jsonify({'project_id': None}), 404
                    
        except Exception as e:
            logger.error(f"Error getting project ID: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/get_saved_enquiries')
    @login_required
    def get_saved_enquiries():
        """Get all saved enquiries from both databases."""
        try:
            enquiries = []
            
            # Get from local database
            try:
                conn = sqlite3.connect('fan_pricing.db')
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT enquiry_number, customer_name, total_fans, sales_engineer, created_at
                    FROM Projects 
                    ORDER BY created_at DESC
                ''')
                local_enquiries = cursor.fetchall()
                for enq in local_enquiries:
                    enquiries.append({
                        'enquiry_number': enq[0],
                        'customer_name': enq[1] or '',
                        'total_fans': enq[2] or 0,
                        'sales_engineer': enq[3] or '',
                        'created_at': enq[4] or '',
                        'source': 'local'
                    })
                conn.close()
            except Exception as e:
                logger.warning(f"Could not load from local database: {str(e)}")
            
            # Get from central database
            try:
                central_db_path = 'data/central_database/all_projects.db'
                if os.path.exists(central_db_path):
                    conn = sqlite3.connect(central_db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT DISTINCT enquiry_number, customer_name, total_fans, sales_engineer, created_at
                        FROM Projects 
                        ORDER BY created_at DESC
                    ''')
                    central_enquiries = cursor.fetchall()
                    
                    # Add central enquiries that aren't already in the list
                    existing_enquiries = {enq['enquiry_number'] for enq in enquiries}
                    for enq in central_enquiries:
                        if enq[0] not in existing_enquiries:
                            enquiries.append({
                                'enquiry_number': enq[0],
                                'customer_name': enq[1] or '',
                                'total_fans': enq[2] or 0,
                                'sales_engineer': enq[3] or '',
                                'created_at': enq[4] or '',
                                'source': 'central'
                            })
                    conn.close()
            except Exception as e:
                logger.warning(f"Could not load from central database: {str(e)}")
            
            # Sort by enquiry number descending
            enquiries.sort(key=lambda x: x['enquiry_number'], reverse=True)
            
            logger.info(f"Retrieved {len(enquiries)} saved enquiries")
            return jsonify({
                'success': True,
                'enquiries': enquiries
            })
            
        except Exception as e:
            logger.error(f"Error getting saved enquiries: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': str(e),
                'enquiries': []
            })

    @app.route('/store_project_for_export', methods=['POST'])
    @login_required
    def store_project_for_export():
        """Store current project data in session for Excel export"""
        try:
            data = request.get_json()
            logger.info(f"Storing project data for export: {data}")
            
            # Store all project data in session
            session['enquiry_number'] = data.get('enquiry_number', '')
            session['customer_name'] = data.get('customer_name', '')
            session['total_fans'] = data.get('total_fans', 1)
            session['sales_engineer'] = data.get('sales_engineer', session.get('full_name', ''))
            session['fans'] = data.get('fans', [])
            
            logger.info(f"Stored in session - fans count: {len(session.get('fans', []))}")
            return jsonify({'success': True, 'message': 'Project data stored for export'})
            
        except Exception as e:
            logger.error(f"Error storing project data for export: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/export_summary_excel', methods=['GET'])
    @login_required
    def export_summary_excel():
        """Export comprehensive project summary to Excel with all details including optional items, accessories, custom materials, and complete cost breakdowns."""
        try:
            enquiry_number = session.get('enquiry_number')
            customer_name = session.get('customer_name')
            total_fans = session.get('total_fans')
            fans = session.get('fans', [])
            sales_engineer = session.get('sales_engineer')
            
            logger.info(f"Export - enquiry: {enquiry_number}, fans count: {len(fans)}")
            if fans:
                logger.info(f"First fan data structure: {list(fans[0].keys()) if fans else 'No fans'}")
            
            if not enquiry_number or not fans:
                return jsonify({'error': 'No project data found. Please ensure you have calculated fan data before exporting.'}), 400

            # --- Enhanced structure with comprehensive details ---
            rows = []
            def section(title):
                return {'type': 'section', 'label': title}
            def field(label, key, is_numeric=False, total=True, format_type=None):
                return {'type': 'field', 'label': label, 'key': key, 'is_numeric': is_numeric, 'total': total, 'format_type': format_type}

            # Project Information
            rows.append(section('Project Information'))
            rows += [
                field('Enquiry Number', 'enquiry_number'),
                field('Customer Name', 'customer_name'),
                field('Sales Engineer', 'sales_engineer'),
                field('Total Fans', 'total_fans'),
            ]

            # Fan Specifications
            rows.append(section('Fan Specifications'))
            rows += [
                field('Fan Number', 'fan_number'),
                field('Fan Model', 'fan_model'),
                field('Fan Size', 'fan_size'),
                field('Class', 'class_'),
                field('Arrangement', 'arrangement'),
                field('Material of Construction', 'material'),
                field('Vendor', 'vendor'),
                field('Shaft Diameter (mm)', 'shaft_diameter', is_numeric=True),
                field('No. of Isolators', 'no_of_isolators', is_numeric=True),
                field('Vibration Isolators', 'vibration_isolators'),
                field('Bearing Brand', 'bearing_brand'),
            ]

            # Motor Details
            rows.append(section('Motor Details'))
            rows += [
                field('Motor Brand', 'motor_brand'),
                field('Motor kW', 'motor_kw', is_numeric=True),
                field('Motor Pole', 'pole', is_numeric=True),
                field('Motor Efficiency', 'efficiency'),
                field('Motor Discount (%)', 'motor_discount', is_numeric=True, format_type='percentage'),
                field('Drive Pack kW', 'drive_pack_kw', is_numeric=True),
            ]

            # Weights Breakdown
            rows.append(section('Weights Breakdown'))
            rows += [
                field('Bare Fan Weight (kg)', 'bare_fan_weight', is_numeric=True, format_type='weight'),
                field('Accessory Weight (kg)', 'accessory_weights', is_numeric=True, format_type='weight'),
                field('Total Weight (kg)', 'total_weight', is_numeric=True, format_type='weight'),
                field('Fabrication Weight (kg)', 'fabrication_weight', is_numeric=True, format_type='weight'),
                field('Bought Out Weight (kg)', 'bought_out_weight', is_numeric=True, format_type='weight'),
            ]

            # Detailed Cost Breakdown
            rows.append(section('Detailed Cost Breakdown'))
            rows += [
                field('Fabrication Cost (₹)', 'fabrication_cost', is_numeric=True, format_type='currency'),
                field('Fabrication Margin (%)', 'fabrication_margin', is_numeric=True, total=False, format_type='percentage'),
                field('Fabrication Selling Price (₹)', 'fabrication_selling_price', is_numeric=True, format_type='currency'),
                field('Motor Cost (₹)', 'motor_cost', is_numeric=True, format_type='currency'),
                field('Vibration Isolators Cost (₹)', 'vibration_isolators_cost', is_numeric=True, format_type='currency'),
                field('Drive Pack Cost (₹)', 'drive_pack_cost', is_numeric=True, format_type='currency'),
                field('Bearing Cost (₹)', 'bearing_cost', is_numeric=True, format_type='currency'),
                field('Optional Items Cost (₹)', 'optional_items_cost', is_numeric=True, format_type='currency'),
                field('Flex Connectors Cost (₹)', 'flex_connectors_cost', is_numeric=True, format_type='currency'),
                field('Total Bought Out Cost (₹)', 'bought_out_cost', is_numeric=True, format_type='currency'),
                field('Bought Out Margin (%)', 'bought_out_margin', is_numeric=True, total=False, format_type='percentage'),
                field('Bought Out Selling Price (₹)', 'bought_out_selling_price', is_numeric=True, format_type='currency'),
                field('Total Cost (₹)', 'total_cost', is_numeric=True, format_type='currency'),
                field('Total Selling Price (₹)', 'total_selling_price', is_numeric=True, format_type='currency'),
                field('Total Job Margin (%)', 'total_job_margin', is_numeric=True, total=False, format_type='percentage'),
            ]

            # Standard Accessories (show Included/Not Included)
            rows.append(section('Standard Accessories'))
            standard_accessories = [
                'unitary_base_frame', 'isolation_base_frame', 'split_casing',
                'inlet_companion_flange', 'outlet_companion_flange', 'inlet_butterfly_damper'
            ]
            
            # Collect all accessory keys from all fans
            all_accessories = set(standard_accessories)
            for fan in fans:
                accs = fan.get('accessories', {})
                if isinstance(accs, dict):
                    for k in accs.keys():
                        all_accessories.add(k)
            
            for acc in sorted(all_accessories):
                label = acc.replace('_', ' ').title()
                rows.append(field(label, f'accessories.{acc}', is_numeric=False, total=False))

            # Custom Accessories (show name and weight)
            rows.append(section('Custom Accessories'))
            all_custom_accessories = set()
            for fan in fans:
                custom_accs = fan.get('custom_accessories', {})
                if isinstance(custom_accs, dict):
                    for k in custom_accs.keys():
                        all_custom_accessories.add(k)
                elif isinstance(custom_accs, str) and custom_accs:
                    # Handle case where custom_accessories is a string (accessory name)
                    all_custom_accessories.add(custom_accs)
                
                # Also check customAccessories field
                custom_accs_alt = fan.get('customAccessories', {})
                if isinstance(custom_accs_alt, dict):
                    for k in custom_accs_alt.keys():
                        all_custom_accessories.add(k)
            
            for custom_acc in sorted(all_custom_accessories):
                rows.append(field(f'{custom_acc} (kg)', f'custom_accessories.{custom_acc}', is_numeric=True, format_type='weight'))

            # Standard Optional Items (show cost or blank)
            rows.append(section('Standard Optional Items'))
            standard_optional_items = [
                'flex_connectors', 'silencer', 'testing_charges', 'freight_charges', 
                'warranty_charges', 'packing_charges', 'vibration_sensors', 'temperature_sensors'
            ]
            
            # Collect all optional item keys from all fans with enhanced extraction
            all_optional_items = set(standard_optional_items)
            for fan in fans:
                # First check regular optional_items
                opts = fan.get('optional_items', {})
                if isinstance(opts, dict):
                    for k in opts.keys():
                        all_optional_items.add(k)
                
                # Also check for standard_optional_items[] format
                std_opt_item = fan.get('standard_optional_items[]', '')
                if std_opt_item:
                    all_optional_items.add(std_opt_item)
            
            for opt in sorted(all_optional_items):
                label = opt.replace('_', ' ').title()
                rows.append(field(f'{label} (₹)', f'optional_items.{opt}', is_numeric=True, format_type='currency'))

            # Custom Optional Items (show cost)
            rows.append(section('Custom Optional Items'))
            all_custom_optional_items = set()
            for fan in fans:
                custom_opts = fan.get('custom_option_items', {})
                for k in custom_opts.keys():
                    all_custom_optional_items.add(k)
            
            for custom_opt in sorted(all_custom_optional_items):
                rows.append(field(f'{custom_opt} (₹)', f'custom_option_items.{custom_opt}', is_numeric=True, format_type='currency'))

            # Custom Materials (for fans with material='others')
            rows.append(section('Custom Materials'))
            has_custom_materials = any(fan.get('material') == 'others' for fan in fans)
            if has_custom_materials:
                for i in range(5):
                    rows.append(field(f'Material {i+1} Name', f'material_name_{i}', is_numeric=False, total=False))
                    rows.append(field(f'Material {i+1} Weight (kg)', f'material_weight_{i}', is_numeric=True, format_type='weight'))
                    rows.append(field(f'Material {i+1} Rate (₹/kg)', f'material_rate_{i}', is_numeric=True, format_type='currency'))
            # --- End of enhanced structure ---

            # Build columns for each fan with comprehensive data
            fan_columns = []
            for i, fan in enumerate(fans):
                col = {}
                
                # Helper function to safely get values with enhanced mapping
                def safe_get(fan_data, *keys, default=''):
                    # Try direct key access first
                    for key_path in keys:
                        if isinstance(key_path, str):
                            if key_path in fan_data:
                                value = fan_data[key_path]
                                # Handle empty strings as defaults for certain fields
                                if key_path in ['motor_brand', 'motor_kw', 'pole', 'efficiency'] and value == '':
                                    continue
                                return value
                        elif isinstance(key_path, (list, tuple)):
                            temp = fan_data
                            try:
                                for k in key_path:
                                    temp = temp[k]
                                return temp
                            except (KeyError, TypeError):
                                continue
                    
                    # Special handling for specific field mappings
                    field_mappings = {
                        'fan_model': ['Fan_Model', 'model'],
                        'fan_size': ['Fan_Size', 'size'],
                        'class_': ['Class', 'class'],
                        'arrangement': ['Arrangement'],
                        'motor_kw': ['motor_power'],
                        'pole': ['poles'],
                        'drive_pack_kw': ['drive_pack', 'drive_pack_kw']
                    }
                    
                    # Check if this is a field that needs special mapping
                    for key_path in keys:
                        if isinstance(key_path, str) and key_path in field_mappings:
                            for alt_key in field_mappings[key_path]:
                                if alt_key in fan_data:
                                    value = fan_data[alt_key]
                                    if value != '':  # Don't return empty strings
                                        return value
                    
                    return default
                
                # Project info (same for all fans)
                col['enquiry_number'] = enquiry_number
                col['customer_name'] = customer_name
                col['sales_engineer'] = sales_engineer
                col['total_fans'] = total_fans
                
                # Basic fan data
                col['fan_number'] = i + 1
                all_fields = [
                    'fan_model', 'fan_size', 'class_', 'arrangement', 'material', 'vendor',
                    'shaft_diameter', 'no_of_isolators', 'vibration_isolators', 'bearing_brand',
                    'motor_brand', 'motor_kw', 'pole', 'efficiency', 'motor_discount', 'drive_pack_kw',
                    'bare_fan_weight', 'accessory_weights', 'total_weight', 'fabrication_weight', 'bought_out_weight',
                    'fabrication_cost', 'fabrication_margin', 'fabrication_selling_price',
                    'motor_cost', 'vibration_isolators_cost', 'drive_pack_cost', 'bearing_cost',
                    'optional_items_cost', 'flex_connectors_cost', 'bought_out_cost', 'bought_out_margin',
                    'bought_out_selling_price', 'total_cost', 'total_selling_price', 'total_job_margin'
                ]
                
                for field in all_fields:
                    col[field] = safe_get(fan, field, ['specifications', field], ['weights', field], ['costs', field], ['motor', field.replace('motor_', '')])
                
                # Additional field mappings for specific cases
                if not col.get('drive_pack_kw'):
                    col['drive_pack_kw'] = safe_get(fan, 'drive_pack', 'drive_pack_kw', default='')
                
                # Handle motor data based on arrangement and whether motor fields are filled
                arrangement = col.get('arrangement', '')
                motor_brand = col.get('motor_brand', '')
                
                print(f"[DEBUG] Fan {i}: arrangement = '{arrangement}', motor_brand = '{motor_brand}'")
                print(f"[DEBUG] Fan {i}: motor_kw = '{col.get('motor_kw', '')}'")
                print(f"[DEBUG] Fan {i}: pole = '{col.get('pole', '')}'")
                print(f"[DEBUG] Fan {i}: efficiency = '{col.get('efficiency', '')}'")
                
                if arrangement == '4':  # Direct drive - no motor
                    col['motor_brand'] = 'Not Required (Direct Drive)'
                    col['motor_kw'] = 'N/A'
                    col['pole'] = 'N/A'
                    col['efficiency'] = 'N/A'
                    print(f"[DEBUG] Fan {i}: Set motor to Direct Drive mode")
                elif not motor_brand or motor_brand == '':  # Motor fields not filled
                    col['motor_brand'] = 'To Be Selected'
                    col['motor_kw'] = 'TBD'
                    col['pole'] = 'TBD'
                    col['efficiency'] = 'TBD'
                    print(f"[DEBUG] Fan {i}: Set motor to 'To Be Selected' mode")
                else:
                    print(f"[DEBUG] Fan {i}: Using actual motor data")
                
                # Standard Accessories (show 'Included' if true)
                accs = safe_get(fan, 'accessories', default={})
                if not isinstance(accs, dict):
                    accs = {}
                
                print(f"[DEBUG] Fan {i}: Raw accessories data = {accs}")
                accessories_processed = 0
                for acc in all_accessories:
                    is_included = accs.get(acc)
                    col[f'accessories.{acc}'] = 'Included' if is_included else ''
                    if is_included:
                        accessories_processed += 1
                        print(f"[DEBUG] Fan {i}: Accessory '{acc}' = Included")
                
                print(f"[DEBUG] Fan {i}: Total accessories processed = {accessories_processed}")
                
                # Custom Accessories (show weight) - Enhanced extraction
                custom_accs = safe_get(fan, 'custom_accessories', default={})
                if not isinstance(custom_accs, dict):
                    # Handle case where custom_accessories is a string (accessory name)
                    if isinstance(custom_accs, str) and custom_accs:
                        # Create dict with the accessory name and try to get weight from accessories
                        weight = safe_get(fan, 'accessories', {}).get(custom_accs, True)
                        custom_accs = {custom_accs: weight}
                    else:
                        custom_accs = {}
                
                # Also check customAccessories field
                custom_accs_alt = safe_get(fan, 'customAccessories', default={})
                if isinstance(custom_accs_alt, dict):
                    custom_accs.update(custom_accs_alt)
                
                for custom_acc in all_custom_accessories:
                    weight = custom_accs.get(custom_acc, '')
                    col[f'custom_accessories.{custom_acc}'] = weight if weight else ''
                
                # Standard Optional Items (show cost) - Enhanced extraction
                opts = safe_get(fan, 'optional_items', default={})
                if not isinstance(opts, dict):
                    opts = {}
                
                # CRITICAL FIX: Handle standard_optional_items[] format correctly
                std_opt_item = safe_get(fan, 'standard_optional_items[]', default='')
                print(f"[DEBUG] Fan {i}: std_opt_item = '{std_opt_item}'")
                print(f"[DEBUG] Fan {i}: optional_items = {opts}")
                
                if std_opt_item and std_opt_item not in opts:
                    # If we have a standard optional item but no cost, try to get it from optional_items_cost
                    item_cost = safe_get(fan, 'optional_items_cost', default=0)
                    print(f"[DEBUG] Fan {i}: item_cost from optional_items_cost = {item_cost}")
                    
                    if item_cost > 0:
                        opts[std_opt_item] = item_cost
                        print(f"[DEBUG] Fan {i}: Using actual cost {item_cost} for {std_opt_item}")
                    else:
                        # Default costs for specific optional items if not specified
                        default_costs = {
                            'testing_charges': 2000,
                            'silencer': 5000,
                            'flex_connectors': 3000,
                            'freight_charges': 1000,
                            'warranty_charges': 1500,
                            'packing_charges': 500,
                            'vibration_sensors': 4000,
                            'temperature_sensors': 3500
                        }
                        opts[std_opt_item] = default_costs.get(std_opt_item, 'Included')
                        print(f"[DEBUG] Fan {i}: Using default cost {default_costs.get(std_opt_item, 'Included')} for {std_opt_item}")
                
                # Additional fix: Check if optional_items is empty but we have optional_items_cost > 0
                if not opts and safe_get(fan, 'optional_items_cost', default=0) > 0:
                    # If there's a cost but no items, check for any standard item reference
                    if std_opt_item:
                        opts[std_opt_item] = safe_get(fan, 'optional_items_cost', default=0)
                        print(f"[DEBUG] Fan {i}: Recovered optional item {std_opt_item} from orphaned cost")
                
                print(f"[DEBUG] Fan {i}: Final optional_items = {opts}")
                
                for opt in all_optional_items:
                    cost = opts.get(opt, '')
                    col[f'optional_items.{opt}'] = cost if cost else ''
                
                # Custom Optional Items (show cost)
                custom_opts = safe_get(fan, 'custom_option_items', default={})
                if not isinstance(custom_opts, dict):
                    custom_opts = {}
                for custom_opt in all_custom_optional_items:
                    cost = custom_opts.get(custom_opt, '')
                    col[f'custom_option_items.{custom_opt}'] = cost if cost else ''
                
                # Custom Materials (if applicable)
                if has_custom_materials:
                    for j in range(5):
                        col[f'material_name_{j}'] = safe_get(fan, f'material_name_{j}', ['specifications', f'material_name_{j}'])
                        col[f'material_weight_{j}'] = safe_get(fan, f'material_weight_{j}', ['specifications', f'material_weight_{j}'])
                        col[f'material_rate_{j}'] = safe_get(fan, f'material_rate_{j}', ['specifications', f'material_rate_{j}'])
                
                fan_columns.append(col)

            # Build Excel rows
            excel_rows = []
            header = ['Field'] + [f"Fan {i+1}" for i in range(len(fan_columns))]
            excel_rows.append(header)
            for row in rows:
                if row['type'] == 'section':
                    excel_rows.append([row['label']] + ['']*len(fan_columns))
                else:
                    vals = [row['label']]
                    for col in fan_columns:
                        v = col.get(row['key'], '')
                        vals.append(v)
                    excel_rows.append(vals)
            # Totals row (only for numeric fields with total=True)
            totals_row = ['TOTALS']
            for i in range(len(fan_columns)):
                total = 0
                for idx, row in enumerate(rows):
                    if row['type'] == 'field' and row.get('is_numeric') and row.get('total', True):
                        v = fan_columns[i].get(row['key'])
                        try:
                            v = float(v) if v not in ['', None] else 0
                        except (TypeError, ValueError):
                            v = 0
                        total += v
                totals_row.append(total if total != 0 else '')
            excel_rows.append(totals_row)

            # Create Excel file
            filename = f"{enquiry_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "Project Summary"
            # Add project details
            ws['A1'] = 'Project Summary'
            ws['A1'].font = Font(bold=True, size=16)
            ws.merge_cells('A1:H1')
            ws['A3'] = 'Enquiry Number:'
            ws['B3'] = enquiry_number
            ws['A4'] = 'Customer Name:'
            ws['B4'] = customer_name
            ws['A5'] = 'Sales Engineer:'
            ws['B5'] = sales_engineer
            ws['A6'] = 'Date:'
            ws['B6'] = datetime.now().strftime('%d-%m-%Y')
            ws['D3'] = 'Total Fans:'
            ws['E3'] = total_fans
            # Write rows to Excel
            start_row = 8
            for r, row in enumerate(excel_rows):
                for c, value in enumerate(row):
                    cell = ws.cell(row=start_row + r, column=1 + c)
                    cell.value = value
                    # Section header formatting
                    if r > 0 and rows[r-1]['type'] == 'section' and c == 0:
                        cell.font = Font(bold=True, color='FFFFFF')
                        cell.fill = PatternFill(start_color='4a90e2', end_color='4a90e2', fill_type='solid')
                        cell.alignment = Alignment(horizontal='center')
                    # Header formatting
                    if r == 0:
                        cell.font = Font(bold=True, color='FFFFFF')
                        cell.fill = PatternFill(start_color='2c3e50', end_color='2c3e50', fill_type='solid')
                        cell.alignment = Alignment(horizontal='center')
                    # Totals formatting
                    if r == len(excel_rows) - 1:
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill(start_color='e8f4fd', end_color='e8f4fd', fill_type='solid')
                    
                    # Enhanced number formatting based on format_type
                    if isinstance(value, (int, float)) and value != 0:
                        if r > 0 and r < len(rows) + 1:  # Skip header and totals
                            row_def = rows[r-1]
                            format_type = row_def.get('format_type', None)
                            
                            if format_type == 'currency':
                                cell.number_format = '₹#,##0.00'
                            elif format_type == 'weight':
                                cell.number_format = '#,##0.00" kg"'
                            elif format_type == 'percentage':
                                cell.number_format = '#,##0.00"%"'
                            else:
                                # Legacy formatting for backward compatibility
                                if any(keyword in row[0] for keyword in ['Cost', 'Price', '₹']):
                                    cell.number_format = '₹#,##0.00'
                                elif any(keyword in row[0] for keyword in ['Weight', 'kg']):
                                    cell.number_format = '#,##0.00" kg"'
                                elif any(keyword in row[0] for keyword in ['Margin', '%']):
                                    cell.number_format = '#,##0.00"%"'
                                else:
                                    cell.number_format = '#,##0.00'
                    
                    # Add borders for better readability
                    thin_border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )
                    cell.border = thin_border
            
            # Auto-fit columns with better width management
            for column_cells in ws.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter
                for cell in column_cells:
                    try:
                        cell_value_length = len(str(cell.value)) if cell.value is not None else 0
                        if cell_value_length > max_length:
                            max_length = cell_value_length
                    except:
                        pass
                # Set reasonable column widths
                if max_length < 10:
                    adjusted_width = 12
                elif max_length > 60:
                    adjusted_width = 60
                else:
                    adjusted_width = max_length + 4
                ws.column_dimensions[column_letter].width = adjusted_width
                
            # Freeze panes for better navigation
            ws.freeze_panes = 'B9'  # Freeze first column and header rows
            
            wb.save(filename)
            return send_file(
                filename,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            logger.error(f"Error exporting project summary to Excel: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/export_project_summary_excel', methods=['POST'])
    @login_required
    def export_project_summary_excel():
        """Export the project summary table sent from fixes.js to Excel with proper formatting."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            table = data.get('table', [])
            enquiry_number = data.get('enquiry_number', 'PROJECT')
            customer_name = data.get('customer_name', 'Customer')
            sales_engineer = data.get('sales_engineer', 'Sales Engineer')
            
            print(f"[DEBUG] Received table data: {len(table)} rows")
            print(f"[DEBUG] First few rows: {table[:3] if table else 'No data'}")
            
            if not table:
                return jsonify({'error': 'No table data provided'}), 400

            # Create Excel file
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from datetime import datetime
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Project Summary"
            
            # Add project header
            ws['A1'] = 'Project Summary'
            ws['A1'].font = Font(bold=True, size=16)
            ws.merge_cells('A1:H1')
            
            ws['A3'] = 'Enquiry Number:'
            ws['B3'] = enquiry_number
            ws['A4'] = 'Customer Name:'
            ws['B4'] = customer_name
            ws['A5'] = 'Sales Engineer:'
            ws['B5'] = sales_engineer
            ws['A6'] = 'Date:'
            ws['B6'] = datetime.now().strftime('%d-%m-%Y')
            
            # Write table data starting from row 8
            start_row = 8
            
            for r, row_data in enumerate(table):
                for c, cell_value in enumerate(row_data):
                    cell = ws.cell(row=start_row + r, column=1 + c)
                    cell.value = cell_value
                    
                    # Format header row
                    if r == 0:
                        cell.font = Font(bold=True, color='FFFFFF')
                        cell.fill = PatternFill(start_color='2c3e50', end_color='2c3e50', fill_type='solid')
                        cell.alignment = Alignment(horizontal='center')
                    
                    # Format section headers (rows with only first column filled)
                    elif c == 0 and cell_value and all(not cell for cell in row_data[1:]):
                        cell.font = Font(bold=True, color='FFFFFF')
                        cell.fill = PatternFill(start_color='4a90e2', end_color='4a90e2', fill_type='solid')
                        cell.alignment = Alignment(horizontal='center')
                    
                    # Format currency values
                    elif isinstance(cell_value, str) and cell_value.startswith('₹'):
                        try:
                            # Extract numeric value and format as currency
                            numeric_value = float(cell_value.replace('₹', '').replace(',', ''))
                            cell.value = numeric_value
                            cell.number_format = '₹#,##0.00'
                        except ValueError:
                            pass  # Keep as text if can't convert
                    
                    # Add borders
                    thin_border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )
                    cell.border = thin_border
            
            # Auto-fit columns
            for column_cells in ws.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter
                for cell in column_cells:
                    try:
                        cell_value_length = len(str(cell.value)) if cell.value is not None else 0
                        if cell_value_length > max_length:
                            max_length = cell_value_length
                    except:
                        pass
                # Set reasonable column widths
                if max_length < 10:
                    adjusted_width = 12
                elif max_length > 60:
                    adjusted_width = 60
                else:
                    adjusted_width = max_length + 4
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Freeze panes
            ws.freeze_panes = 'B9'
            
            # Save to memory
            from io import BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            filename = f"{enquiry_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        except Exception as e:
            logger.error(f"Error exporting project summary from fixes.js: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/load_enquiry/<enquiry_number>')
    @login_required
    def load_enquiry(enquiry_number):
        """Load a specific enquiry and all its fan data."""
        try:
            logger.info(f"Loading enquiry: {enquiry_number}")
            
            # Try to load from central database first (most up-to-date)
            central_db_path = 'data/central_database/all_projects.db'
            project_data = None
            fans_data = []
            
            if os.path.exists(central_db_path):
                try:
                    conn = sqlite3.connect(central_db_path)
                    cursor = conn.cursor()
                    
                    # Get project info
                    cursor.execute('''
                        SELECT enquiry_number, customer_name, total_fans, sales_engineer
                        FROM Projects 
                        WHERE enquiry_number = ?
                    ''', (enquiry_number,))
                    
                    project_result = cursor.fetchone()
                    if project_result:
                        project_data = {
                            'enquiry_number': project_result[0],
                            'customer_name': project_result[1],
                            'total_fans': project_result[2],
                            'sales_engineer': project_result[3]
                        }
                        
                        # Get all fans for this enquiry
                        cursor.execute('''
                            SELECT * FROM ProjectFans 
                            WHERE enquiry_number = ?
                            ORDER BY fan_number
                        ''', (enquiry_number,))
                        
                        fan_columns = [description[0] for description in cursor.description]
                        fan_results = cursor.fetchall()
                        
                        for fan_row in fan_results:
                            fan_dict = dict(zip(fan_columns, fan_row))
                            
                            # Process JSON fields
                            json_fields = ['accessories', 'custom_accessories', 'optional_items', 'custom_option_items']
                            for json_field in json_fields:
                                if json_field in fan_dict and fan_dict[json_field]:
                                    try:
                                        parsed_json = json.loads(fan_dict[json_field])
                                        fan_dict[json_field] = parsed_json
                                    except (json.JSONDecodeError, TypeError):
                                        logger.warning(f"Could not parse {json_field} JSON: {fan_dict[json_field]}")
                                        fan_dict[json_field] = {}
                            
                            # Also try JSON versions of optional items
                            if 'optional_items_json' in fan_dict and fan_dict['optional_items_json']:
                                try:
                                    parsed_json = json.loads(fan_dict['optional_items_json'])
                                    fan_dict['optional_items'] = parsed_json
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            
                            if 'custom_optional_items_json' in fan_dict and fan_dict['custom_optional_items_json']:
                                try:
                                    parsed_json = json.loads(fan_dict['custom_optional_items_json'])
                                    fan_dict['custom_option_items'] = parsed_json
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            
                            fans_data.append(fan_dict)
                    
                    conn.close()
                    logger.info(f"Loaded enquiry {enquiry_number} from central database")
                    
                except Exception as e:
                    logger.warning(f"Could not load from central database: {str(e)}")
            
            # If not found in central database, try local database
            if not project_data:
                try:
                    conn = sqlite3.connect('fan_pricing.db')
                    cursor = conn.cursor()
                    
                    # Get project info
                    cursor.execute('''
                        SELECT enquiry_number, customer_name, total_fans, sales_engineer
                        FROM Projects 
                        WHERE enquiry_number = ?
                    ''', (enquiry_number,))
                    
                    project_result = cursor.fetchone()
                    if project_result:
                        project_data = {
                            'enquiry_number': project_result[0],
                            'customer_name': project_result[1],
                            'total_fans': project_result[2],
                            'sales_engineer': project_result[3]
                        }
                        
                        # Get all fans for this enquiry
                        cursor.execute('''
                            SELECT * FROM ProjectFans 
                            WHERE enquiry_number = ?
                            ORDER BY fan_number
                        ''', (enquiry_number,))
                        
                        fan_columns = [description[0] for description in cursor.description]
                        fan_results = cursor.fetchall()
                        
                        for fan_row in fan_results:
                            fan_dict = dict(zip(fan_columns, fan_row))
                            
                            # Process JSON fields
                            json_fields = ['accessories', 'custom_accessories', 'optional_items', 'custom_option_items']
                            for json_field in json_fields:
                                if json_field in fan_dict and fan_dict[json_field]:
                                    try:
                                        parsed_json = json.loads(fan_dict[json_field])
                                        fan_dict[json_field] = parsed_json
                                    except (json.JSONDecodeError, TypeError):
                                        logger.warning(f"Could not parse {json_field} JSON: {fan_dict[json_field]}")
                                        fan_dict[json_field] = {}
                            
                            # Also try JSON versions of optional items
                            if 'optional_items_json' in fan_dict and fan_dict['optional_items_json']:
                                try:
                                    parsed_json = json.loads(fan_dict['optional_items_json'])
                                    fan_dict['optional_items'] = parsed_json
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            
                            if 'custom_optional_items_json' in fan_dict and fan_dict['custom_optional_items_json']:
                                try:
                                    parsed_json = json.loads(fan_dict['custom_optional_items_json'])
                                    fan_dict['custom_option_items'] = parsed_json
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            
                            fans_data.append(fan_dict)
                    
                    conn.close()
                    logger.info(f"Loaded enquiry {enquiry_number} from local database")
                    
                except Exception as e:
                    logger.warning(f"Could not load from local database: {str(e)}")
            
            if not project_data:
                return jsonify({
                    'success': False,
                    'message': f'Enquiry {enquiry_number} not found'
                }), 404
            
            logger.info(f"Successfully loaded enquiry {enquiry_number} with {len(fans_data)} fans")
            return jsonify({
                'success': True,
                'project': project_data,
                'fans': fans_data
            })
            
        except Exception as e:
            logger.error(f"Error loading enquiry {enquiry_number}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/save_project_to_database/', methods=['POST'])
    @login_required
    def save_project_to_database():
        """Save complete project data to database."""
        try:
            data = request.get_json()
            logger.info(f"Received project data for saving: {data}")
            
            # Extract project information
            enquiry_number = data.get('enquiry_number')
            customer_name = data.get('customer_name')
            total_fans = data.get('total_fans', 1)
            sales_engineer = data.get('sales_engineer', session.get('full_name', ''))
            fans_data = data.get('fans_data', [])
            
            # Also try 'fans' key as that's what the frontend sends
            if not fans_data:
                fans_data = data.get('fans', [])
            
            if not enquiry_number:
                return jsonify({
                    'success': False,
                    'message': 'Enquiry number is required'
                }), 400
            
            if not fans_data:
                return jsonify({
                    'success': False,
                    'message': 'At least one fan is required'
                }), 400
            
            logger.info(f"Saving project: {enquiry_number} with {len(fans_data)} fans")
            
            # Save to local database first
            try:
                conn = sqlite3.connect('fan_pricing.db')
                cursor = conn.cursor()
                
                # Create Projects table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        enquiry_number TEXT UNIQUE,
                        customer_name TEXT,
                        total_fans INTEGER,
                        sales_engineer TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert or update project
                cursor.execute('''
                    INSERT OR REPLACE INTO Projects (enquiry_number, customer_name, total_fans, sales_engineer)
                    VALUES (?, ?, ?, ?)
                ''', (enquiry_number, customer_name, total_fans, sales_engineer))
                
                # Get the project ID
                cursor.execute('SELECT id FROM Projects WHERE enquiry_number = ?', (enquiry_number,))
                project_result = cursor.fetchone()
                if not project_result:
                    raise Exception("Failed to get project ID after insertion")
                project_id = project_result[0]
                
                # Delete existing fan records for this enquiry
                cursor.execute('DELETE FROM ProjectFans WHERE enquiry_number = ?', (enquiry_number,))
                
                # Process each fan
                for fan_number, fan_data in enumerate(fans_data, 1):
                    # Extract optional items from multiple possible sources
                    optional_items = {}
                    
                    # First check if optional_items is directly in fan_data
                    direct_optional = fan_data.get('optional_items', {})
                    if isinstance(direct_optional, dict):
                        optional_items.update(direct_optional)
                    elif isinstance(direct_optional, list):
                        # Convert list to dict with default prices
                        for item in direct_optional:
                            optional_items[item] = 0
                    
                    # Check if optional_items is nested in specifications
                    specs_optional = fan_data.get('specifications', {}).get('optional_items', {})
                    if isinstance(specs_optional, dict):
                        optional_items.update(specs_optional)
                    elif isinstance(specs_optional, list):
                        # Convert list to dict with default prices
                        for item in specs_optional:
                            optional_items[item] = 0
                    
                    # Handle standard_optional_items[] format from frontend
                    standard_items = fan_data.get('standard_optional_items[]', [])
                    if isinstance(standard_items, str):
                        standard_items = [standard_items]
                    elif not isinstance(standard_items, list):
                        standard_items = []
                    
                    # Add standard optional items to the optional_items dict
                    for item in standard_items:
                        if item and item not in optional_items:
                            # Set a default value or get from optional_item_prices if available
                            item_price = fan_data.get('optional_item_prices', {}).get(item, 0)
                            if not item_price:
                                # Try to get cost from the fan data directly
                                if item == 'flex_connectors' and fan_data.get('flex_connectors_cost'):
                                    item_price = fan_data.get('flex_connectors_cost', 0)
                                else:
                                    item_price = 0
                            optional_items[item] = item_price
                    
                    # Also check costs section for optional items cost
                    costs_optional_cost = fan_data.get('costs', {}).get('optional_items_cost', 0)
                    if costs_optional_cost and not optional_items:
                        # If we have cost but no items, try to extract from other sources
                        if fan_data.get('flex_connectors_cost'):
                            optional_items['flex_connectors'] = fan_data.get('flex_connectors_cost', 0)
                    
                    # Helper function to safely get nested values
                    def get_nested_value(data, *keys, default=''):
                        """Get nested value from dict, trying multiple key paths"""
                        for key_path in keys:
                            if isinstance(key_path, str):
                                if key_path in data:
                                    return data[key_path]
                            elif isinstance(key_path, (list, tuple)):
                                temp = data
                                try:
                                    for k in key_path:
                                        temp = temp[k]
                                    return temp
                                except (KeyError, TypeError):
                                    continue
                        return default
                    
                    # Extract custom optional items from multiple sources
                    custom_option_items = {}
                    custom_direct = fan_data.get('custom_option_items', {})
                    if isinstance(custom_direct, dict):
                        custom_option_items.update(custom_direct)
                    
                    custom_specs = fan_data.get('specifications', {}).get('custom_option_items', {})
                    if isinstance(custom_specs, dict):
                        custom_option_items.update(custom_specs)
                    
                    # Extract accessories from multiple sources
                    accessories = {}
                    acc_direct = fan_data.get('accessories', {})
                    if isinstance(acc_direct, dict):
                        accessories.update(acc_direct)
                    elif isinstance(acc_direct, list):
                        # Convert list to dict
                        for acc in acc_direct:
                            accessories[acc] = True
                            
                    acc_specs = fan_data.get('specifications', {}).get('accessories', {})
                    if isinstance(acc_specs, dict):
                        accessories.update(acc_specs)
                    elif isinstance(acc_specs, list):
                        # Convert list to dict
                        for acc in acc_specs:
                            accessories[acc] = True
                    
                    # Extract custom accessories
                    custom_accessories = {}
                    custom_acc_direct = fan_data.get('custom_accessories', {})
                    if isinstance(custom_acc_direct, dict):
                        custom_accessories.update(custom_acc_direct)
                    elif isinstance(custom_acc_direct, list):
                        # Convert list to dict with default weights
                        for acc in custom_acc_direct:
                            custom_accessories[acc] = 0
                            
                    custom_acc_specs = fan_data.get('specifications', {}).get('custom_accessories', {})
                    if isinstance(custom_acc_specs, dict):
                        custom_accessories.update(custom_acc_specs)
                    elif isinstance(custom_acc_specs, list):
                        # Convert list to dict with default weights
                        for acc in custom_acc_specs:
                            custom_accessories[acc] = 0
                    
                    # Prepare fan data for database insertion
                    fan_db_data = {
                        'project_id': project_id,
                        'enquiry_number': enquiry_number,
                        'fan_number': fan_number,
                        'fan_model': get_nested_value(fan_data, 'fan_model', ['specifications', 'fan_model']),
                        'fan_size': get_nested_value(fan_data, 'fan_size', ['specifications', 'size'], ['specifications', 'fan_size']),
                        'size': get_nested_value(fan_data, 'fan_size', ['specifications', 'size'], ['specifications', 'fan_size']),
                        'class': get_nested_value(fan_data, 'class_', 'class', ['specifications', 'class']),
                        'arrangement': get_nested_value(fan_data, 'arrangement', ['specifications', 'arrangement']),
                        'vendor': get_nested_value(fan_data, 'vendor', ['specifications', 'vendor']),
                        'material': get_nested_value(fan_data, 'material', 'moc', ['specifications', 'material']),
                        'accessories': json.dumps(accessories),
                        'custom_accessories': json.dumps(custom_accessories),
                        'optional_items': json.dumps(optional_items),
                        'custom_option_items': json.dumps(custom_option_items),
                        'optional_items_json': json.dumps(optional_items),
                        'custom_optional_items_json': json.dumps(custom_option_items),
                        'bare_fan_weight': get_nested_value(fan_data, 'bare_fan_weight', ['weights', 'bare_fan_weight'], default=0),
                        'accessory_weight': get_nested_value(fan_data, 'accessory_weights', 'accessory_weight', ['weights', 'accessory_weight'], default=0),
                        'accessory_weights': get_nested_value(fan_data, 'accessory_weights', 'accessory_weight', ['weights', 'accessory_weight'], default=0),
                        'total_weight': get_nested_value(fan_data, 'total_weight', ['weights', 'total_weight'], default=0),
                        'fabrication_weight': get_nested_value(fan_data, 'fabrication_weight', ['weights', 'fabrication_weight'], default=0),
                        'bought_out_weight': get_nested_value(fan_data, 'bought_out_weight', ['weights', 'bought_out_weight'], default=0),
                        'fabrication_cost': get_nested_value(fan_data, 'fabrication_cost', ['costs', 'fabrication_cost'], default=0),
                        'motor_cost': get_nested_value(fan_data, 'motor_cost', ['costs', 'motor_cost'], default=0),
                        'vibration_isolators_cost': get_nested_value(fan_data, 'vibration_isolators_cost', ['costs', 'vibration_isolators_cost'], default=0),
                        'drive_pack_cost': get_nested_value(fan_data, 'drive_pack_cost', ['costs', 'drive_pack_cost'], default=0),
                        'bearing_cost': get_nested_value(fan_data, 'bearing_cost', ['costs', 'bearing_cost'], default=0),
                        'optional_items_cost': get_nested_value(fan_data, 'optional_items_cost', ['costs', 'optional_items_cost'], default=0),
                        'flex_connectors_cost': get_nested_value(fan_data, 'flex_connectors_cost', ['costs', 'flex_connectors_cost'], default=0),
                        'bought_out_cost': get_nested_value(fan_data, 'bought_out_cost', ['costs', 'bought_out_cost'], default=0),
                        'total_cost': get_nested_value(fan_data, 'total_cost', ['costs', 'total_cost'], default=0),
                        'fabrication_selling_price': get_nested_value(fan_data, 'fabrication_selling_price', ['costs', 'fabrication_selling_price'], default=0),
                        'bought_out_selling_price': get_nested_value(fan_data, 'bought_out_selling_price', ['costs', 'bought_out_selling_price'], default=0),
                        'total_selling_price': get_nested_value(fan_data, 'total_selling_price', ['costs', 'total_selling_price'], default=0),
                        'total_job_margin': get_nested_value(fan_data, 'total_job_margin', ['costs', 'total_job_margin'], default=0),
                        'vibration_isolators': get_nested_value(fan_data, 'vibration_isolators', ['specifications', 'vibration_isolators']),
                        'drive_pack_kw': get_nested_value(fan_data, 'drive_pack_kw', ['specifications', 'drive_pack_kw'], default=0),
                        'motor_kw': get_nested_value(fan_data, 'motor_kw', ['motor', 'kw'], ['specifications', 'motor_kw'], default=0),
                        'motor_brand': get_nested_value(fan_data, 'motor_brand', ['motor', 'brand'], ['specifications', 'motor_brand']),
                        'motor_pole': get_nested_value(fan_data, 'pole', 'motor_pole', ['motor', 'pole'], ['specifications', 'motor_pole'], default=0),
                        'motor_efficiency': get_nested_value(fan_data, 'efficiency', 'motor_efficiency', ['motor', 'efficiency'], ['specifications', 'motor_efficiency']),
                        'motor_discount_rate': get_nested_value(fan_data, 'motor_discount', 'motor_discount_rate', ['motor', 'discount_rate'], ['specifications', 'motor_discount'], default=0),
                        'bearing_brand': get_nested_value(fan_data, 'bearing_brand', ['specifications', 'bearing_brand']),
                        'shaft_diameter': get_nested_value(fan_data, 'shaft_diameter', 'custom_shaft_diameter', ['specifications', 'shaft_diameter'], default=0),
                        'no_of_isolators': get_nested_value(fan_data, 'no_of_isolators', 'custom_no_of_isolators', ['specifications', 'no_of_isolators'], default=0),
                        'fabrication_margin': get_nested_value(fan_data, 'fabrication_margin', ['specifications', 'fabrication_margin'], default=25),
                        'bought_out_margin': get_nested_value(fan_data, 'bought_out_margin', ['specifications', 'bought_out_margin'], default=25),
                        'custom_no_of_isolators': get_nested_value(fan_data, 'custom_no_of_isolators', ['specifications', 'custom_no_of_isolators'], default=0),
                        'custom_shaft_diameter': get_nested_value(fan_data, 'custom_shaft_diameter', ['specifications', 'custom_shaft_diameter'], default=0),
                    }
                    
                    # Handle material data (for custom materials)
                    for i in range(5):
                        for key in ['material_name', 'material_weight', 'material_rate']:
                            field_key = f'{key}_{i}'
                            fan_db_data[field_key] = get_nested_value(fan_data, field_key, ['specifications', field_key], default='')
                    
                    # Insert fan data
                    columns = list(fan_db_data.keys())
                    placeholders = ', '.join(['?' for _ in columns])
                    values = list(fan_db_data.values())
                    
                    cursor.execute(f'''
                        INSERT INTO ProjectFans ({', '.join(columns)})
                        VALUES ({placeholders})
                    ''', values)
                
                conn.commit()
                conn.close()
                logger.info(f"Successfully saved project {enquiry_number} to local database")
                
            except Exception as e:
                logger.error(f"Error saving to local database: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'message': f'Failed to save to local database: {str(e)}'
                }), 500
            
            # Also sync to central database
            try:
                sync_project_data = {
                    'enquiry_number': enquiry_number,
                    'customer_name': customer_name,
                    'total_fans': total_fans,
                    'sales_engineer': sales_engineer,
                    'fans': fans_data
                }
                
                sync_success = sync_to_central_database(sync_project_data)
                if not sync_success:
                    logger.warning("Failed to sync to central database, but local save succeeded")
            
            except Exception as e:
                logger.warning(f"Failed to sync to central database: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': f'Project {enquiry_number} saved successfully',
                'enquiry_number': enquiry_number
            })
            
        except Exception as e:
            logger.error(f"Error saving project to database: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/get_vendor_rate')
    def get_vendor_rate():
        vendor = request.args.get('vendor')
        material = request.args.get('material', 'ms')
        try:
            total_weight = float(request.args.get('weight', 1))
        except Exception:
            total_weight = 1
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MSPrice, SS304Price FROM VendorWeightDetails
                WHERE Vendor = ? AND WeightStart <= ? AND WeightEnd > ?
            ''', (vendor, total_weight, total_weight))
            row = cursor.fetchone()
            if not row:
                return jsonify({'rate': None}), 404
            if material == 'ss304':
                return jsonify({'rate': row['SS304Price']})
            else:
                return jsonify({'rate': row['MSPrice']})

    return app 