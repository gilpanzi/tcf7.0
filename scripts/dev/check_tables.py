import sqlite3

def check_tables():
    conn = sqlite3.connect('fan_pricing.db')
    cursor = conn.cursor()
    
    # Check for Tables table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("Tables in database:", tables)
    
    # Check if Projects and ProjectFans exist
    if 'Projects' in tables and 'ProjectFans' in tables:
        print("Projects and ProjectFans tables exist!")
        
        # Check Projects table structure
        cursor.execute("PRAGMA table_info(Projects)")
        print("\nProjects table columns:")
        for column in cursor.fetchall():
            print(f"  {column[1]} ({column[2]})")
            
        # Check ProjectFans table structure
        cursor.execute("PRAGMA table_info(ProjectFans)")
        print("\nProjectFans table columns:")
        for column in cursor.fetchall():
            print(f"  {column[1]} ({column[2]})")
    else:
        if 'Projects' not in tables:
            print("Projects table does not exist!")
        if 'ProjectFans' not in tables:
            print("ProjectFans table does not exist!")
    
    conn.close()

if __name__ == "__main__":
    check_tables() 