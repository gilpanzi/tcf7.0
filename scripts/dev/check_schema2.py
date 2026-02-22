import sqlite3
import pprint
conn = sqlite3.connect('data/fan_pricing.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Projects';")
res = cursor.fetchone()
if res:
    print(res[0])
    cursor.execute("PRAGMA index_list('Projects');")
    print("Indexes:", cursor.fetchall())
else:
    print("Table Projects not found")
