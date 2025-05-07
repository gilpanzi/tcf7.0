import sqlite3
import pandas as pd
import os

# Set the CSV file path
CSV_FILE = "database/MotorPrices.csv"

def update_both_databases():
    """Update motor prices in both databases from CSV file"""
    try:
        # Check if the CSV file exists
        if not os.path.exists(CSV_FILE):
            print(f"Error: CSV file not found at '{CSV_FILE}'")
            return False
        
        # Read the CSV file
        print(f"Reading data from {CSV_FILE}...")
        df = pd.read_csv(CSV_FILE)
        
        # Show data preview
        print(f"Total records in CSV: {len(df)}")
        
        # Convert data types
        df['Motor kW'] = pd.to_numeric(df['Motor kW'], errors='coerce')
        df['Pole'] = pd.to_numeric(df['Pole'], errors='coerce')
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        # List of databases to update
        databases = [
            {'path': 'fan_pricing.db', 'name': 'Main database (fan_pricing.db)'},
            {'path': 'database/fan_weights.db', 'name': 'Secondary database (fan_weights.db)'}
        ]
        
        # Update each database
        for db in databases:
            print(f"\n=== Updating {db['name']} ===")
            
            try:
                # Connect to the database
                conn = sqlite3.connect(db['path'])
                cursor = conn.cursor()
                
                # Check if MotorPrices table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='MotorPrices'")
                if not cursor.fetchone():
                    print(f"Warning: MotorPrices table not found in {db['name']}. Skipping...")
                    conn.close()
                    continue
                
                # Get current row count
                cursor.execute("SELECT COUNT(*) FROM MotorPrices")
                old_count = cursor.fetchone()[0]
                print(f"Found {old_count} existing records")
                
                # Create a backup
                backup_name = f"MotorPrices_backup"
                print(f"Creating backup table: {backup_name}")
                cursor.execute(f"DROP TABLE IF EXISTS {backup_name}")
                cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM MotorPrices")
                
                # Clear existing data
                print("Clearing existing data...")
                cursor.execute("DELETE FROM MotorPrices")
                
                # Insert new data
                print("Importing new data...")
                success_count = 0
                error_count = 0
                
                for index, row in df.iterrows():
                    try:
                        cursor.execute(
                            "INSERT INTO MotorPrices (Brand, \"Motor kW\", Pole, Efficiency, Price) VALUES (?, ?, ?, ?, ?)",
                            (row['Brand'], row['Motor kW'], row['Pole'], row['Efficiency'], row['Price'])
                        )
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                
                # Verify import
                cursor.execute("SELECT COUNT(*) FROM MotorPrices")
                new_count = cursor.fetchone()[0]
                
                print(f"Import summary:")
                print(f"  - Successfully imported: {success_count} records")
                print(f"  - Failed: {error_count} records")
                print(f"  - Total records in table: {new_count}")
                
                # Commit and close
                conn.commit()
                print("Changes committed successfully!")
                conn.close()
                
            except Exception as e:
                print(f"Error updating {db['name']}: {str(e)}")
        
        print("\nUpdate process completed!")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Updating Motor Prices in Both Databases ===")
    update_both_databases() 