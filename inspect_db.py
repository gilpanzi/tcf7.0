
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)


try:
    with open('inspect_result.txt', 'w') as f:
        conn = sqlite3.connect('fan_pricing.db')
        cursor = conn.cursor()
        
        f.write("--- FanWeights Schema ---\n")
        cursor.execute("PRAGMA table_info(FanWeights)")
        for col in cursor.fetchall():
            f.write(f"{col}\n")
            
        f.write("\n--- VendorWeightDetails Schema ---\n")
        cursor.execute("PRAGMA table_info(VendorWeightDetails)")
        for col in cursor.fetchall():
            f.write(f"{col}\n")

        f.write("\n--- Specific Fan Weight ---\n")
        # Check bare fan weight explicitly
        cursor.execute('SELECT "Bare Fan Weight" FROM FanWeights WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?', ('BC-SW', '270', 1, 1))
        row = cursor.fetchone()
        f.write(f"Bare Fan Weight for BC-SW/270/1/1: {row}\n")

        f.write("\n--- Vendor Rates (First 5) ---\n")
        cursor.execute("SELECT * FROM VendorWeightDetails LIMIT 5")
        for row in cursor.fetchall():
            f.write(f"{row}\n")

        conn.close()
    
except Exception as e:
    with open('inspect_result.txt', 'w') as f:
        f.write(f"Error: {e}\n")

