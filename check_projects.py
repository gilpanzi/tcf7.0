import sqlite3
import os

db_path = os.path.join("data", "fan_pricing.db")
if not os.path.exists(db_path):
    print(f"DB not found: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Projects LIMIT 5")
    rows = cursor.fetchall()
    print("Projects Sample:")
    for r in rows:
        print(dict(r))
    
    cursor.execute("SELECT DISTINCT status FROM Projects")
    statuses = cursor.fetchall()
    print("\nDistinct Statuses in Projects:")
    for s in statuses:
        print(s[0])
    
    conn.close()
