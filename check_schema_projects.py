import sqlite3
conn = sqlite3.connect("fan_pricing.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(Projects)")
cols = cursor.fetchall()
for c in cols:
    print(c)
conn.close()
