import sqlite3
import os

db_path = os.path.join("data", "fan_pricing.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

query = """
SELECT r.enquiry_number, r.year, p.status as pricing_status, 
(SELECT SUM(CAST(json_extract(f.costs, "$.total_selling_price") AS REAL)) FROM Fans f WHERE f.project_id = p.id) as total_value
FROM EnquiryRegister r 
LEFT JOIN Projects p ON r.enquiry_number = p.enquiry_number
"""
cursor.execute(query)
rows = cursor.fetchall()
matches = 0
total = 0
priced_val = 0
for r in rows:
    total += 1
    if r['pricing_status']:
        matches += 1
        priced_val += (r['total_value'] or 0)

print(f"Total Enquiries in Register: {total}")
print(f"Enquiries with Project match: {matches}")
print(f"Total Priced Value: {priced_val}")

cursor.execute("SELECT enquiry_number FROM Projects LIMIT 10")
print("\nSample Enquiry Numbers in Projects:")
for r in cursor.fetchall():
    print(f"'{r[0]}'")

cursor.execute("SELECT enquiry_number FROM EnquiryRegister LIMIT 10")
print("\nSample Enquiry Numbers in Register:")
for r in cursor.fetchall():
    print(f"'{r[0]}'")

conn.close()
