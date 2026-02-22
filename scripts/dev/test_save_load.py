import sqlite3
import os
import json
import requests
import logging
import uuid
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_save_load.log')
    ]
)

logger = logging.getLogger(__name__)

def test_save_load_project():
    """Test saving a project with all fields to the database and then loading it."""
    try:
        base_url = "http://localhost:5000"  # Update if your app runs on a different port
        
        # Generate a unique test enquiry number
        test_enquiry = f"TEST_{uuid.uuid4().hex[:8]}"
        logger.info(f"Testing with enquiry number: {test_enquiry}")
        
        # Create test project data with all fields
        project_data = {
            "enquiry_number": test_enquiry,
            "customer_name": "Test Customer",
            "total_fans": 1,
            "sales_engineer": "Test Engineer",
            "fans": [
                {
                    "fan_number": 1,
                    "specifications": {
                        "fan_model": "TEST-FAN",
                        "size": "1000",
                        "class": "2",
                        "arrangement": "4",
                        "vendor": "TCF Factory",
                        "material": "ms",
                        "vibration_isolators": "Spring",
                        "bearing_brand": "SKF",
                        "drive_pack_kw": 22.5,
                        "custom_accessories": ["Custom Item 1", "Custom Item 2"],
                        "optional_items": ["Vibration Sensors", "Temperature Sensors"],
                        "custom_option_items": ["Custom Option 1", "Custom Option 2"],
                        "accessories": ["Inlet Guard", "Outlet Guard"]
                    },
                    "weights": {
                        "bare_fan_weight": 500.0,
                        "accessory_weight": 50.0,
                        "total_weight": 550.0,
                        "fabrication_weight": 300.0,
                        "bought_out_weight": 250.0
                    },
                    "costs": {
                        "fabrication_cost": 1500.0,
                        "bought_out_cost": 1000.0,
                        "total_cost": 2500.0,
                        "fabrication_selling_price": 2000.0,
                        "bought_out_selling_price": 1500.0,
                        "total_selling_price": 3500.0,
                        "total_job_margin": 40.0
                    },
                    "motor": {
                        "kw": 18.5,
                        "brand": "ABB",
                        "pole": 4,
                        "efficiency": 0.95,
                        "discount_rate": 0.15
                    }
                }
            ]
        }
        
        # Direct database test (bypass HTTP)
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
            
            # Delete previous test entry if it exists (for clean test)
            cursor.execute('DELETE FROM Projects WHERE enquiry_number LIKE "TEST_%"')
            cursor.execute('DELETE FROM ProjectFans WHERE enquiry_number LIKE "TEST_%"')
            conn.commit()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    enquiry_number TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    total_fans INTEGER NOT NULL,
                    sales_engineer TEXT NOT NULL,
                    total_weight REAL,
                    total_fabrication_cost REAL,
                    total_bought_out_cost REAL,
                    total_cost REAL,
                    total_selling_price REAL, 
                    total_job_margin REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert project data
            project = project_data
            fan = project['fans'][0]
            
            # Calculate totals
            total_weight = fan['weights']['total_weight']
            total_fabrication_cost = fan['costs']['fabrication_cost']
            total_bought_out_cost = fan['costs']['bought_out_cost']
            total_cost = fan['costs']['total_cost']
            total_job_margin = fan['costs']['total_job_margin']
            
            cursor.execute('''
                INSERT INTO Projects (
                    enquiry_number, customer_name, total_fans, sales_engineer,
                    total_weight, total_fabrication_cost, total_bought_out_cost,
                    total_cost, total_selling_price, total_job_margin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project['enquiry_number'], project['customer_name'], project['total_fans'],
                project['sales_engineer'], total_weight, total_fabrication_cost,
                total_bought_out_cost, total_cost, total_cost, total_job_margin
            ))
            
            # Insert fan data
            specs = fan['specifications']
            weights = fan['weights']
            costs = fan['costs']
            motor = fan['motor']
            
            cursor.execute('''
                INSERT INTO ProjectFans (
                    enquiry_number, fan_number, fan_model, size, class, arrangement,
                    vendor, material, accessories, bare_fan_weight, accessory_weight,
                    total_weight, fabrication_weight, bought_out_weight,
                    fabrication_cost, bought_out_cost, total_cost,
                    fabrication_selling_price, bought_out_selling_price, total_selling_price, total_job_margin,
                    vibration_isolators, drive_pack_kw, custom_accessories, optional_items, custom_option_items,
                    motor_kw, motor_brand, motor_pole, motor_efficiency, motor_discount_rate, bearing_brand
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project['enquiry_number'], 1, 
                specs.get('fan_model', ''),
                specs.get('size', ''),
                specs.get('class', ''),
                specs.get('arrangement', ''),
                specs.get('vendor', ''),
                specs.get('material', ''),
                json.dumps(specs.get('accessories', [])),
                weights.get('bare_fan_weight', 0),
                weights.get('accessory_weight', 0),
                weights.get('total_weight', 0),
                weights.get('fabrication_weight', 0),
                weights.get('bought_out_weight', 0),
                costs.get('fabrication_cost', 0),
                costs.get('bought_out_cost', 0),
                costs.get('total_cost', 0),
                costs.get('fabrication_selling_price', 0),
                costs.get('bought_out_selling_price', 0),
                costs.get('total_selling_price', 0),
                costs.get('total_job_margin', 0),
                specs.get('vibration_isolators', ''),
                specs.get('drive_pack_kw', 0),
                json.dumps(specs.get('custom_accessories', [])),
                json.dumps(specs.get('optional_items', [])),
                json.dumps(specs.get('custom_option_items', [])),
                motor.get('kw', 0),
                motor.get('brand', ''),
                motor.get('pole', 0),
                motor.get('efficiency', 0),
                motor.get('discount_rate', 0),
                specs.get('bearing_brand', '')
            ))
            
            conn.commit()
            logger.info(f"Successfully inserted test project {test_enquiry}")
            
            # Now retrieve the fan to verify the data was saved correctly
            cursor.execute('''
                SELECT * FROM ProjectFans
                WHERE enquiry_number = ?
            ''', (test_enquiry,))
            
            # Get column names
            column_names = [col[0] for col in cursor.description]
            
            # Fetch the fan data
            fan_row = cursor.fetchone()
            if not fan_row:
                logger.error(f"Failed to retrieve test fan for {test_enquiry}")
                conn.close()
                return False
            
            # Create a dictionary from the row
            fan_dict = dict(zip(column_names, fan_row))
            
            # Log the values of specific fields we care about
            important_fields = [
                'vibration_isolators', 'drive_pack_kw', 'custom_accessories', 
                'optional_items', 'custom_option_items', 'motor_kw', 
                'motor_brand', 'motor_pole', 'motor_efficiency', 
                'motor_discount_rate', 'bearing_brand'
            ]
            
            logger.info("\nTest Fan Data Retrieved:")
            logger.info("========================")
            
            for field in important_fields:
                value = fan_dict.get(field)
                
                # Pretty-print JSON fields
                if field in ['custom_accessories', 'optional_items', 'custom_option_items', 'accessories'] and value:
                    try:
                        parsed_value = json.loads(value)
                        logger.info(f"{field}: {parsed_value}")
                    except:
                        logger.info(f"{field}: {value}")
                else:
                    logger.info(f"{field}: {value}")
            
            # Verify specific fields match what we saved
            success = True
            
            # Check motor_kw
            if fan_dict.get('motor_kw') != motor.get('kw'):
                logger.error(f"motor_kw mismatch: {fan_dict.get('motor_kw')} != {motor.get('kw')}")
                success = False
                
            # Check motor_brand
            if fan_dict.get('motor_brand') != motor.get('brand'):
                logger.error(f"motor_brand mismatch: {fan_dict.get('motor_brand')} != {motor.get('brand')}")
                success = False
                
            # Check motor_pole
            if fan_dict.get('motor_pole') != motor.get('pole'):
                logger.error(f"motor_pole mismatch: {fan_dict.get('motor_pole')} != {motor.get('pole')}")
                success = False
                
            # Check bearing_brand
            if fan_dict.get('bearing_brand') != specs.get('bearing_brand'):
                logger.error(f"bearing_brand mismatch: {fan_dict.get('bearing_brand')} != {specs.get('bearing_brand')}")
                success = False
                
            # Check vibration_isolators
            if fan_dict.get('vibration_isolators') != specs.get('vibration_isolators'):
                logger.error(f"vibration_isolators mismatch: {fan_dict.get('vibration_isolators')} != {specs.get('vibration_isolators')}")
                success = False
                
            # Check drive_pack_kw
            if fan_dict.get('drive_pack_kw') != specs.get('drive_pack_kw'):
                logger.error(f"drive_pack_kw mismatch: {fan_dict.get('drive_pack_kw')} != {specs.get('drive_pack_kw')}")
                success = False
            
            conn.close()
            
            if success:
                logger.info("\nTest PASSED! All data was saved and retrieved correctly.")
                return True
            else:
                logger.error("\nTest FAILED! Some data was not saved or retrieved correctly.")
                return False
            
        except Exception as e:
            logger.error(f"Error during direct database test: {str(e)}", exc_info=True)
            return False
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_save_load_project():
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1) 