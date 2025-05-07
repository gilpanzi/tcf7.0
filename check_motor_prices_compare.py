import sqlite3
import pandas as pd

def compare_motor_prices():
    print("\n=== Comparing MotorPrices tables in both databases ===\n")
    
    # Connect to both databases
    try:
        conn1 = sqlite3.connect('fan_pricing.db')
        conn2 = sqlite3.connect('database/fan_weights.db')
        
        # Get data from both tables
        df1 = pd.read_sql_query("SELECT * FROM MotorPrices ORDER BY Brand, 'Motor kW', Pole, Efficiency", conn1)
        df2 = pd.read_sql_query("SELECT * FROM MotorPrices ORDER BY Brand, 'Motor kW', Pole, Efficiency", conn2)
        
        # Print basic info
        print(f"fan_pricing.db - MotorPrices rows: {len(df1)}")
        print(f"fan_weights.db - MotorPrices rows: {len(df2)}\n")
        
        # Check structure
        print("Column comparison:")
        print(f"fan_pricing.db columns: {', '.join(df1.columns)}")
        print(f"fan_weights.db columns: {', '.join(df2.columns)}\n")
        
        # Sample data from the first database
        print("Sample data from fan_pricing.db (first 5 rows):")
        print(df1.head(5))
        print("\nSample data from fan_weights.db (first 5 rows):")
        print(df2.head(5))
        
        # Check for differences in values
        print("\nChecking for price differences between identical motors...")
        
        # Create a common key for comparison
        df1['key'] = df1['Brand'] + '_' + df1['Motor kW'].astype(str) + '_' + df1['Pole'].astype(str) + '_' + df1['Efficiency']
        df2['key'] = df2['Brand'] + '_' + df2['Motor kW'].astype(str) + '_' + df2['Pole'].astype(str) + '_' + df2['Efficiency']
        
        # Check for differences
        common_keys = set(df1['key']).intersection(set(df2['key']))
        
        if common_keys:
            diff_count = 0
            print("\nPrice differences (showing first 10):")
            for i, key in enumerate(common_keys):
                price1 = df1.loc[df1['key'] == key, 'Price'].values[0]
                price2 = df2.loc[df2['key'] == key, 'Price'].values[0]
                
                if price1 != price2:
                    diff_count += 1
                    if diff_count <= 10:  # Limit output to 10 differences
                        motor_data = key.split('_')
                        print(f"Motor: {motor_data[0]} {motor_data[1]}kW {motor_data[2]}-pole {motor_data[3]}")
                        print(f"  fan_pricing.db: ₹{price1}")
                        print(f"  fan_weights.db: ₹{price2}")
                        print(f"  Difference: ₹{price1 - price2}\n")
            
            print(f"Total motors with different prices: {diff_count} out of {len(common_keys)} common motors")
        else:
            print("No common motors found between the two databases")
        
        # Close connections
        conn1.close()
        conn2.close()
    
    except Exception as e:
        print(f"Error comparing databases: {str(e)}")

if __name__ == "__main__":
    compare_motor_prices() 