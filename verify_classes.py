import sqlite3

def verify_classes():
    conn = sqlite3.connect('database/fan_weights.db')
    cursor = conn.cursor()
    
    print("Checking current class values in the database:")
    cursor.execute('SELECT DISTINCT "Class" FROM FanWeights ORDER BY CAST("Class" AS INTEGER)')
    classes = cursor.fetchall()
    
    print("\nUnique Class values found:")
    for class_value in classes:
        print(f"- {class_value[0]}")
    
    conn.close()

if __name__ == "__main__":
    verify_classes() 