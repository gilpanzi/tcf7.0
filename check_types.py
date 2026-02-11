
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    conn = sqlite3.connect('fan_pricing.db')
    cursor = conn.cursor()
    
    # Check types for the specific row
    query = '''
    SELECT 
        typeof("Fan Model"), "Fan Model",
        typeof("Fan Size"), "Fan Size",
        typeof("Class"), "Class",
        typeof("Arrangement"), "Arrangement"
    FROM FanWeights 
    WHERE "Fan Model" = 'BC-SW' 
    AND "Fan Size" = '270'
    '''
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("No rows found for BC-SW size 270")
    else:
        for row in rows:
            print(f"Row: {row}")
            
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
