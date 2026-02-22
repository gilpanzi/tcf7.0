import sqlite3
import json

db_path = 'data/fan_pricing.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT costs FROM Fans WHERE costs IS NOT NULL AND costs != 'null' LIMIT 1")
row = cursor.fetchone()
if row:
    with open('check_costs.json', 'w') as f:
        json.dump(json.loads(row['costs']), f, indent=2)
conn.close()
