
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    conn = sqlite3.connect('fan_pricing.db')
    cursor = conn.cursor()
    
    # Check for the specific combination from user's payload
    # Payload: Fan Model: 'BC-SW', Fan Size: '270', Class: '1', Arrangement: '1'
    

    # Specific check for the user's failed request
    model = 'BC-SW'
    size = '270'
    cls = 1
    arr = 1
    
    print(f"Checking for Model='{model}', Size='{size}', Class={cls}, Arr={arr}")
    
    # Check with integers
    cursor.execute('SELECT * FROM FanWeights WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?', (model, size, cls, arr))
    row = cursor.fetchone()
    
    with open('result.txt', 'w') as f:
        if row:
            f.write(f"FOUND: {row}\n")
            print("FOUND")
            # Check column types in this row
            cursor.execute('SELECT typeof("Class"), typeof("Arrangement") FROM FanWeights WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?', (model, size, cls, arr))
            types = cursor.fetchone()
            print(f"Types: {types}")
            f.write(f"Types: {types}\n")
        else:
            f.write("NOT FOUND\n")
            print("NOT FOUND")
            
    conn.close()
    
except Exception as e:
    with open('result.txt', 'w') as f:
        f.write(f"ERROR: {e}\n")
    print(f"Error: {e}")

