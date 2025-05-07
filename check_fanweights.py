import sqlite3

try:
    # Connect to database
    conn = sqlite3.connect('database/fan_weights.db')
    cursor = conn.cursor()
    
    # Get schema of FanWeights table
    cursor.execute("PRAGMA table_info(FanWeights)")
    columns = cursor.fetchall()
    print("\nFanWeights table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Get first few rows of data
    cursor.execute("SELECT * FROM FanWeights LIMIT 5")
    rows = cursor.fetchall()
    print("\nFirst 5 rows of FanWeights:")
    for row in rows:
        print(row)
    
    conn.close()
except Exception as e:
    print("Error:", str(e)) 