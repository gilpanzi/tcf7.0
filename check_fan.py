import sqlite3

def check_fan():
    try:
        # Connect to the database
        conn = sqlite3.connect('database/fan_weights.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check for the specific fan model
        cursor.execute('''
            SELECT * FROM FanWeights 
            WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?
        ''', ("BC-SW", "122", "II", 4))
        
        row = cursor.fetchone()
        if row:
            print("Fan found:")
            print(dict(row))
        else:
            print("Fan not found")
            
        # Show all fan models for reference
        print("\nAll available fan models:")
        cursor.execute('SELECT DISTINCT "Fan Model", "Fan Size", "Class", "Arrangement" FROM FanWeights')
        models = cursor.fetchall()
        for model in models:
            print(dict(model))
        
        conn.close()
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    check_fan() 