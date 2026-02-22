import sqlite3
import json
import os

def check_optional_items_in_db():
    """Check what optional items data is actually stored in the database."""
    
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
    
    # First, check the schema
    print("=== DATABASE SCHEMA FOR ProjectFans ===")
    cursor.execute("PRAGMA table_info(ProjectFans)")
    schema = cursor.fetchall()
    
    print("Columns in ProjectFans table:")
    for col in schema:
        col_id, col_name, col_type, not_null, default_val, pk = col
        print(f"  {col_name}: {col_type} (Not Null: {not_null}, Default: {default_val}, PK: {pk})")
    
    # Check for optional items related columns
    optional_columns = [col[1] for col in schema if 'optional' in col[1].lower()]
    print(f"\nOptional items related columns: {optional_columns}")
    
    # Get all projects
    cursor.execute('SELECT enquiry_number, customer_name FROM Projects ORDER BY created_at DESC LIMIT 5')
    projects = cursor.fetchall()
    
    print("\n=== RECENT PROJECTS ===")
    for project in projects:
        print(f"  {project[0]} - {project[1]}")
    
    # Get detailed fan data for the most recent project
    if projects:
        latest_enquiry = projects[0][0]
        print(f"\n=== CHECKING OPTIONAL ITEMS FOR ENQUIRY: {latest_enquiry} ===")
        
        # Get all optional-related columns that exist
        existing_cols = [col[1] for col in schema]
        optional_cols_to_check = []
        
        for col in ['optional_items', 'custom_option_items', 'optional_items_cost', 
                   'optional_items_json', 'custom_optional_items_json']:
            if col in existing_cols:
                optional_cols_to_check.append(col)
        
        if optional_cols_to_check:
            cols_str = ', '.join(optional_cols_to_check)
            query = f'''
                SELECT fan_number, {cols_str}
                FROM ProjectFans 
                WHERE enquiry_number = ?
                ORDER BY fan_number
            '''
            cursor.execute(query, (latest_enquiry,))
            fans = cursor.fetchall()
            
            for fan in fans:
                fan_number = fan[0]
                print(f"\nFan {fan_number}:")
                
                for i, col_name in enumerate(optional_cols_to_check):
                    col_value = fan[i + 1]  # +1 because fan_number is at index 0
                    print(f"  {col_name}: {col_value}")
                    
                    # Try to parse JSON if it looks like JSON
                    if col_value and isinstance(col_value, str):
                        try:
                            parsed = json.loads(col_value)
                            print(f"    Parsed: {parsed}")
                            print(f"    Type: {type(parsed)}")
                            if isinstance(parsed, dict):
                                print(f"    Keys: {list(parsed.keys())}")
                            elif isinstance(parsed, list):
                                print(f"    Length: {len(parsed)}")
                        except json.JSONDecodeError as e:
                            print(f"    Failed to parse JSON: {e}")
        else:
            print("No optional items related columns found!")
    
    # Also check if there are any fans at all
    print("\n=== CHECKING ALL FANS DATA ===")
    cursor.execute("SELECT COUNT(*) FROM ProjectFans")
    fan_count = cursor.fetchone()[0]
    print(f"Total fans in database: {fan_count}")
    
    if fan_count > 0:
        cursor.execute("SELECT enquiry_number, fan_number, optional_items, custom_option_items FROM ProjectFans LIMIT 5")
        all_fans = cursor.fetchall()
        print("Sample fan records:")
        for fan in all_fans:
            enquiry, fan_num, opt_items, custom_items = fan
            print(f"  Enquiry: {enquiry}, Fan: {fan_num}, Optional: {opt_items}, Custom: {custom_items}")
    
    conn.close()

if __name__ == "__main__":
    check_optional_items_in_db() 