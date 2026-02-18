
import sqlite3
import json
import os

def check_latest_fan_detailed():
    db_path = 'data/fan_pricing.db'
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get latest project
    cursor.execute("SELECT id, enquiry_number, updated_at FROM Projects ORDER BY updated_at DESC LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        print("No projects found.")
        return
        
    pid, enq, updated = row
    print(f"Latest Project: {enq} (ID: {pid}, Updated: {updated})")
    
    # Get fans for this project
    cursor.execute("SELECT fan_number, specifications FROM Fans WHERE project_id = ?", (pid,))
    fans = cursor.fetchall()
    
    print(f"  Fans count: {len(fans)}")
    
    for i, (fnum, raw_specs) in enumerate(fans):
        try:
            specs = json.loads(raw_specs) if raw_specs else {}
            print(f"  --- Fan {fnum} Specs ---")
            for k, v in specs.items():
                print(f"    '{k}': '{v}'")
        except Exception as e:
            print(f"    Error parsing JSON for fan {fnum}: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_latest_fan_detailed()
