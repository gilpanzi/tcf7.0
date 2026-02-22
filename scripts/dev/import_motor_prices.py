import sqlite3
import pandas as pd
import os

def import_motor_prices_from_csv(csv_path):
    """
    Import motor prices from a CSV file and replace the existing MotorPrices table
    in the fan_pricing.db database.
    
    The CSV should have columns matching: Brand, Motor kW, Pole, Efficiency, Price
    """
    try:
        # Check if the CSV file exists
        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found at {csv_path}")
            return False
        
        # Read the CSV file
        print(f"Reading data from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        # Validate columns
        required_columns = ['Brand', 'Motor kW', 'Pole', 'Efficiency', 'Price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Error: Missing required columns in CSV: {', '.join(missing_columns)}")
            print(f"The CSV must have these columns: {', '.join(required_columns)}")
            return False
        
        # Connect to the database
        print("Connecting to database...")
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
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO MotorPrices (Brand, \"Motor kW\", Pole, Efficiency, Price) VALUES (?, ?, ?, ?, ?)",
                (row['Brand'], row['Motor kW'], row['Pole'], row['Efficiency'], row['Price'])
            )
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM MotorPrices")
        new_count = cursor.fetchone()[0]
        
        print(f"Import summary:")
        print(f"  - Backed up {old_count} existing motor price records")
        print(f"  - Imported {new_count} motor price records from CSV")
        
        # Commit changes
        conn.commit()
        print("Changes committed to database successfully!")
        
        # Get sample data to verify
        cursor.execute("SELECT * FROM MotorPrices ORDER BY Brand, \"Motor kW\", Pole LIMIT 5")
        rows = cursor.fetchall()
        
        print("\nSample data from imported records:")
        cursor.execute('PRAGMA table_info(MotorPrices)')
        columns = [col[1] for col in cursor.fetchall()]
        
        for row in rows:
            print(dict(zip(columns, row)))
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error importing data: {str(e)}")
        return False

if __name__ == "__main__":
    csv_path = input("Enter the path to your CSV file: ")
    import_motor_prices_from_csv(csv_path) 