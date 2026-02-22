import sqlite3

# Function to check database tables
def check_db(db_path):
    print(f"\n{'='*50}")
    print(f"Checking database: {db_path}")
    print(f"{'='*50}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = [table[0] for table in cursor.fetchall()]
        print(f"\nTables found: {len(tables)}")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        
        # Check for MotorPrices table
        if 'MotorPrices' in tables:
            print("\nMotorPrices table found! Checking structure:")
            print("-" * 40)
            
            cursor.execute('PRAGMA table_info(MotorPrices)')
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}){'  PRIMARY KEY' if col[5] == 1 else ''}")
            
            # Get row count
            cursor.execute('SELECT COUNT(*) FROM MotorPrices')
            count = cursor.fetchone()[0]
            print(f"\nTotal rows in MotorPrices: {count}")
            
            # Get sample data
            cursor.execute('SELECT * FROM MotorPrices LIMIT 5')
            rows = cursor.fetchall()
            
            if rows:
                print("\nSample data (first 5 rows):")
                print("-" * 40)
                for i, row in enumerate(rows, 1):
                    print(f"  Row {i}: {row}")
            else:
                print("\nNo data found in MotorPrices table")
        else:
            print("\nMotorPrices table NOT found in this database")
        
        conn.close()
    except Exception as e:
        print(f"Error accessing database {db_path}: {str(e)}")

# Check both databases
check_db('fan_pricing.db')
check_db('database/fan_weights.db') 