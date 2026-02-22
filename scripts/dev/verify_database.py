import sqlite3
import os

def verify_database():
    """Verify database schema and data integrity."""
    db_path = 'database/fan_weights.db'
    
    print(f"Verifying database: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    print("-" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nTables found:", len(tables))
        
        for table in tables:
            table_name = table[0]
            print(f"\nChecking table: {table_name}")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            print(f"Row count: {row_count}")
            
            # Check for NULL values in required columns
            null_checks = []
            for col in columns:
                if col[3] == 1:  # NOT NULL constraint
                    null_checks.append(f'"{col[1]}" IS NULL')
            
            if null_checks:
                cursor.execute(f'''
                    SELECT COUNT(*) FROM {table_name}
                    WHERE {' OR '.join(null_checks)}
                ''')
                null_count = cursor.fetchone()[0]
                if null_count > 0:
                    print(f"WARNING: Found {null_count} rows with NULL values in required columns")
            
            # Sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
            sample = cursor.fetchone()
            if sample:
                print("\nSample row:")
                for col, val in zip([col[1] for col in columns], sample):
                    print(f"  {col}: {val}")
        
        # Specific checks for key tables
        print("\nPerforming specific checks:")
        
        # Check FanWeights
        cursor.execute('''
            SELECT DISTINCT "Fan Model", COUNT(*)
            FROM FanWeights
            GROUP BY "Fan Model"
        ''')
        fan_models = cursor.fetchall()
        print("\nFan Models distribution:")
        for model, count in fan_models:
            print(f"  {model}: {count} variants")
        
        # Check MotorPrices
        cursor.execute('''
            SELECT "Brand", "Efficiency", COUNT(*)
            FROM MotorPrices
            GROUP BY "Brand", "Efficiency"
        ''')
        motor_dist = cursor.fetchall()
        print("\nMotor Prices distribution:")
        for brand, efficiency, count in motor_dist:
            print(f"  {brand} ({efficiency}): {count} variants")
        
        # Check VendorWeightDetails
        cursor.execute('SELECT DISTINCT "Vendor" FROM VendorWeightDetails')
        vendors = cursor.fetchall()
        print("\nVendors found:")
        for vendor in vendors:
            print(f"  {vendor[0]}")
        
        conn.close()
        print("\nDatabase verification completed successfully")
        
    except Exception as e:
        print(f"Error during verification: {str(e)}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    verify_database() 