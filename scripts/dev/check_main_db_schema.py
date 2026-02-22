import sqlite3
import os

def check_main_database_schema():
    print("Checking schema for main database (fan_pricing.db)...")
    
    # Check the main database
    main_db_path = 'fan_pricing.db'
        
    if not os.path.exists(main_db_path):
        print(f"Error: Could not find main database at {main_db_path}")
        return
        
    print(f"Using database at: {main_db_path}")
    
    try:
        conn = sqlite3.connect(main_db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("\nTables in the database:")
        print("----------------------")
        for table in tables:
            print(table[0])
        
        # Check if ProjectFans table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ProjectFans'")
        if not cursor.fetchone():
            print("\nProjectFans table does not exist in the main database!")
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
                
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    check_main_database_schema() 