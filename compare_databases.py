import sqlite3
import os

def get_schema(db_path):
    """Get schema information for a database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        schema_info = {}
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            
            # Get schema for each table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            schema_info[table_name] = {
                'columns': [(col[1], col[2]) for col in columns],  # name and type
                'row_count': row_count
            }
        
        conn.close()
        return schema_info
    except Exception as e:
        print(f"Error reading {db_path}: {str(e)}")
        return None

def compare_databases():
    """Compare the two database files."""
    db1_path = 'database/fan_weights.db'
    db2_path = 'fan_weights.db'
    
    print(f"Checking database files:")
    print(f"1. {db1_path} - Exists: {os.path.exists(db1_path)}")
    print(f"2. {db2_path} - Exists: {os.path.exists(db2_path)}")
    print()
    
    db1_schema = get_schema(db1_path)
    db2_schema = get_schema(db2_path)
    
    if not db1_schema or not db2_schema:
        print("Error: Could not read one or both databases")
        return
    
    print("Comparing schemas:")
    print("-" * 50)
    
    # Compare tables
    all_tables = set(db1_schema.keys()) | set(db2_schema.keys())
    
    for table in sorted(all_tables):
        print(f"\nTable: {table}")
        
        if table not in db1_schema:
            print(f"  Only exists in {db2_path}")
            continue
        elif table not in db2_schema:
            print(f"  Only exists in {db1_path}")
            continue
        
        # Compare columns
        db1_cols = dict(db1_schema[table]['columns'])
        db2_cols = dict(db2_schema[table]['columns'])
        
        all_cols = set(db1_cols.keys()) | set(db2_cols.keys())
        differences = []
        
        for col in sorted(all_cols):
            if col not in db1_cols:
                differences.append(f"Column {col} only in {db2_path}")
            elif col not in db2_cols:
                differences.append(f"Column {col} only in {db1_path}")
            elif db1_cols[col] != db2_cols[col]:
                differences.append(f"Column {col} type mismatch: {db1_cols[col]} vs {db2_cols[col]}")
        
        if differences:
            print("  Differences found:")
            for diff in differences:
                print(f"    {diff}")
        else:
            print("  Schema matches")
        
        # Compare row counts
        row_count1 = db1_schema[table]['row_count']
        row_count2 = db2_schema[table]['row_count']
        print(f"  Row counts: {db1_path}: {row_count1}, {db2_path}: {row_count2}")

if __name__ == "__main__":
    compare_databases() 