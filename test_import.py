import sys
import os

# Add current directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import import_orders_from_excel, migrate_to_unified_schema

print("Migrating schema to redefine Orders table...")
migrate_to_unified_schema()

excel_path = r"C:\Basidh\tcf7.0\tcf7.0\TCF SALES MASTER DATA FILE.xlsx"

try:
    with open(excel_path, 'rb') as f:
        print("Importing orders from excel...")
        success = import_orders_from_excel(f)
        if success:
            print("Successfully imported orders!")
        else:
            print("Failed to import orders.")
except Exception as e:
    print(f"Error: {e}")
