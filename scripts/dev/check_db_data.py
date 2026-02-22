import sqlite3

def check_fan_data():
    conn = sqlite3.connect('fan_weights.db')
    cursor = conn.cursor()
    
    # Get fan models and sizes
    cursor.execute('SELECT DISTINCT "Fan Model", "Fan Size" FROM FanWeights ORDER BY "Fan Model", "Fan Size"')
    rows = cursor.fetchall()
    
    print("\nFan Models and Sizes:")
    current_model = None
    for row in rows:
        model, size = row
        if model != current_model:
            print(f"\nModel: {model}")
            current_model = model
        print(f"  Size: {size}")
    
    # Get a sample row with all columns
    cursor.execute('SELECT * FROM FanWeights LIMIT 1')
    row = cursor.fetchone()
    cursor.execute('PRAGMA table_info(FanWeights)')
    columns = cursor.fetchall()
    
    print("\nSample Row:")
    for i, col in enumerate(columns):
        print(f"{col[1]}: {row[i]}")
    
    conn.close()

if __name__ == "__main__":
    check_fan_data() 