import sqlite3
import pandas as pd
import os
import sys

def update_motor_prices(csv_path):
    """
    Update the MotorPrices table in fan_pricing.db with data from the provided CSV file.
    
    Args:
        csv_path: Path to the CSV file containing motor price data
    
    Returns:
        bool: True if successful, False otherwise
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
        
        # Connect to the database
        print("\nConnecting to database...")
        conn = sqlite3.connect('fan_pricing.db')
        cursor = conn.cursor()
        
        # Get current data count for comparison
        cursor.execute("SELECT COUNT(*) FROM MotorPrices")
        old_count = cursor.fetchone()[0]
        
        # Create a backup of the existing table
        print("Creating backup of existing MotorPrices table...")
        backup_table_name = f"MotorPrices_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(f"CREATE TABLE {backup_table_name} AS SELECT * FROM MotorPrices")
        
        # Delete all data from the existing table
        print("Clearing existing MotorPrices table...")
        cursor.execute("DELETE FROM MotorPrices")
        
        # Insert new data
        print("Importing new data...")
        
        # Convert data types if needed (handle numeric columns)
        df['Motor kW'] = pd.to_numeric(df['Motor kW'], errors='coerce')
        df['Pole'] = pd.to_numeric(df['Pole'], errors='coerce')
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
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
                print(f"Error inserting row {index}: {e}")
                print(f"Problem row data: {row}")
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM MotorPrices")
        new_count = cursor.fetchone()[0]
        
        print(f"\nImport summary:")
        print(f"  - Backed up {old_count} existing motor price records to {backup_table_name}")
        print(f"  - Attempted to import {len(df)} records from CSV")
        print(f"  - Successfully imported: {success_count} records")
        print(f"  - Failed to import: {error_count} records")
        print(f"  - Total records now in MotorPrices: {new_count}")
        
        # Commit changes
        conn.commit()
        print("Changes committed to database successfully!")
        
        # Get sample data to verify
        print("\nSample data from updated MotorPrices table:")
        cursor.execute("SELECT * FROM MotorPrices ORDER BY Brand, \"Motor kW\", Pole LIMIT 5")
        rows = cursor.fetchall()
        
        cursor.execute('PRAGMA table_info(MotorPrices)')
        columns = [col[1] for col in cursor.fetchall()]
        
        for row in rows:
            print(dict(zip(columns, row)))
        
        conn.close()
        print("\nDatabase connection closed. Update completed.")
        return True
        
    except Exception as e:
        print(f"Error updating motor prices: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Motor Prices Update Tool ===")
    
    # Check if CSV path is provided as command line argument
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        print(f"Using CSV file from command line argument: {csv_path}")
    else:
        # Default to motor_prices.csv in the current directory
        csv_path = "motor_prices.csv"
        print(f"No CSV file specified. Using default: {csv_path}")
        print("Tip: You can specify a CSV file path as a command line argument:")
        print("     python update_motor_prices.py path/to/your/motor_prices.csv")
    
    # Confirm before proceeding
    confirm = input(f"Update MotorPrices table with data from '{csv_path}'? (y/n): ")
    
    if confirm.lower() == 'y':
        update_motor_prices(csv_path)
    else:
        print("Operation cancelled.") 