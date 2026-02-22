import sqlite3
import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_load_test.log')
    ]
)

logger = logging.getLogger(__name__)

def test_load_project():
    """Test loading project data from the central database."""
    try:
        # Find the central database
        central_db_path = None
        if os.path.exists('data/central_database/all_projects.db'):
            central_db_path = 'data/central_database/all_projects.db'
        elif os.path.exists('central_database/all_projects.db'):
            central_db_path = 'central_database/all_projects.db'
        else:
            logger.error("Central database not found")
            return False
        
        logger.info(f"Using central database at: {central_db_path}")
        
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Get all project enquiry numbers
        cursor.execute("SELECT enquiry_number FROM Projects")
        projects = cursor.fetchall()
        
        if not projects:
            logger.error("No projects found in database")
            conn.close()
            return False
        
        # Test the first project
        enquiry_number = projects[0][0]
        logger.info(f"Testing project with enquiry number: {enquiry_number}")
        
        # Get project details
        cursor.execute('''
            SELECT enquiry_number, customer_name, total_fans, sales_engineer, created_at
            FROM Projects
            WHERE enquiry_number = ?
        ''', (enquiry_number,))
        
        project = cursor.fetchone()
        if not project:
            logger.error(f"No project found with enquiry number: {enquiry_number}")
            conn.close()
            return False
        
        project_dict = {
            'enquiry_number': project[0],
            'customer_name': project[1],
            'total_fans': project[2],
            'sales_engineer': project[3],
            'created_at': project[4]
        }
        
        logger.info(f"Project details: {project_dict}")
        
        # Get all fans for this project
        cursor.execute('''
            SELECT * FROM ProjectFans
            WHERE enquiry_number = ?
            ORDER BY fan_number
        ''', (enquiry_number,))
        
        fans = []
        fan_rows = cursor.fetchall()
        
        if not fan_rows:
            logger.error(f"No fans found for project: {enquiry_number}")
            conn.close()
            return False
        
        logger.info(f"Found {len(fan_rows)} fans for project {enquiry_number}")
        
        # Get column names
        column_names = [col[0] for col in cursor.description]
        logger.info(f"Database columns: {column_names}")
        
        for row in fan_rows:
            fan_dict = dict(zip(column_names, row))
            logger.info(f"Raw fan data from database: {fan_dict}")
            
            # Build a proper fan structure with nested objects
            fan_data = {
                'specifications': {
                    'fan_model': fan_dict.get('fan_model', ''),
                    'size': fan_dict.get('size', ''),
                    'class': fan_dict.get('class', ''),
                    'arrangement': fan_dict.get('arrangement', ''),
                    'vendor': fan_dict.get('vendor', ''),
                    'material': fan_dict.get('material', ''),
                    'vibration_isolators': fan_dict.get('vibration_isolators', ''),
                    'bearing_brand': fan_dict.get('bearing_brand', ''),
                    'drive_pack_kw': fan_dict.get('drive_pack_kw', 0),
                },
                'weights': {
                    'bare_fan_weight': float(fan_dict.get('bare_fan_weight', 0) or 0),
                    'accessory_weight': float(fan_dict.get('accessory_weight', 0) or 0),
                    'total_weight': float(fan_dict.get('total_weight', 0) or 0),
                    'fabrication_weight': float(fan_dict.get('fabrication_weight', 0) or 0),
                    'bought_out_weight': float(fan_dict.get('bought_out_weight', 0) or 0),
                },
                'costs': {
                    'fabrication_cost': float(fan_dict.get('fabrication_cost', 0) or 0),
                    'bought_out_cost': float(fan_dict.get('bought_out_cost', 0) or 0),
                    'total_cost': float(fan_dict.get('total_cost', 0) or 0),
                    'fabrication_selling_price': float(fan_dict.get('fabrication_selling_price', 0) or 0),
                    'bought_out_selling_price': float(fan_dict.get('bought_out_selling_price', 0) or 0),
                    'total_selling_price': float(fan_dict.get('total_selling_price', 0) or 0),
                    'total_job_margin': float(fan_dict.get('total_job_margin', 0) or 0),
                },
                'motor': {
                    'kw': float(fan_dict.get('motor_kw', 0) or 0),
                    'brand': fan_dict.get('motor_brand', ''),
                    'pole': int(fan_dict.get('motor_pole', 0) or 0),
                    'efficiency': float(fan_dict.get('motor_efficiency', 0) or 0),
                    'discount_rate': float(fan_dict.get('motor_discount_rate', 0) or 0),
                }
            }
            
            # Parse JSON fields
            for json_field, spec_field in [
                ('accessories', 'accessories'),
                ('custom_accessories', 'custom_accessories'),
                ('optional_items', 'optional_items'),
                ('custom_option_items', 'custom_option_items')
            ]:
                if fan_dict.get(json_field):
                    try:
                        fan_data['specifications'][spec_field] = json.loads(fan_dict[json_field])
                    except:
                        logger.warning(f"Failed to parse JSON for {json_field}: {fan_dict.get(json_field)}")
                        fan_data['specifications'][spec_field] = []
                else:
                    fan_data['specifications'][spec_field] = []
            
            fans.append(fan_data)
            
            # Log important values
            logger.info(f"Fan #{fan_dict.get('fan_number')} Model: {fan_data['specifications']['fan_model']}")
            logger.info(f"Fan #{fan_dict.get('fan_number')} Size: {fan_data['specifications']['size']}")
            logger.info(f"Fan #{fan_dict.get('fan_number')} Class: {fan_data['specifications']['class']}")
            logger.info(f"Fan #{fan_dict.get('fan_number')} Arrangement: {fan_data['specifications']['arrangement']}")
            logger.info(f"Fan #{fan_dict.get('fan_number')} Total Weight: {fan_data['weights']['total_weight']}")
            logger.info(f"Fan #{fan_dict.get('fan_number')} Total Cost: {fan_data['costs']['total_cost']}")
        
        conn.close()
        logger.info("Data loading test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error testing data loading: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_load_project():
        print("Data loading test completed successfully")
    else:
        print("Data loading test failed") 