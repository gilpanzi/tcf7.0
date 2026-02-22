import sqlite3
from database import get_db_connection

def list_columns():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = ["FanWeights", "BearingLookup", "DrivePackLookup", "MotorPrices"]
        for table in tables:
            print(f"\n--- {table} Columns ---")
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                for col in columns:
                    print(col[1])
            except Exception as e:
                print(f"Error reading {table}: {e}")
                
    except Exception as e:
        print(f"Error connecting to DB: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    list_columns()
