import sqlite3
from tabulate import tabulate

def check_drive_pack():
    conn = sqlite3.connect('database/fan_weights.db')
    cursor = conn.cursor()
    
    print("Checking DrivePackLookup table...")
    
    # Get column names
    cursor.execute('PRAGMA table_info(DrivePackLookup)')
    columns = [col[1] for col in cursor.fetchall()]
    print("\nColumns:", columns)
    
    # Get row count
    cursor.execute('SELECT COUNT(*) FROM DrivePackLookup')
    count = cursor.fetchone()[0]
    print(f"Total rows: {count}")
    
    # Get all data
    cursor.execute('SELECT * FROM DrivePackLookup ORDER BY "Motor kW"')
    rows = cursor.fetchall()
    
    # Format data for tabulate
    table_data = [[row[0], f"₹{row[1]:,}"] for row in rows]
    print("\nAll rows:")
    print(tabulate(table_data, headers=['Motor kW', 'Drive Pack (₹)'], 
                  tablefmt='grid', floatfmt='.3f'))
    
    # Get kW range
    cursor.execute('SELECT MIN("Motor kW"), MAX("Motor kW") FROM DrivePackLookup')
    min_kw, max_kw = cursor.fetchone()
    print(f"\nMotor kW range: {min_kw} to {max_kw}")
    
    # Verify expected values
    expected_kw = [0.75, 1.125, 1.5, 2.2, 3.7, 5.5, 7.5, 9.3, 11.0, 15.0, 
                  18.5, 22.0, 30.0, 37.0, 45.0, 55.0, 75.0, 90.0, 110.0, 
                  132.0, 160.0, 180.0, 200.0, 225.0]
    
    actual_kw = [row[0] for row in rows]
    missing_kw = [kw for kw in expected_kw if kw not in actual_kw]
    
    if missing_kw:
        print("\nMISSING kW values:", missing_kw)
    else:
        print("\nAll expected kW values are present")
    
    conn.close()

if __name__ == "__main__":
    check_drive_pack() 