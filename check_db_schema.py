import sqlite3
import os

def check_database_schema():
    print("Checking database schema for ProjectFans table...")
    
    # Check the central database
    central_db_path = 'data/central_database/all_projects.db'
    if not os.path.exists(central_db_path):
        central_db_path = 'central_database/all_projects.db'
        
    if not os.path.exists(central_db_path):
        print(f"Error: Could not find database at either path.")
        return
        
    print(f"Using database at: {central_db_path}")
    
    try:
        conn = sqlite3.connect(central_db_path)
        cursor = conn.cursor()
        
        # Check if ProjectFans table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
        if not cursor.fetchone():
            print("ProjectFans table does not exist in the database!")
            conn.close()
            return
            
        # Get column information
        cursor.execute("PRAGMA table_info(ProjectFans)")
        columns = cursor.fetchall()
        
        print("\nProjectFans table has the following columns:")
        print("--------------------------------------------")
        for col in columns:
            column_id, column_name, column_type, not_null, default_value, is_pk = col
            print(f"{column_id:2d}: {column_name:<25} (Type: {column_type})")
            
        # Check for specific columns
        important_columns = [
            'motor_kw', 'motor_brand', 'motor_pole', 'motor_efficiency', 'motor_discount_rate',
            'bearing_brand', 'vibration_isolators', 'drive_pack_kw'
        ]
        
        column_names = [col[1] for col in columns]
        
        print("\nChecking for important columns:")
        print("--------------------------------")
        for col in important_columns:
            if col in column_names:
                print(f"✓ {col} - FOUND")
            else:
                print(f"✗ {col} - MISSING")
                
        # Show example row if any data exists
        cursor.execute("SELECT * FROM ProjectFans LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            print("\nExample data in ProjectFans:")
            print("----------------------------")
            for i, col in enumerate(columns):
                column_name = col[1]
                value = row[i]
                print(f"{column_name:<25}: {value}")
        else:
            print("\nNo data found in ProjectFans table.")
            
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    check_database_schema() 