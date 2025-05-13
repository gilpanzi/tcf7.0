import sqlite3
import os

def check_db_schema():
    """Check the database schema and compare column count with parameter count."""
    
    # Connect to the database
    data_dir = 'data'
    central_db_dir = os.path.join(data_dir, 'central_database')
    central_db_path = os.path.join(central_db_dir, 'all_projects.db')
    
    conn = sqlite3.connect(central_db_path)
    cursor = conn.cursor()
    
    # Get the ProjectFans table schema
    cursor.execute("PRAGMA table_info(ProjectFans)")
    cols = cursor.fetchall()
    
    # Print column names and info
    print(f"Total columns in ProjectFans table: {len(cols)}")
    
    # Print all columns separately
    for i, col in enumerate(cols):
        print(f"{i+1}. {col[1]} ({col[2]})")
    
    # Count the VALUES placeholders
    placeholders = "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    placeholder_count = placeholders.count('?')
    print(f"Number of placeholders in VALUES clause: {placeholder_count}")
    
    # Create the list of column names for comparison
    column_names = [col[1] for col in cols]
    print(f"The columns are: {column_names}")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    check_db_schema() 