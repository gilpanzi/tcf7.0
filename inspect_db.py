
import sqlite3
import json
import os
import sys

def inspect_fan_data():
    db_path = os.path.join('data', 'fan_pricing.db')
    output_file = 'db_inspection_results.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Checking database at: {os.path.abspath(db_path)}\n")
        
        if not os.path.exists(db_path):
            f.write(f"Database not found at {db_path}\n")
            return

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            f.write(f"Tables in DB: {[t['name'] for t in tables]}\n")

            if 'Fans' not in [t['name'] for t in tables]:
                f.write("Fans table not found!\n")
                return

            f.write("\n--- Inspecting Fans Table ---\n")
            cursor.execute("SELECT id, project_id, fan_number, specifications FROM Fans")
            fans = cursor.fetchall()

            if not fans:
                f.write("No fans found in database.\n")
            
            for fan in fans:
                f.write(f"\nFan ID: {fan['id']}, Project ID: {fan['project_id']}, Fan #: {fan['fan_number']}\n")
                try:
                    specs = json.loads(fan['specifications'])
                    if not specs:
                        f.write("  Specifications is empty or None\n")
                    else:
                        f.write(f"  Fan Model: '{specs.get('Fan Model')}'\n")
                        f.write(f"  fan_model (lowercase): '{specs.get('fan_model')}'\n")
                        f.write(f"  Fan Size: '{specs.get('Fan Size')}'\n")
                        f.write(f"  All Spec Keys: {list(specs.keys())}\n")
                except json.JSONDecodeError:
                    f.write(f"  Error decoding specifications JSON: {fan['specifications']}\n")
                except Exception as e:
                    f.write(f"  Error parsing specs: {e}\n")

            conn.close()

        except Exception as e:
            f.write(f"Database error: {e}\n")

if __name__ == "__main__":
    inspect_fan_data()
