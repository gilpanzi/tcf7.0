import sqlite3
import pandas as pd
import os
import sys

def update_motor_prices_in_both_databases(csv_path):
    """
    Update the MotorPrices table in both fan_pricing.db and database/fan_weights.db
    with data from the provided CSV file.
    """
    try:
        # Check if the CSV file exists
        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found at '{csv_path}'")
            return False
        
        # Read the CSV file
        print(f"Reading data from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        # Show data preview
        print("\nPreview of CSV data:")
        print(df.head())
        print(f"Total records in CSV: {len(df)}")
        
        # Validate columns
        required_columns = ['Brand', 'Motor kW', 'Pole', 'Efficiency', 'Price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Error: Missing required columns in CSV: {', '.join(missing_columns)}")
            print(f"The CSV must have these columns: {', '.join(required_columns)}")
            return False
        
        # Convert data types if needed (handle numeric columns)
        df['Motor kW'] = pd.to_numeric(df['Motor kW'], errors='coerce')
        df['Pole'] = pd.to_numeric(df['Pole'], errors='coerce')
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        # List of databases to update
        databases = [
            {'path': 'fan_pricing.db', 'name': 'fan_pricing.db (main database)'},
            {'path': 'database/fan_weights.db', 'name': 'fan_weights.db (secondary database)'}
        ]
        
        # Update each database
        for db in databases:
            print(f"\n{'='*50}")
            print(f"Updating {db['name']}...")
            print(f"{'='*50}")
            
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
                
                # Get current data count for comparison
                cursor.execute("SELECT COUNT(*) FROM MotorPrices")
                old_count = cursor.fetchone()[0]
                
                # Create a backup of the existing table
                backup_table_name = f"MotorPrices_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"Creating backup: {backup_table_name}")
                cursor.execute(f"CREATE TABLE {backup_table_name} AS SELECT * FROM MotorPrices")
                
                # Delete all data from the existing table
                print("Clearing existing MotorPrices table...")
                cursor.execute("DELETE FROM MotorPrices")
                
                # Insert new data
                print("Importing new data...")
                
                # Row by row insertion for better error handling
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
                        if error_count <= 5:  # Only show the first 5 errors to avoid flooding the console
                            print(f"Error inserting row {index}: {str(e)}")
                            print(f"Problem row data: {row}")
                        elif error_count == 6:
                            print("Additional errors occurred but are not displayed...")
                
                # Verify import
                cursor.execute("SELECT COUNT(*) FROM MotorPrices")
                new_count = cursor.fetchone()[0]
                
                print(f"\nImport summary for {db['name']}:")
                print(f"  - Backed up {old_count} existing motor price records")
                print(f"  - Attempted to import {len(df)} records from CSV")
                print(f"  - Successfully imported: {success_count} records")
                print(f"  - Failed to import: {error_count} records")
                print(f"  - Total records now in MotorPrices: {new_count}")
                
                # Commit changes
                conn.commit()
                print(f"Changes committed to {db['name']} successfully!")
                
                # Get sample data to verify
                print(f"\nSample data from updated MotorPrices table in {db['name']}:")
                cursor.execute("SELECT * FROM MotorPrices ORDER BY Brand, \"Motor kW\", Pole LIMIT 3")
                rows = cursor.fetchall()
                
                cursor.execute('PRAGMA table_info(MotorPrices)')
                columns = [col[1] for col in cursor.fetchall()]
                
                for row in rows:
                    print(dict(zip(columns, row)))
                
                conn.close()
                
            except Exception as e:
                print(f"Error updating {db['name']}: {str(e)}")
                continue
        
        print("\nDatabase update process completed.")
        return True
        
    except Exception as e:
        print(f"Error in update process: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Motor Prices Update Tool for Multiple Databases ===")
    
    # Check if CSV path is provided as command line argument
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        print(f"Using CSV file from command line argument: {csv_path}")
    else:
        # Default to motor_prices.csv in the current directory
        csv_path = "database/MotorPrices.csv"
        print(f"No CSV file specified. Using default: {csv_path}")
        print("Tip: You can specify a CSV file path as a command line argument:")
        print("     python update_both_databases.py path/to/your/motor_prices.csv")
    
    # Confirm before proceeding
    confirm = input(f"Update MotorPrices table in BOTH databases with data from '{csv_path}'? (y/n): ")
    
    if confirm.lower() == 'y':
        update_motor_prices_in_both_databases(csv_path)
    else:
        print("Operation cancelled.") 