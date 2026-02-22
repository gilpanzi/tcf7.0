import sqlite3

def check_schema():
    try:
        conn = sqlite3.connect('data/fan_pricing.db')
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute('PRAGMA table_info(FanWeights)')
        columns = cursor.fetchall()
        
        print("\nFanWeights table schema:")
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}")
        
        # Get sample data
        cursor.execute('SELECT * FROM FanWeights LIMIT 1')
        row = cursor.fetchone()
        if row:
            print("\nSample row:")
            for i, col in enumerate(columns):
                print(f"{col[1]}: {row[i]}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    check_schema() 