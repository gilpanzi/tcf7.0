import sqlite3

def check_data():
    conn = sqlite3.connect('database/fan_weights.db')
    cursor = conn.cursor()
    
    print("\nChecking all records with their class values:")
    cursor.execute('''
        SELECT "Fan Model", "Fan Size", "Class", "Arrangement" 
        FROM FanWeights 
        ORDER BY "Fan Model", "Fan Size", CAST("Class" AS INTEGER), "Arrangement"
    ''')
    records = cursor.fetchall()
    
    print("\nFan Model | Size | Class | Arrangement")
    print("-" * 40)
    for record in records:
        print(f"{record[0]:<10} | {record[1]:<5} | {record[2]:<5} | {record[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_data() 