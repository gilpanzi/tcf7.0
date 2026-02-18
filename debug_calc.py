
import sqlite3
import logging
from calculations import calculate_fabrication_cost

# Setup logging to console
logging.basicConfig(level=logging.INFO)

def test_calculation_logic():
    # Mock cursor and data
    # We need a real DB connection or a mock that returns price
    # Let's use the actual DB
    conn = sqlite3.connect('database.db') # Assuming database.db is in current dir
    cursor = conn.cursor()
    
    # Mock fan data
    fan_data = {
        'fan_model': 'BC-SW',
        'material': 'ms',
        'vendor_rate': "0.00", # The problematic input
        'vendor': 'TCF Factory' # Assuming this vendor exists and has rates
    }
    
    total_weight = 100 # Arbitrary weight to find price
    
    print("--- Running calculate_fabrication_cost ---")
    result = calculate_fabrication_cost(cursor, fan_data, total_weight)
    print(f"Raw Result Type: {type(result)}")
    print(f"Raw Result: {result}")
    
    if result and isinstance(result, tuple) and len(result) == 5:
        cost, weight, custom_weights, rate_used, error = result
        print(f"Result: Cost={cost}, RateUsed={rate_used}, Error={error}")
        
        if rate_used and rate_used > 0:
            print("SUCCESS: Rate used is positive.")
        else:
            print("FAILURE: Rate used is 0 or None.")
    else:
        print("FAILURE: Invalid return format.")

    conn.close()

if __name__ == "__main__":
    test_calculation_logic()
