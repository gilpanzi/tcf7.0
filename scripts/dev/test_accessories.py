import sqlite3
import os
import json
import logging
import uuid
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_accessories.log')
    ]
)

logger = logging.getLogger(__name__)

def test_accessories_and_fields():
    """Test saving and loading of accessories, vibration isolators, motor pole, and efficiency."""
    try:
        # Generate a unique test enquiry number
        test_enquiry = f"TEST_ACC_{uuid.uuid4().hex[:8]}"
        logger.info(f"Testing with enquiry number: {test_enquiry}")
        
        # Create test project data
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
                        "vibration_isolators": "dunlop",
                        "bearing_brand": "SKF",
                        "drive_pack_kw": 22.5,
                        "accessories": ["Inlet Guard", "Outlet Guard", "Unitary Base Frame"],
                        "custom_accessories": ["Custom Item 1", "Custom Item 2"],
                        "optional_items": ["Vibration Sensors", "Temperature Sensors"],
                        "custom_option_items": ["Custom Option 1", "Custom Option 2"]
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
        
        # Direct database test
        try:
            # Find the central database
            data_dir = 'data'
            central_db_path = os.path.join(data_dir, 'central_database', 'all_projects.db')
            
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
            
            # Delete previous test entries
            cursor.execute('DELETE FROM Projects WHERE enquiry_number LIKE "TEST_ACC_%"')
            cursor.execute('DELETE FROM ProjectFans WHERE enquiry_number LIKE "TEST_ACC_%"')
            conn.commit()
            
            # Insert project data
            project = project_data
            fan = project['fans'][0]
            
            # Calculate totals
            total_weight = fan['weights']['total_weight']
            total_cost = fan['costs']['total_cost']
            total_job_margin = fan['costs']['total_job_margin']
            
            cursor.execute('''
                INSERT INTO Projects (
                    enquiry_number, customer_name, total_fans, sales_engineer,
                    total_weight, total_cost, total_job_margin
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                project['enquiry_number'], project['customer_name'], 
                project['total_fans'], project['sales_engineer'],
                total_weight, total_cost, total_job_margin
            ))
            
            # Insert fan data
            specs = fan['specifications']
            weights = fan['weights']
            costs = fan['costs']
            motor = fan['motor']
            
            # Log what we're inserting
            logger.info("Inserting the following data into ProjectFans:")
            logger.info(f"  vibration_isolators: {specs.get('vibration_isolators', '')}")
            logger.info(f"  accessories: {specs.get('accessories', [])}")
            logger.info(f"  drive_pack_kw: {specs.get('drive_pack_kw', 0)}")
            logger.info(f"  motor_kw: {motor.get('kw', 0)}")
            logger.info(f"  motor_brand: {motor.get('brand', '')}")
            logger.info(f"  motor_pole: {motor.get('pole', 0)}")
            logger.info(f"  motor_efficiency: {motor.get('efficiency', 0)}")
            
            cursor.execute('''
                INSERT INTO ProjectFans (
                    enquiry_number, fan_number, fan_model, size, class, arrangement,
                    vendor, material, accessories, bare_fan_weight, accessory_weight,
                    total_weight, fabrication_cost, bought_out_cost, total_cost,
                    vibration_isolators, drive_pack_kw, custom_accessories, optional_items, 
                    custom_option_items, motor_kw, motor_brand, motor_pole, motor_efficiency, 
                    motor_discount_rate, bearing_brand
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                costs.get('fabrication_cost', 0),
                costs.get('bought_out_cost', 0),
                costs.get('total_cost', 0),
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
            
            # Now retrieve the fan to verify the data
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
            
            logger.info("Test Fan Data Retrieved:")
            logger.info("========================")
            
            # Log specific important fields first
            important_fields = [
                'vibration_isolators', 'drive_pack_kw', 'motor_kw', 'motor_brand',
                'motor_pole', 'motor_efficiency', 'bearing_brand'
            ]
            
            for field in important_fields:
                value = fan_dict.get(field)
                logger.info(f"{field}: {value}")
            
            # Log JSON fields
            json_fields = [
                'accessories', 'custom_accessories', 'optional_items', 'custom_option_items'
            ]
            
            for field in json_fields:
                json_str = fan_dict.get(field, '[]')
                try:
                    parsed_value = json.loads(json_str) if json_str else []
                    logger.info(f"{field}: {parsed_value}")
                except json.JSONDecodeError:
                    logger.info(f"{field}: {json_str} (Failed to parse JSON)")
            
            # Check specific fields
            check_fields = {
                'vibration_isolators': ('dunlop', str),
                'motor_kw': (18.5, float),
                'motor_brand': ('ABB', str),
                'motor_pole': (4, int),
                'motor_efficiency': (0.95, float),
                'drive_pack_kw': (22.5, float)
            }
            
            logger.info("Validation Results:")
            logger.info("==================")
            
            all_valid = True
            for field, (expected_value, value_type) in check_fields.items():
                actual_value = fan_dict.get(field)
                
                # Convert to expected type if needed
                if value_type == float and isinstance(actual_value, (int, float)):
                    actual_value = float(actual_value)
                elif value_type == int and isinstance(actual_value, (int, float)):
                    actual_value = int(actual_value)
                    
                if actual_value == expected_value:
                    logger.info(f"✓ {field}: {actual_value} (Expected: {expected_value})")
                else:
                    logger.error(f"✗ {field}: {actual_value} (Expected: {expected_value})")
                    all_valid = False
            
            # Check JSON fields
            json_field_values = {
                'accessories': ["Inlet Guard", "Outlet Guard", "Unitary Base Frame"],
                'custom_accessories': ["Custom Item 1", "Custom Item 2"],
                'optional_items': ["Vibration Sensors", "Temperature Sensors"],
                'custom_option_items': ["Custom Option 1", "Custom Option 2"]
            }
            
            for field, expected_list in json_field_values.items():
                json_str = fan_dict.get(field, '[]')
                try:
                    actual_list = json.loads(json_str) if json_str else []
                    missing = set(expected_list) - set(actual_list)
                    extra = set(actual_list) - set(expected_list)
                    
                    if not missing and not extra:
                        logger.info(f"✓ {field}: matched expected list")
                    else:
                        if missing:
                            logger.error(f"✗ {field}: Missing items: {missing}")
                        if extra:
                            logger.error(f"✗ {field}: Extra items: {extra}")
                        all_valid = False
                except json.JSONDecodeError:
                    logger.error(f"✗ {field}: Failed to parse JSON: {json_str}")
                    all_valid = False
            
            # Close the connection
            conn.close()
            
            if all_valid:
                logger.info("All values matched expected values!")
                return True
            else:
                logger.error("Some values did not match expected values.")
                return False
            
        except Exception as e:
            logger.error(f"Error during database test: {str(e)}", exc_info=True)
            return False
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_accessories_and_fields():
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1) 