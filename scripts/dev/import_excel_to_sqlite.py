import pandas as pd
import sqlite3
import os

# Create database directory if it doesn't exist
os.makedirs('database', exist_ok=True)

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('database/fan_weights.db')
cursor = conn.cursor()

# Load data from Excel
excel_file = 'FanWeights.xlsx'

# Define sheet names and corresponding table names with their column mappings
sheets_to_tables = {
    'FanWeights': {
        'table': 'FanWeights',
        'columns': {
            'Fan Model': 'Fan Model',
            'Fan Size': 'Fan Size',
            'Class': 'Class',
            'Arrangement': 'Arrangement',
            'Bare Fan Weight': 'Bare Fan Weight',
            'Unitary Base Frame': 'Unitary Base Frame',
            'Isolation Base Frame': 'Isolation Base Frame',
            'Split Casing': 'Split Casing',
            'Inlet Companion Flange': 'Inlet Companion Flange',
            'Outlet Companion Flange': 'Outlet Companion Flange',
            'Inlet Butterfly Damper': 'Inlet Butterfly Damper',
            'No. of Isolators': 'No. of Isolators',
            'Shaft Dia': 'Shaft Dia'
        }
    },
    'VendorWeightDetails': {
        'table': 'VendorWeightDetails',
        'columns': {
            'Vendor': 'Vendor',
            'WeightStart': 'WeightStart',
            'WeightEnd': 'WeightEnd',
            'MSPrice': 'MSPrice',
            'SS304Price': 'SS304Price'
        }
    },
    'BearingLookup': {
        'table': 'BearingLookup',
        'columns': {
            'Brand': 'Brand',
            'Shaft Dia': 'Shaft Dia',
            'Description': 'Description',
            'Bearing': 'Bearing',
            'Plummer block': 'Plummer block',
            'Sleeve': 'Sleeve',
            'Total': 'Total'
        }
    },
    'DrivePackLookup': {
        'table': 'DrivePackLookup',
        'columns': {
            'Motor kW': 'Motor kW',
            'Drive Pack': 'Drive Pack'
        }
    },
    'MotorPrices': {
        'table': 'MotorPrices',
        'columns': {
            'Motor kW': 'Motor kW',
            'Pole': 'Pole',
            'Brand': 'Brand',
            'Efficiency': 'Efficiency',
            'List Price': 'List Price'
        }
    }
}

print("Starting data import...")

# Loop through each sheet and insert data into the corresponding table
for sheet_name, config in sheets_to_tables.items():
    try:
        print(f"\nProcessing sheet '{sheet_name}'...")
        # Read the Excel sheet into a pandas DataFrame
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        print(f"Found {len(df)} rows in {sheet_name}")

        # Rename columns according to mapping
        df = df.rename(columns=config['columns'])

        # Replace blank cells with NULL (NaN in pandas)
        df = df.where(pd.notnull(df), None)

        # Insert data into the SQLite table
        df.to_sql(config['table'], conn, if_exists='replace', index=False)
        print(f"Data from sheet '{sheet_name}' imported into table '{config['table']}'")
        
        # Verify the import
        cursor.execute(f"SELECT COUNT(*) FROM {config['table']}")
        count = cursor.fetchone()[0]
        print(f"Verified {count} rows in table {config['table']}")

        # Show first row as sample
        cursor.execute(f"SELECT * FROM {config['table']} LIMIT 1")
        row = cursor.fetchone()
        if row:
            print("\nSample row:")
            print(row)

    except Exception as e:
        print(f"Error processing sheet {sheet_name}: {str(e)}")

# Commit changes and close the connection
conn.commit()
conn.close()

print("\nAll data import completed!")