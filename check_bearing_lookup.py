import sqlite3
from tabulate import tabulate

def check_bearing_lookup():
    conn = sqlite3.connect('database/fan_weights.db')
    cursor = conn.cursor()
    
    print("Checking BearingLookup table...")
    
    # Get column names
    cursor.execute('PRAGMA table_info(BearingLookup)')
    columns = [col[1] for col in cursor.fetchall()]
    print("\nColumns:", columns)
    
    # Get row count
    cursor.execute('SELECT COUNT(*) FROM BearingLookup')
    count = cursor.fetchone()[0]
    print(f"Total rows: {count}")
    
    # Get all data
    cursor.execute('''
        SELECT Brand, "Shaft Diameter", Description, 
               Bearing, "Plummer block", Sleeve, Total
        FROM BearingLookup 
        ORDER BY Brand, "Shaft Diameter"
    ''')
    rows = cursor.fetchall()
    
    # Format data for tabulate
    table_data = []
    for row in rows:
        formatted_row = [
            row[0],  # Brand
            row[1],  # Shaft Diameter
            row[2],  # Description
            f"₹{row[3]:,.2f}" if row[3] else None,  # Bearing
            f"₹{row[4]:,.2f}" if row[4] else None,  # Plummer block
            row[5],  # Sleeve
            f"₹{row[6]:,.2f}" if row[6] else None   # Total
        ]
        table_data.append(formatted_row)
    
    print("\nAll rows:")
    print(tabulate(table_data, 
                  headers=['Brand', 'Shaft Dia', 'Description', 'Bearing', 
                          'Plummer Block', 'Sleeve', 'Total'],
                  tablefmt='grid'))
    
    # Check for potential issues
    print("\nChecking for potential issues:")
    
    # Check for NULL values
    cursor.execute('''
        SELECT Brand, "Shaft Diameter",
               CASE WHEN Description IS NULL THEN 1 ELSE 0 END +
               CASE WHEN Bearing IS NULL THEN 1 ELSE 0 END +
               CASE WHEN "Plummer block" IS NULL THEN 1 ELSE 0 END +
               CASE WHEN Sleeve IS NULL THEN 1 ELSE 0 END +
               CASE WHEN Total IS NULL THEN 1 ELSE 0 END as null_count
        FROM BearingLookup
        WHERE Description IS NULL
           OR Bearing IS NULL
           OR "Plummer block" IS NULL
           OR Sleeve IS NULL
           OR Total IS NULL
    ''')
    null_rows = cursor.fetchall()
    
    if null_rows:
        print("\nRows with NULL values:")
        for row in null_rows:
            print(f"Brand: {row[0]}, Shaft Dia: {row[1]}, Number of NULL fields: {row[2]}")
    else:
        print("No NULL values found")
    
    # Check for total mismatch
    cursor.execute('''
        SELECT Brand, "Shaft Diameter", 
               Bearing, "Plummer block", Sleeve, Total,
               ROUND(COALESCE(Bearing, 0) + COALESCE("Plummer block", 0) + CAST(REPLACE(REPLACE(Sleeve, ',', ''), ' ', '') AS REAL), 2) as calculated_total
        FROM BearingLookup
        WHERE ABS(ROUND(COALESCE(Bearing, 0) + COALESCE("Plummer block", 0) + CAST(REPLACE(REPLACE(Sleeve, ',', ''), ' ', '') AS REAL), 2) - Total) > 0.01
    ''')
    mismatch_rows = cursor.fetchall()
    
    if mismatch_rows:
        print("\nRows with total mismatch:")
        for row in mismatch_rows:
            print(f"Brand: {row[0]}, Shaft Dia: {row[1]}")
            print(f"Bearing: ₹{row[2]:,.2f}, Plummer Block: ₹{row[3]:,.2f}, Sleeve: {row[4]}")
            print(f"Stored Total: ₹{row[5]:,.2f}, Calculated Total: ₹{row[6]:,.2f}")
    else:
        print("\nNo total mismatches found")
    
    conn.close()

if __name__ == "__main__":
    check_bearing_lookup() 