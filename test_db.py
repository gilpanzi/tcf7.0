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

def test_projectfans_columns():
    """Test that the ProjectFans table has all the required columns."""
    try:
        # Check both databases
        for db_path in ['fan_pricing.db', 'data/central_database/all_projects.db']:
            if not os.path.exists(db_path):
                if db_path == 'data/central_database/all_projects.db' and os.path.exists('central_database/all_projects.db'):
                    db_path = 'central_database/all_projects.db'
                else:
                    logger.warning(f"Database not found: {db_path}")
                    continue
            
            conn = sqlite3.connect(db_path)
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
                logger.error(f"Missing columns in {db_path}: {missing_columns}")
            else:
                logger.info(f"All required columns exist in {db_path}")
            
            # Test inserting and retrieving a fan with the new fields
            # Only for the main database
            if db_path == 'fan_pricing.db':
                # Check the foreign key column name (project_id vs enquiry_number)
                uses_project_id = 'project_id' in columns
                uses_enquiry_number = 'enquiry_number' in columns
                
                logger.info(f"Database uses project_id: {uses_project_id}, enquiry_number: {uses_enquiry_number}")
                
                if uses_project_id:
                    # Check if Projects table has sales_engineer field
                    cursor.execute("PRAGMA table_info(Projects)")
                    project_columns = {row[1] for row in cursor.fetchall()}
                    has_sales_engineer = 'sales_engineer' in project_columns
                    
                    test_enquiry = "TEST_DB_CHECK"
                    
                    # Check if test project exists and delete if it does
                    cursor.execute('DELETE FROM Projects WHERE enquiry_number = ?', (test_enquiry,))
                    
                    # Create test project with appropriate fields
                    if has_sales_engineer:
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
                    
                    # Get the project ID
                    cursor.execute('SELECT id FROM Projects WHERE enquiry_number = ?', (test_enquiry,))
                    project_id = cursor.fetchone()[0]
                    
                    # Delete any existing test fans
                    cursor.execute('DELETE FROM ProjectFans WHERE project_id = ?', (project_id,))
                    
                    # Insert a test fan with all the new fields
                    accessories = json.dumps(['Inlet Guard', 'Outlet Guard'])
                    optional_items = json.dumps(['Vibration Sensors', 'Temperature Sensors'])
                    custom_accessories = json.dumps(['Custom Item 1', 'Custom Item 2'])
                    custom_option_items = json.dumps(['Custom Option 1', 'Custom Option 2'])
                    
                    # Check if the column names match the expected format
                    cursor.execute("PRAGMA table_info(ProjectFans)")
                    col_info = cursor.fetchall()
                    col_names = [col[1] for col in col_info]
                    
                    # Adjust for different column naming (fan_size vs size)
                    has_fan_size = 'fan_size' in col_names
                    size_column = 'fan_size' if has_fan_size else 'size'
                    
                    # Adjust for different weight column naming
                    has_accessory_weights = 'accessory_weights' in col_names
                    accessory_weight_column = 'accessory_weights' if has_accessory_weights else 'accessory_weight'
                    
                    # Prepare columns and values for insert
                    columns_str = f'''
                        project_id, fan_number, fan_model, {size_column}, class, arrangement,
                        vendor, material, accessories, bare_fan_weight, {accessory_weight_column},
                        total_weight, fabrication_cost, bought_out_cost, total_cost,
                        total_job_margin, vibration_isolators, drive_pack_kw, 
                        custom_accessories, optional_items, custom_option_items,
                        motor_kw, motor_brand, motor_pole, motor_efficiency, 
                        motor_discount_rate, bearing_brand
                    '''
                    
                    placeholders = ','.join(['?' for _ in range(columns_str.count(',') + 1)])
                    
                    # Execute the insert with dynamic columns
                    cursor.execute(f'''
                        INSERT INTO ProjectFans (
                            {columns_str}
                        ) VALUES ({placeholders})
                    ''', (
                        project_id, 1, 'DIDW', '1120', '2', '3',
                        'TCF', 'CRCA', accessories, 500.0, 50.0,
                        550.0, 1500.0, 1000.0, 2500.0,
                        0.4, 'Spring', 22.0,
                        custom_accessories, optional_items, custom_option_items,
                        18.5, 'ABB', 4, 0.95, 0.15, 'SKF'
                    ))
                    
                    # Retrieve the test fan
                    cursor.execute('''
                        SELECT * FROM ProjectFans
                        WHERE project_id = ?
                    ''', (project_id,))
                    
                    fan = cursor.fetchone()
                    if fan:
                        fan_dict = dict(zip([col[1] for col in col_info], fan))
                        logger.info("Successfully retrieved test fan with new fields")
                        
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
                        cursor.execute('DELETE FROM ProjectFans WHERE project_id = ?', (project_id,))
                    else:
                        logger.error("Failed to retrieve test fan")
            
            conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error testing ProjectFans table: {str(e)}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    if test_projectfans_columns():
        print("ProjectFans table test completed successfully")
    else:
        print("ProjectFans table test failed") 