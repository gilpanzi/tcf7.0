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

def register_routes(app):
    """Register all routes for the application."""
    
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

    @app.route('/api/sales_engineers')
    @login_required
    def api_sales_engineers():
        try:
            from database import get_sales_engineers
            limit = int(request.args.get('limit', 100))
            return jsonify({'sales_engineers': get_sales_engineers(limit)})
        except Exception as e:
            logger.error(f"Error getting sales engineers: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/enquiries')
    @login_required
    def api_saved_enquiries():
        try:
            from database import search_projects
            q = request.args.get('q', '')
            limit = int(request.args.get('limit', 100))
            projects = search_projects(q, limit)
            # Return minimal info for dropdown
            return jsonify({'enquiries': [
                {
                    'enquiry_number': p['enquiry_number'],
                    'customer_name': p['customer_name'],
                    'sales_engineer': p['sales_engineer'],
                    'total_fans': p['total_fans']
                } for p in projects
            ]})
        except Exception as e:
            logger.error(f"Error getting saved enquiries: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/load_enquiry/<enquiry_number>')
    @login_required
    def load_enquiry(enquiry_number):
        """Load a specific enquiry and all its fan data from unified database."""
        try:
            logger.info(f"Loading enquiry: {enquiry_number}")
            
            # Load from unified database using get_project function
            from database import get_project
            project = get_project(enquiry_number)
            
            if not project:
                logger.warning(f"Project not found: {enquiry_number}")
                return jsonify({
                    'success': False,
                    'message': f'No enquiry found with number {enquiry_number}'
                }), 404
            
            logger.info(f"Project loaded successfully: {enquiry_number}, fans: {len(project.get('fans', []))}")
            
            # Convert project data to the format expected by the frontend
            project_data = {
                'enquiry_number': project['enquiry_number'],
                'customer_name': project['customer_name'],
                'total_fans': project['total_fans'],
                'sales_engineer': project['sales_engineer']
            }
            
            # Convert fan data to the format expected by the frontend
            fans_data = []
            for fan in project.get('fans', []):
                fan_data = {
                    'fan_number': fan['fan_number'],
                    'status': fan['status'],
                    'specifications': fan['specifications'],
                    'weights': fan['weights'],
                    'costs': fan['costs'],
                    'motor': fan['motor']
                }
                fans_data.append(fan_data)
            
            logger.info(f"Successfully loaded project {enquiry_number} with {len(fans_data)} fans")
            
            return jsonify({
                'success': True,
                'project': project_data,
                'fans': fans_data
            })
            
        except Exception as e:
            logger.error(f"Error loading enquiry {enquiry_number}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'message': f'Error loading enquiry: {str(e)}'
            }), 500

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
                'fabrication_margin': float(data.get('fabrication_margin', 25) or 25),
                'bought_out_margin': float(data.get('bought_out_margin', 25) or 25),
                'motor_brand': data.get('motor_brand', ''),
                'motor_kw': data.get('motor_kw', ''),
                'pole': data.get('pole', ''),
                'efficiency': data.get('efficiency', ''),
                'motor_discount': float(data.get('motor_discount', 0) or 0),
                'drive_pack': data.get('drive_pack'),
                'customAccessories': data.get('customAccessories', {}),
                'optional_items': data.get('optional_items', {})
            }
            
            # Get selected accessories
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
                    if weight_key in data and data[weight_key] and str(data[weight_key]).strip():
                        fan_data[weight_key] = float(data[weight_key])
                    if name_key in data:
                        fan_data[name_key] = data[name_key]
                    if rate_key in data and data[rate_key] and str(data[rate_key]).strip():
                        fan_data[rate_key] = float(data[rate_key])
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
                
                if 'optional_items' in fan_data:
                    for item_name, item_price in fan_data['optional_items'].items():
                        if item_price and str(item_price).strip() and float(item_price) > 0:
                            optional_items_cost += float(item_price)
                            optional_items_detail[item_name] = float(item_price)
                
                bought_out_cost += optional_items_cost
                
                # Calculate total costs and margins (do not add optional_items_cost again)
                fabrication_selling_price = fabrication_cost / (1 - fan_data['fabrication_margin'] / 100)
                bought_out_selling_price = bought_out_cost / (1 - fan_data['bought_out_margin'] / 100)
                total_selling_price = fabrication_selling_price + bought_out_selling_price
                
                # Calculate total job margin on raw costs (fab + BO including optionals already in BO)
                total_raw_cost = fabrication_cost + bought_out_cost
                if total_raw_cost > 0:
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

    # New unified API endpoints
    @app.route('/api/projects', methods=['POST'])
    @login_required
    def api_create_project():
        """Create or update a project."""
        try:
            data = request.json
            enquiry_number = data.get('enquiry_number')
            customer_name = data.get('customer_name')
            total_fans = data.get('total_fans')
            sales_engineer = data.get('sales_engineer')
            
            if not all([enquiry_number, customer_name, total_fans, sales_engineer]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            if not isinstance(total_fans, int) or total_fans < 1:
                return jsonify({'error': 'total_fans must be a positive integer'}), 400
            
            from database import create_or_update_project
            project_id = create_or_update_project(enquiry_number, customer_name, total_fans, sales_engineer)

            return jsonify({'success': True, 'project_id': project_id, 'enquiry_number': enquiry_number})
                
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/projects', methods=['GET'])
    @login_required
    def api_search_projects():
        """Search projects."""
        try:
            query = request.args.get('q', '')
            limit = int(request.args.get('limit', 50))
            
            from database import search_projects
            projects = search_projects(query, limit)
            
            return jsonify({'projects': projects})
                
        except Exception as e:
            logger.error(f"Error searching projects: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/projects/<enquiry_number>', methods=['GET'])
    @login_required
    def api_get_project(enquiry_number):
        """Get project by enquiry number."""
        try:
            from database import get_project
            project = get_project(enquiry_number)
            
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            
            return jsonify(project)
                
        except Exception as e:
            logger.error(f"Error getting project: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/projects/<enquiry_number>/fans/<int:fan_number>', methods=['GET'])
    @login_required
    def api_get_fan(enquiry_number, fan_number):
        """Get a specific fan."""
        try:
            from database import get_fan
            fan = get_fan(enquiry_number, fan_number)
            
            if not fan:
                return jsonify({'error': 'Fan not found'}), 404
            
            return jsonify(fan)
            
        except Exception as e:
            logger.error(f"Error getting fan: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/projects/<enquiry_number>/fans/<int:fan_number>', methods=['PUT'])
    @login_required
    def api_save_fan(enquiry_number, fan_number):
        """Save fan data with calculations."""
        try:
            logger.info(f"Saving fan data for {enquiry_number}/fan {fan_number}")
            data = request.json
            if not data:
                logger.error("No JSON data received")
                return jsonify({'error': 'No data received'}), 400
            
            specifications = data.get('specifications', {})
            motor = data.get('motor', {})
            logger.info(f"Specifications: {specifications}")
            logger.info(f"Motor: {motor}")
            
            # Perform calculations
            with get_db_connection() as conn:
                cursor = conn.cursor()
            
                # Convert specifications to fan_data format for calculations
                fan_data = {
                    'Fan Model': specifications.get('Fan Model'),
                    'Fan Size': specifications.get('Fan Size'),
                    'Class': specifications.get('Class'),
                    'Arrangement': specifications.get('Arrangement'),
                    'vendor': specifications.get('vendor', 'TCF Factory'),
                    'material': specifications.get('material', 'ms'),
                    'vibration_isolators': specifications.get('vibration_isolators', 'not_required'),
                    'fabrication_margin': float(specifications.get('fabrication_margin', 25) or 25),
                    'bought_out_margin': float(specifications.get('bought_out_margin', 25) or 25),
                    'motor_brand': motor.get('brand', ''),
                    'motor_kw': motor.get('kw', ''),
                    'pole': motor.get('pole', ''),
                    'efficiency': motor.get('efficiency', ''),
                    'motor_discount': float(motor.get('discount', 0) or 0),
                    'drive_pack': specifications.get('drive_pack'),
                    'customAccessories': specifications.get('custom_accessories', {}),
                    'optional_items': specifications.get('optional_items', {}),
                    'bearing_brand': specifications.get('bearing_brand', 'SKF')
                }
                
                # Add custom material data if present
                if fan_data['material'] == 'others':
                    for i in range(5):
                        weight_key = f'material_weight_{i}'
                        name_key = f'material_name_{i}'
                        rate_key = f'material_rate_{i}'
                        if weight_key in specifications and specifications[weight_key] and str(specifications[weight_key]).strip():
                            fan_data[weight_key] = float(specifications[weight_key])
                        if name_key in specifications:
                            fan_data[name_key] = specifications[name_key]
                        if rate_key in specifications and specifications[rate_key] and str(specifications[rate_key]).strip():
                            fan_data[rate_key] = float(specifications[rate_key])
                
                # Get selected accessories
                selected_accessories = []
                if 'accessories' in specifications:
                    if isinstance(specifications['accessories'], dict):
                        selected_accessories = [key for key, value in specifications['accessories'].items() if value]
                    elif isinstance(specifications['accessories'], list):
                        selected_accessories = specifications['accessories']
                
                # Calculate weights
                logger.info(f"Calculating fan weight for model: {fan_data.get('Fan Model')}, size: {fan_data.get('Fan Size')}, class: {fan_data.get('Class')}, arrangement: {fan_data.get('Arrangement')}")
                bare_fan_weight, no_of_isolators, shaft_diameter, total_weight, fan_error, accessory_details = calculate_fan_weight(
                    cursor, fan_data, selected_accessories
                )
                
                if fan_error:
                    logger.error(f"Fan weight calculation error: {fan_error}")
                    return jsonify({'error': fan_error}), 400
                
                # Allow manual override from UI for isolators/shaft if provided
                try:
                    if 'no_of_isolators' in specifications and str(specifications['no_of_isolators']).strip() != '':
                        no_of_isolators = int(float(specifications['no_of_isolators']))
                except Exception:
                    pass
                try:
                    if 'shaft_diameter' in specifications and str(specifications['shaft_diameter']).strip() != '':
                        shaft_diameter = float(specifications['shaft_diameter'])
                except Exception:
                    pass
                
                # Calculate fabrication cost
                logger.info(f"Calculating fabrication cost for vendor: {fan_data.get('vendor')}, material: {fan_data.get('material')}, weight: {total_weight}")
                fabrication_cost, total_weight, custom_weights, fab_error = calculate_fabrication_cost(cursor, fan_data, total_weight)
                if fab_error:
                    logger.error(f"Fabrication cost calculation error: {fab_error}")
                    return jsonify({'error': fab_error}), 400
                
                # Calculate bought out components
                logger.info(f"Calculating bought out components for isolators: {no_of_isolators}, shaft: {shaft_diameter}")
                bought_out_result, error = calculate_bought_out_components(cursor, fan_data, no_of_isolators, shaft_diameter)
                if error:
                    logger.error(f"Bought out components calculation error: {error}")
                    return jsonify({'error': error}), 400
                
                # Extract costs
                bought_out_cost = bought_out_result['total_cost']
                vibration_isolators_price = bought_out_result['vibration_isolators_price']
                bearing_price = bought_out_result['bearing_price']
                drive_pack_price = bought_out_result['drive_pack_price']
                motor_list_price = bought_out_result['motor_list_price']
                motor_discount = bought_out_result['motor_discount']
                discounted_motor_price = bought_out_result['discounted_motor_price']
                
                # Add optional items cost
                optional_items_cost = 0
                optional_items_detail = {}
                if 'optional_items' in specifications:
                    for item_name, item_price in specifications['optional_items'].items():
                        if item_price and str(item_price).strip() and float(item_price) > 0:
                            optional_items_cost += float(item_price)
                            optional_items_detail[item_name] = float(item_price)
                
                bought_out_cost += optional_items_cost
                
                # Calculate selling prices and margins (do not add optional_items_cost again)
                fabrication_selling_price = fabrication_cost / (1 - fan_data['fabrication_margin'] / 100)
                bought_out_selling_price = bought_out_cost / (1 - fan_data['bought_out_margin'] / 100)
                total_selling_price = fabrication_selling_price + bought_out_selling_price
                
                # Raw cost is fab + BO including optionals already
                total_raw_cost = fabrication_cost + bought_out_cost
                if total_selling_price > 0:
                    total_job_margin = ((total_selling_price - total_raw_cost) / total_selling_price) * 100
                else:
                    total_job_margin = 0
                
                # Prepare data structures
                weights = {
                    'bare_fan_weight': bare_fan_weight,
                    'accessory_weight': sum(weight for name, weight in accessory_details.items() 
                                         if name in ACCESSORY_NAME_MAP.values()),
                    'total_weight': total_weight,
                    'no_of_isolators': no_of_isolators,
                    'shaft_diameter': shaft_diameter,
                    'accessory_weight_details': accessory_details
                }
                
                # total_cost equals total_raw_cost (optionals already inside BO)
                total_cost = total_raw_cost
                # Proportional fabrication cost per accessory (estimate by weight share)
                accessory_cost_estimates = {}
                try:
                    if total_weight and total_weight > 0 and fabrication_cost is not None:
                        for acc_name, acc_wt in accessory_details.items():
                            share = (acc_wt or 0) / total_weight
                            accessory_cost_estimates[acc_name] = fabrication_cost * share
                except Exception:
                    accessory_cost_estimates = {}
                
                fabrication_cost_breakdown = {}
                try:
                    if total_weight and total_weight > 0 and fabrication_cost is not None:
                        accessory_weight_total = sum(accessory_details.values()) if accessory_details else 0
                        fabrication_cost_breakdown = {
                            'base_fabrication_cost': fabrication_cost * ((bare_fan_weight or 0) / total_weight),
                            'accessories_fabrication_cost': fabrication_cost * ((accessory_weight_total or 0) / total_weight)
                        }
                except Exception:
                    fabrication_cost_breakdown = {}
                costs = {
                    'fabrication_cost': fabrication_cost,
                    'fabrication_cost_breakdown': fabrication_cost_breakdown,
                    'bought_out_cost': bought_out_cost,
                    'optional_items_cost': optional_items_cost,
                    'optional_items_detail': optional_items_detail,
                    'total_raw_cost': total_raw_cost,
                    'total_cost': total_cost,
                    'fabrication_selling_price': fabrication_selling_price,
                    'bought_out_selling_price': bought_out_selling_price,
                    'total_selling_price': total_selling_price,
                    'total_job_margin': total_job_margin,
                    'vibration_isolators_price': vibration_isolators_price,
                    'bearing_price': bearing_price,
                    'drive_pack_price': drive_pack_price,
                    'motor_list_price': motor_list_price,
                    'discounted_motor_price': discounted_motor_price,
                    'motor_discount': motor_discount,
                    'selected_accessories': selected_accessories,
                    'accessory_cost_estimates': accessory_cost_estimates
                }
                # Attach true custom accessory fabrication costs if available (and not custom materials map)
                if isinstance(custom_weights, dict) and custom_weights:
                    try:
                        sample_val = next(iter(custom_weights.values()))
                        if not (isinstance(sample_val, dict) and 'weight' in sample_val):
                            costs['custom_accessory_costs'] = custom_weights
                    except StopIteration:
                        pass
                
                motor_data = {
                    'brand': motor.get('brand', ''),
                    'kw': motor.get('kw', ''),
                    'pole': motor.get('pole', ''),
                    'efficiency': motor.get('efficiency', ''),
                    'discount': motor.get('discount', 0)
                }
                
                # Ensure custom material data is included in specifications for database storage
                if fan_data['material'] == 'others':
                    for i in range(5):
                        weight_key = f'material_weight_{i}'
                        name_key = f'material_name_{i}'
                        rate_key = f'material_rate_{i}'
                        if weight_key in fan_data:
                            specifications[weight_key] = fan_data[weight_key]
                        if name_key in fan_data:
                            specifications[name_key] = fan_data[name_key]
                        if rate_key in fan_data:
                            specifications[rate_key] = fan_data[rate_key]

                # Save to database
                logger.info(f"Saving fan to database: {enquiry_number}/fan {fan_number}")
                from database import save_fan
                save_fan(enquiry_number, fan_number, specifications, weights, costs, motor_data, 'draft')
                logger.info(f"Fan saved successfully to database")
                
            return jsonify({
                'success': True,
                'specifications': specifications,
                'weights': weights,
                'costs': costs,
                'motor': motor_data
            })
            
        except Exception as e:
            logger.error(f"Error saving fan {enquiry_number}/fan {fan_number}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/projects/<enquiry_number>/fans/<int:fan_number>/add-to-project', methods=['POST'])
    @login_required
    def api_add_fan_to_project(enquiry_number, fan_number):
        """Mark fan as added to project."""
        try:
            from database import save_fan, get_fan
            
            # Get current fan data
            fan = get_fan(enquiry_number, fan_number)
            if not fan:
                return jsonify({'error': 'Fan not found'}), 404
            
            # Update status to 'added'
            save_fan(enquiry_number, fan_number, fan['specifications'], 
                    fan['weights'], fan['costs'], fan['motor'], 'added')
            
            return jsonify({'success': True, 'status': 'added'})
        
        except Exception as e:
            logger.error(f"Error adding fan to project: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Dependent dropdown APIs (filtered options)
    @app.route('/api/options/sizes/<fan_model>')
    @login_required
    def api_options_sizes(fan_model):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT "Fan Size" FROM FanWeights
                    WHERE "Fan Model" = ?
                    ORDER BY CAST("Fan Size" AS FLOAT)
                ''', (fan_model,))
                sizes = [str(row[0]) for row in cursor.fetchall()]
            return jsonify({'sizes': sizes})
        except Exception as e:
            logger.error(f"Error getting sizes: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/options/classes/<fan_model>/<fan_size>')
    @login_required
    def api_options_classes(fan_model, fan_size):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT "Class" FROM FanWeights
                    WHERE "Fan Model" = ? AND "Fan Size" = ?
                    ORDER BY "Class"
                ''', (fan_model, fan_size))
                classes = [str(row[0]) for row in cursor.fetchall()]
            return jsonify({'classes': classes})
        except Exception as e:
            logger.error(f"Error getting classes: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/options/arrangements/<fan_model>/<fan_size>/<class_>')
    @login_required
    def api_options_arrangements(fan_model, fan_size, class_):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT "Arrangement" FROM FanWeights
                    WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ?
                    ORDER BY CAST("Arrangement" AS TEXT)
                ''', (fan_model, fan_size, class_))
                arrangements = [str(row[0]) for row in cursor.fetchall()]
            return jsonify({'arrangements': arrangements})
        except Exception as e:
            logger.error(f"Error getting arrangements: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/vendor-rate/<vendor>/<material>/<float:weight>')
    @login_required
    def api_vendor_rate(vendor, material, weight):
        """Get vendor rate for specific material and weight."""
        logger.info(f"Vendor rate endpoint called: vendor={vendor}, material={material}, weight={weight}")
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get rate from VendorWeightDetails table
                cursor.execute('''
                    SELECT MSPrice, SS304Price FROM VendorWeightDetails
                    WHERE Vendor = ? AND WeightStart <= ? AND WeightEnd > ?
                ''', (vendor, weight, weight))
                
                vendor_row = cursor.fetchone()
                if not vendor_row:
                    logger.warning(f"No rate found for vendor {vendor} at weight {weight}")
                    return jsonify({'error': f'No rate found for vendor {vendor} at weight {weight}'}), 404
                
                ms_price, ss304_price = vendor_row
                logger.info(f"Found rates: MS={ms_price}, SS304={ss304_price}")
                
                # Determine rate based on material
                if material == 'ms':
                    rate = ms_price
                elif material == 'ss304':
                    rate = ss304_price
                elif material == 'mixed':
                    # For mixed, return MS rate (user will specify percentage)
                    rate = ms_price
                else:
                    # For others, return MS rate as default
                    rate = ms_price
                
                logger.info(f"Returning rate: {rate} for material: {material}")
                return jsonify({
                    'vendor': vendor,
                    'material': material,
                    'weight': weight,
                    'rate': rate,
                    'ms_rate': ms_price,
                    'ss304_rate': ss304_price
                })
                
        except Exception as e:
            logger.error(f"Error getting vendor rate: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # New page routes
    @app.route('/enquiries/<enquiry_number>/fans/<int:fan_number>')
    @login_required
    def fan_calculator_page(enquiry_number, fan_number):
        """Render fan calculator page."""
        try:
            from database import get_fan, get_project
            import json
            
            # Get project info
            project = get_project(enquiry_number)
            if not project:
                flash('Project not found')
                return redirect(url_for('index'))
            
            # Get fan data
            fan = get_fan(enquiry_number, fan_number)
            if not fan:
                flash('Fan not found')
                return redirect(url_for('index'))
            
            # Load dropdown options
            options = load_dropdown_options()
            
            return render_template('fan_calculator.html', 
                                 project=project, 
                                 fan=fan, 
                                 fan_number=fan_number,
                                 **options)
            
        except Exception as e:
            logger.error(f"Error loading fan calculator page: {str(e)}")
            flash('Error loading fan calculator')
            return redirect(url_for('index'))

    @app.route('/enquiries/<enquiry_number>/summary')
    @login_required
    def project_summary_page(enquiry_number):
        """Render project summary page."""
        try:
            from database import get_project
            
            logger.info(f"Loading project summary for enquiry: {enquiry_number}")
            project = get_project(enquiry_number)
            if not project:
                logger.warning(f"Project not found: {enquiry_number}")
                flash('Project not found')
                return redirect(url_for('index'))
            
            logger.info(f"Project loaded successfully: {enquiry_number}, fans: {len(project.get('fans', []))}")
            
            # Debug: Log fan specifications to see if custom material data is present
            for fan in project.get('fans', []):
                logger.info(f"Fan {fan.get('fan_number')} specifications: {fan.get('specifications', {})}")
                if fan.get('specifications', {}).get('material') == 'others':
                    logger.info(f"Fan {fan.get('fan_number')} has material='others', checking for custom materials:")
                    for i in range(5):
                        name = fan.get('specifications', {}).get(f'material_name_{i}')
                        weight = fan.get('specifications', {}).get(f'material_weight_{i}')
                        rate = fan.get('specifications', {}).get(f'material_rate_{i}')
                        logger.info(f"  Material {i}: name={name}, weight={weight}, rate={rate}")
            
            return render_template('project_summary.html', project=project)
        
        except Exception as e:
            logger.error(f"Error loading project summary for {enquiry_number}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            flash(f'Error loading project summary: {str(e)}')
            return redirect(url_for('index'))

    @app.route('/add_fan_model', methods=['POST'])
    @login_required
    def add_fan_model():
        """Add a new fan model to the database."""
        try:
            data = request.json
            logger.info(f"Adding new fan model: {data}")

            # Validate mandatory fields
            required_fields = ['new_fan_model', 'new_fan_size', 'new_class', 'new_arrangement', 'new_bare_fan_weight']
            if not all(key in data for key in required_fields):
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
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if entry already exists
                cursor.execute('''
                    SELECT COUNT(*) FROM FanWeights 
                    WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
                ''', (fan_data['fan_model'], fan_data['fan_size'], fan_data['class_'], fan_data['arrangement']))
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # Update existing entry
                    logger.info(f"Updating existing fan model: {fan_data['fan_model']}/{fan_data['fan_size']}/{fan_data['class_']}/{fan_data['arrangement']}")
                    cursor.execute('''
                        UPDATE FanWeights SET 
                            "Bare Fan Weight" = ?, "Shaft Diameter" = ?, "No. of Isolators" = ?,
                            "Unitary Base Frame" = ?, "Isolation Base Frame" = ?, "Split Casing" = ?,
                            "Inlet Companion Flange" = ?, "Outlet Companion Flange" = ?, "Inlet Butterfly Damper" = ?
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
                logger.info(f"{message} - Saved to unified database")
                return jsonify({'success': True, 'message': message})
                
        except Exception as e:
            logger.error(f"Error adding/updating fan model: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': f'Error with fan model: {str(e)}'})

    return app 
