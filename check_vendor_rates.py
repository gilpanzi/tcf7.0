
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

try:
    conn = sqlite3.connect('fan_pricing.db')
    cursor = conn.cursor()
    
    vendor = "TCF Factory"
    material = "ms"
    
    check_query = 'SELECT * FROM VendorWeightDetails WHERE Vendor = ? AND Material = ? ORDER BY "Min Weight"'
    cursor.execute(check_query, (vendor, material))
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} entries for {vendor}/{material}:")
    for row in rows:
        print(row)
        
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
