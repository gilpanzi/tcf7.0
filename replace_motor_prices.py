import sqlite3
import pandas as pd
import os

# Set the CSV file path - update this to your CSV file's location
CSV_FILE = "motor_prices.csv"  # Assuming the file is named motor_prices.csv in the project root

def replace_motor_prices():
    """
    Replace the MotorPrices table in fan_pricing.db with data from the CSV file.
    """
    try:
        # Check if the CSV file exists
        if not os.path.exists(CSV_FILE):
            print(f"Error: CSV file not found at '{CSV_FILE}'")
            print("Please place your CSV file in the project directory with the name 'motor_prices.csv'")
            print("Or update the CSV_FILE variable in this script with the correct path")
            return False
        
        # Read the CSV file
        print(f"Reading data from {CSV_FILE}...")
        df = pd.read_csv(CSV_FILE)
        
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
        cursor.execute("DROP TABLE IF EXISTS MotorPrices_backup")
        cursor.execute("CREATE TABLE MotorPrices_backup AS SELECT * FROM MotorPrices")
        
        # Delete all data from the existing table
        print("Clearing existing MotorPrices table...")
        cursor.execute("DELETE FROM MotorPrices")
        
        # Insert new data
        print("Importing new data...")
        
        # Direct pandas to_sql method with replace (alternative method)
        # df.to_sql('MotorPrices', conn, if_exists='replace', index=False)
        
        # Row by row insertion for better error handling
        for index, row in df.iterrows():
            try:
                cursor.execute(
                    "INSERT INTO MotorPrices (Brand, \"Motor kW\", Pole, Efficiency, Price) VALUES (?, ?, ?, ?, ?)",
                    (row['Brand'], row['Motor kW'], row['Pole'], row['Efficiency'], row['Price'])
                )
            except Exception as e:
                print(f"Error inserting row {index}: {e}")
                print(f"Problem row data: {row}")
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM MotorPrices")
        new_count = cursor.fetchone()[0]
        
        print(f"\nImport summary:")
        print(f"  - Backed up {old_count} existing motor price records")
        print(f"  - Imported {new_count} motor price records from CSV")
        
        # Commit changes
        conn.commit()
        print("Changes committed to database successfully!")
        
        # Get sample data to verify
        print("\nSample data from imported records:")
        cursor.execute("SELECT * FROM MotorPrices ORDER BY Brand, \"Motor kW\", Pole LIMIT 5")
        rows = cursor.fetchall()
        
        cursor.execute('PRAGMA table_info(MotorPrices)')
        columns = [col[1] for col in cursor.fetchall()]
        
        for row in rows:
            print(dict(zip(columns, row)))
        
        conn.close()
        print("\nDatabase connection closed. Import completed.")
        return True
        
    except Exception as e:
        print(f"Error importing data: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Motor Prices Replacement Tool ===")
    print(f"This script will replace the MotorPrices table with data from '{CSV_FILE}'")
    confirm = input("Continue? (y/n): ")
    
    if confirm.lower() == 'y':
        replace_motor_prices()
    else:
        print("Operation cancelled.") 