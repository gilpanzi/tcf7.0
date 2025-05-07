import sqlite3
import os

# Print current directory and check if database file exists
print("Current directory:", os.getcwd())
print("Database file exists:", os.path.exists('database/fan_weights.db'))

def check_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('database/fan_weights.db')
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:", [table[0] for table in tables])
        
        # Check FanWeights table
        cursor.execute("SELECT * FROM FanWeights LIMIT 1;")
        columns = [description[0] for description in cursor.description]
        print("\nFanWeights columns:", columns)
        
        # Check specific fan model
        cursor.execute('''
            SELECT * FROM FanWeights 
            WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
        ''', ("BC-SW", "122", "II", 4))
        row = cursor.fetchone()
        print("\nMatching fan model:", row)
        
        conn.close()
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    check_database() 