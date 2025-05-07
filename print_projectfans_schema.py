import sqlite3

DB_PATH = 'data/central_database/all_projects.db'

def print_projectfans_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ProjectFans)")
    columns = cursor.fetchall()
    print(f"ProjectFans table has {len(columns)} columns:")
    for col in columns:
        print(f"{col[0]:2}: {col[1]:30} {col[2]}")
    conn.close()

if __name__ == "__main__":
    print_projectfans_schema() 