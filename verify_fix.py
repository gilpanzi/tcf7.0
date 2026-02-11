
import sqlite3
import logging
import sys
import os

# Add current directory to path to import calculations
sys.path.append(os.getcwd())

from calculations import calculate_fabrication_cost

logging.basicConfig(level=logging.INFO)

try:
    conn = sqlite3.connect('fan_pricing.db')
    cursor = conn.cursor()
    
    # Test data based on user's fail case
    # Material: ms
    # Vendor: TCF Factory
    # Weight: 60.0 (Assumed from previous findings, or use a value known to be in DB)
    
    # Check what weight range is valid first
    cursor.execute('SELECT * FROM VendorWeightDetails WHERE Vendor="TCF Factory" LIMIT 1')
    row = cursor.fetchone()
    print(f"Sample Vendor Row: {row}")
    # Row: (Vendor, Start, End, MSPrice, SS304Price)
    # e.g. ('TCF Factory', 0, 100, 200, 500)
    
    test_weight = 50.0 # Should be in first range usually
    
    fan_data = {
        'vendor': 'TCF Factory',
        'material': 'ms',
        'vendor_rate': None # Standard case
    }
    
    print(f"\n--- Testing calculate_fabrication_cost with Weight={test_weight} ---")
    cost, weight, details, error = calculate_fabrication_cost(cursor, fan_data, test_weight)
    
    if error:
        print(f"FAILED: {error}")
    else:
        print(f"SUCCESS: Cost={cost}")
        
    # Test Mixed Material
    print(f"\n--- Testing Mixed Material (50% MS) ---")
    fan_data['material'] = 'mixed'
    fan_data['ms_percentage'] = 50
    
    cost, weight, details, error = calculate_fabrication_cost(cursor, fan_data, test_weight)
    
    if error:
        print(f"FAILED Mixed: {error}")
    else:
        print(f"SUCCESS Mixed: Cost={cost}")

    conn.close()
    
except Exception as e:
    print(f"Error during verification: {e}")
    import traceback
    traceback.print_exc()
