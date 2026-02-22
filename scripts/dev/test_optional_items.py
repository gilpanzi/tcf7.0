import sqlite3
import json
import os

def test_manual_optional_items():
    """Test manually inserting optional items data to verify the database works"""
    
    # Path to the central database
    data_dir = 'data'
    central_db_path = os.path.join(data_dir, 'central_database', 'all_projects.db')
    
    # Also check the original location
    if not os.path.exists(central_db_path) and os.path.exists('central_database/all_projects.db'):
        central_db_path = 'central_database/all_projects.db'
    
    if not os.path.exists(central_db_path):
        print("No central database found")
        return
    
    conn = sqlite3.connect(central_db_path)
    cursor = conn.cursor()
    
    # Get the most recent fan record
    cursor.execute('''
        SELECT id, enquiry_number, fan_number 
        FROM ProjectFans 
        ORDER BY id DESC 
        LIMIT 1
    ''')
    
    result = cursor.fetchone()
    if not result:
        print("No fan records found")
        conn.close()
        return
    
    fan_id, enquiry_number, fan_number = result
    print(f"Testing with Fan ID: {fan_id}, Enquiry: {enquiry_number}, Fan Number: {fan_number}")
    
    # Create test optional items data
    test_optional_items = {
        "flex_connectors": 5000,
        "silencer": 3000,
        "testing_charges": 2000
    }
    
    test_custom_items = {
        "custom_item_1": 1500,
        "custom_item_2": 2500
    }
    
    # Update the record with test data
    cursor.execute('''
        UPDATE ProjectFans 
        SET optional_items = ?, custom_option_items = ?, optional_items_cost = ?
        WHERE id = ?
    ''', (
        json.dumps(test_optional_items),
        json.dumps(test_custom_items),
        sum(test_optional_items.values()) + sum(test_custom_items.values()),
        fan_id
    ))
    
    conn.commit()
    print("Updated record with test optional items data")
    
    # Verify the data was saved
    cursor.execute('''
        SELECT optional_items, custom_option_items, optional_items_cost
        FROM ProjectFans 
        WHERE id = ?
    ''', (fan_id,))
    
    result = cursor.fetchone()
    if result:
        optional_items, custom_items, cost = result
        print(f"\nSaved data:")
        print(f"  optional_items: {optional_items}")
        print(f"  custom_option_items: {custom_items}")
        print(f"  optional_items_cost: {cost}")
        
        # Parse and verify
        try:
            parsed_optional = json.loads(optional_items) if optional_items else {}
            parsed_custom = json.loads(custom_items) if custom_items else {}
            
            print(f"\nParsed data:")
            print(f"  Parsed optional_items: {parsed_optional}")
            print(f"  Parsed custom_items: {parsed_custom}")
            print(f"  Total items: {len(parsed_optional) + len(parsed_custom)}")
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
    
    conn.close()
    print("\nTest completed. Try loading this enquiry in the app to see if it shows the optional items.")

if __name__ == "__main__":
    test_manual_optional_items() 