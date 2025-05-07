import sqlite3

def check_motor_prices():
    # Check first database
    print("\n=== Checking MotorPrices in fan_pricing.db ===")
    conn = sqlite3.connect('fan_pricing.db')
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute('PRAGMA table_info(MotorPrices)')
    columns = [col[1] for col in cursor.fetchall()]
    print("Columns:", columns)
    
    # Get row count
    cursor.execute('SELECT COUNT(*) FROM MotorPrices')
    count = cursor.fetchone()[0]
    print(f"\nTotal rows: {count}")
    
    # Get sample data
    print("\nSample rows:")
    cursor.execute('SELECT * FROM MotorPrices ORDER BY Brand, "Motor kW", Pole LIMIT 10')
    rows = cursor.fetchall()
    for row in rows:
        print(dict(zip(columns, row)))
    
    # Get unique brands
    cursor.execute('SELECT DISTINCT Brand FROM MotorPrices ORDER BY Brand')
    brands = cursor.fetchall()
    print("\nUnique brands:", [b[0] for b in brands])
    
    # Get kW range
    cursor.execute('SELECT MIN("Motor kW"), MAX("Motor kW") FROM MotorPrices')
    min_kw, max_kw = cursor.fetchone()
    print(f"\nMotor kW range: {min_kw} to {max_kw}")
    
    conn.close()
    
    # Check second database
    print("\n=== Checking MotorPrices in database/fan_weights.db ===")
    conn = sqlite3.connect('database/fan_weights.db')
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute('PRAGMA table_info(MotorPrices)')
    columns = [col[1] for col in cursor.fetchall()]
    print("Columns:", columns)
    
    # Get row count
    cursor.execute('SELECT COUNT(*) FROM MotorPrices')
    count = cursor.fetchone()[0]
    print(f"\nTotal rows: {count}")
    
    # Get sample data
    print("\nSample rows:")
    cursor.execute('SELECT * FROM MotorPrices ORDER BY Brand, "Motor kW", Pole LIMIT 10')
    rows = cursor.fetchall()
    for row in rows:
        print(dict(zip(columns, row)))
    
    # Get unique brands
    cursor.execute('SELECT DISTINCT Brand FROM MotorPrices ORDER BY Brand')
    brands = cursor.fetchall()
    print("\nUnique brands:", [b[0] for b in brands])
    
    # Get kW range
    cursor.execute('SELECT MIN("Motor kW"), MAX("Motor kW") FROM MotorPrices')
    min_kw, max_kw = cursor.fetchone()
    print(f"\nMotor kW range: {min_kw} to {max_kw}")
    
    conn.close()

if __name__ == "__main__":
    check_motor_prices() 