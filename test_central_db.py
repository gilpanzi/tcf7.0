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
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def test_central_database():
    """Test that the ProjectFans table in the central database has all the required columns and works properly."""
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
        
        # Get current columns in ProjectFans table
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Check for required columns
        required_columns = [
            'vibration_isolators', 'drive_pack_kw', 'custom_accessories', 
            'optional_items', 'custom_option_items', 'motor_kw', 
            'motor_brand', 'motor_pole', 'motor_efficiency', 
            'motor_discount_rate', 'bearing_brand'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            logger.error(f"Missing columns in central database: {missing_columns}")
            conn.close()
            return False
        else:
            logger.info(f"All required columns exist in central database")
        
        # Check if Projects table has all required fields
        cursor.execute("PRAGMA table_info(Projects)")
        project_columns = {row[1] for row in cursor.fetchall()}
        
        # Test inserting and retrieving a fan with the new fields
        test_enquiry = "TEST_CENTRAL_DB_CHECK"
        
        # Check if test project exists and delete if it does
        cursor.execute('DELETE FROM Projects WHERE enquiry_number = ?', (test_enquiry,))
        cursor.execute('DELETE FROM ProjectFans WHERE enquiry_number = ?', (test_enquiry,))
        
        # Create test project with appropriate fields
        if 'sales_engineer' in project_columns:
            cursor.execute('''
                INSERT INTO Projects (
                    enquiry_number, customer_name, total_fans, sales_engineer,
                    total_weight, total_fabrication_cost, total_bought_out_cost,
                    total_cost, total_selling_price, total_job_margin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_enquiry, 'Test Customer', 1, 'Test Engineer',
                100.0, 500.0, 500.0, 1000.0, 1500.0, 0.5
            ))
        else:
            cursor.execute('''
                INSERT INTO Projects (
                    enquiry_number, customer_name, total_fans,
                    total_weight, total_fabrication_cost, total_bought_out_cost,
                    total_cost, total_selling_price, total_job_margin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_enquiry, 'Test Customer', 1,
                100.0, 500.0, 500.0, 1000.0, 1500.0, 0.5
            ))
        
        # Insert a test fan with all the new fields
        accessories = json.dumps(['Inlet Guard', 'Outlet Guard'])
        optional_items = json.dumps(['Vibration Sensors', 'Temperature Sensors'])
        custom_accessories = json.dumps(['Custom Item 1', 'Custom Item 2'])
        custom_option_items = json.dumps(['Custom Option 1', 'Custom Option 2'])
        
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
            test_enquiry, 1, 'DIDW', '1120', '2', '3',
            'TCF', 'CRCA', accessories, 500.0, 50.0,
            550.0, 300.0, 250.0, 1500.0, 1000.0, 2500.0,
            2000.0, 1500.0, 3500.0, 0.4, 'Spring', 22.0,
            custom_accessories, optional_items, custom_option_items,
            18.5, 'ABB', 4, 0.95, 0.15, 'SKF'
        ))
        
        # Retrieve the test fan
        cursor.execute('''
            SELECT * FROM ProjectFans
            WHERE enquiry_number = ?
        ''', (test_enquiry,))
        
        fan = cursor.fetchone()
        if fan:
            cursor.execute("PRAGMA table_info(ProjectFans)")
            col_info = cursor.fetchall()
            fan_dict = dict(zip([col[1] for col in col_info], fan))
            logger.info("Successfully retrieved test fan with new fields from central database")
            
            # Check specific fields
            for field in [
                'vibration_isolators', 'drive_pack_kw', 'custom_accessories', 
                'optional_items', 'custom_option_items', 'motor_kw', 
                'motor_brand', 'motor_pole', 'motor_efficiency', 
                'motor_discount_rate', 'bearing_brand'
            ]:
                logger.info(f"Field {field} = {fan_dict.get(field)}")
            
            # Clean up
            cursor.execute('DELETE FROM Projects WHERE enquiry_number = ?', (test_enquiry,))
            cursor.execute('DELETE FROM ProjectFans WHERE enquiry_number = ?', (test_enquiry,))
        else:
            logger.error("Failed to retrieve test fan from central database")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        logger.info("Central database test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error testing central database: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_central_database():
        print("Central database test completed successfully")
    else:
        print("Central database test failed") 