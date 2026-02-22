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
        logging.FileHandler('test_motor_data.log')
    ]
)

logger = logging.getLogger(__name__)

def test_motor_fields():
    """Test saving and loading of motor efficiency, motor discount rate, and drive pack kw."""
    try:
        # Generate a unique test enquiry number
        test_enquiry = f"TEST_MOTOR_{uuid.uuid4().hex[:8]}"
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
                        "drive_pack_kw": 22.5  # Important field being tested
                    },
                    "weights": {
                        "bare_fan_weight": 500.0,
                        "accessory_weight": 50.0,
                        "total_weight": 550.0
                    },
                    "costs": {
                        "fabrication_cost": 1500.0,
                        "bought_out_cost": 1000.0,
                        "total_cost": 2500.0
                    },
                    "motor": {
                        "kw": 18.5,
                        "brand": "ABB",
                        "pole": 4,
                        "efficiency": "IE3",  # Changed from 0.95 to IE3 as it's a string
                        "discount_rate": 0.15  # Important field being tested
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
            cursor.execute('DELETE FROM Projects WHERE enquiry_number LIKE "TEST_MOTOR_%"')
            cursor.execute('DELETE FROM ProjectFans WHERE enquiry_number LIKE "TEST_MOTOR_%"')
            conn.commit()
            
            # Insert project data
            project = project_data
            fan = project['fans'][0]
            
            # Calculate totals
            total_weight = fan['weights']['total_weight']
            total_cost = fan['costs']['total_cost']
            
            cursor.execute('''
                INSERT INTO Projects (
                    enquiry_number, customer_name, total_fans, sales_engineer,
                    total_weight, total_cost
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                project['enquiry_number'], project['customer_name'], 
                project['total_fans'], project['sales_engineer'],
                total_weight, total_cost
            ))
            
            # Insert fan data
            specs = fan['specifications']
            weights = fan['weights']
            costs = fan['costs']
            motor = fan['motor']
            
            # Log what we're inserting
            logger.info("Inserting the following test data:")
            logger.info(f"  drive_pack_kw: {specs.get('drive_pack_kw', 0)}")
            logger.info(f"  motor_kw: {motor.get('kw', 0)}")
            logger.info(f"  motor_pole: {motor.get('pole', 0)}")
            logger.info(f"  motor_efficiency: {motor.get('efficiency', 0)}")
            logger.info(f"  motor_discount_rate: {motor.get('discount_rate', 0)}")
            
            cursor.execute('''
                INSERT INTO ProjectFans (
                    enquiry_number, fan_number, fan_model, size, class, arrangement,
                    vendor, material, bare_fan_weight, accessory_weight,
                    total_weight, fabrication_cost, bought_out_cost, total_cost,
                    drive_pack_kw, motor_kw, motor_brand, motor_pole, motor_efficiency, 
                    motor_discount_rate, bearing_brand
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project['enquiry_number'], 1, 
                specs.get('fan_model', ''),
                specs.get('size', ''),
                specs.get('class', ''),
                specs.get('arrangement', ''),
                specs.get('vendor', ''),
                specs.get('material', ''),
                weights.get('bare_fan_weight', 0),
                weights.get('accessory_weight', 0),
                weights.get('total_weight', 0),
                costs.get('fabrication_cost', 0),
                costs.get('bought_out_cost', 0),
                costs.get('total_cost', 0),
                specs.get('drive_pack_kw', 0),
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
            
            logger.info("Test Results - Data Retrieved from Database:")
            logger.info("=========================================")
            
            # Check specific fields
            important_fields = [
                ('drive_pack_kw', 22.5),
                ('motor_efficiency', "IE3"),
                ('motor_pole', 4),
                ('motor_discount_rate', 0.15)
            ]
            
            all_valid = True
            for field, expected_value in important_fields:
                actual_value = fan_dict.get(field)
                if isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
                    actual_value = float(actual_value)
                    expected_value = float(expected_value)
                
                if actual_value == expected_value:
                    logger.info(f"PASS: {field}: {actual_value} (Expected: {expected_value})")
                else:
                    logger.error(f"FAIL: {field}: {actual_value} (Expected: {expected_value})")
                    all_valid = False
            
            # Simulate the data structure when loading from the API
            fan_data = {
                'specifications': {
                    'drive_pack_kw': fan_dict.get('drive_pack_kw')
                },
                'motor': {
                    'kw': fan_dict.get('motor_kw'),
                    'brand': fan_dict.get('motor_brand'),
                    'pole': fan_dict.get('motor_pole'),
                    'efficiency': fan_dict.get('motor_efficiency'),
                    'discount_rate': fan_dict.get('motor_discount_rate')
                }
            }
            
            logger.info("\nSimulating frontend data handling:")
            logger.info("----------------------------------")
            
            # Simulate data in the JavaScript flat data structure
            js_flat = {
                'drive_pack_kw': fan_data['specifications']['drive_pack_kw'],
                'motor_kw': fan_data['motor']['kw'],
                'motor_brand': fan_data['motor']['brand'],
                'pole': fan_data['motor']['pole'],
                'motor_pole': fan_data['motor']['pole'],
                'efficiency': fan_data['motor']['efficiency'],
                'motor_efficiency': fan_data['motor']['efficiency'],
                'motor_discount': fan_data['motor']['discount_rate'],
                'motor_discount_rate': fan_data['motor']['discount_rate']
            }
            
            logger.info("Simulated frontend flat data structure:")
            for key, value in js_flat.items():
                logger.info(f"  {key}: {value}")
            
            # Close the connection
            conn.close()
            
            if all_valid:
                logger.info("\nAll fields matched expected values!")
                return True
            else:
                logger.error("\nSome fields did not match expected values.")
                return False
            
        except Exception as e:
            logger.error(f"Error during database test: {str(e)}", exc_info=True)
            return False
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_motor_fields():
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1) 