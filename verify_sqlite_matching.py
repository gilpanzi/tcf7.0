
import sqlite3
import os

# Create a temporary db
if os.path.exists('test_types.db'):
    os.remove('test_types.db')

conn = sqlite3.connect('test_types.db')
cursor = conn.cursor()

cursor.execute('CREATE TABLE Test (id INTEGER PRIMARY KEY, val INTEGER, text_val TEXT)')
cursor.execute('INSERT INTO Test (val, text_val) VALUES (1, "1")')
conn.commit()

print("Testing integer column matches key...")

# Match int with int
cursor.execute('SELECT * FROM Test WHERE val = ?', (1,))
row = cursor.fetchone()
print(f"Int 1 vs Int 1: {'Found' if row else 'Not Found'}")

# Match int with str
cursor.execute('SELECT * FROM Test WHERE val = ?', ("1",))
row = cursor.fetchone()
print(f"Int 1 vs Str '1': {'Found' if row else 'Not Found'}")

print("\nTesting text column matches key...")

# Match text with str
cursor.execute('SELECT * FROM Test WHERE text_val = ?', ("1",))
row = cursor.fetchone()
print(f"Text '1' vs Str '1': {'Found' if row else 'Not Found'}")

# Match text with int
cursor.execute('SELECT * FROM Test WHERE text_val = ?', (1,))
row = cursor.fetchone()
print(f"Text '1' vs Int 1: {'Found' if row else 'Not Found'}")

conn.close()
os.remove('test_types.db')
