import sqlite3

def print_table_info(cursor, table_name):
    print(f"\n{'='*50}")
    print(f"Table: {table_name}")
    print('='*50)
    
    # Get schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print("\nColumns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Get sample data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
    rows = cursor.fetchall()
    print("\nSample data (first 3 rows):")
    for row in rows:
        print(row)
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\nTotal rows: {count}")

try:
    conn = sqlite3.connect('database/fan_weights.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    # Print info for each table
    for table in tables:
        table_name = table[0]
        print_table_info(cursor, table_name)
    
    conn.close()
except Exception as e:
    print("Error:", str(e)) 