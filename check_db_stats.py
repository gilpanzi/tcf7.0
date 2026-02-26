import sqlite3
import datetime
import os

def check_db():
    db_path = os.path.join('data', 'fan_pricing.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Let's find customers whose FIRST activity (enquiry or order) was in Jan 2026
    # This might be a better definition of "New" if the database is historical.
    
    target_months = [('2026', 'January'), ('2026', 'February')]
    
    for year, month in target_months:
        print(f"\nAnalyzing {month} {year}:")
        
        # Customers whose first enquiry or order is in this month
        cursor.execute('''
            SELECT COUNT(DISTINCT customer_id) FROM (
                SELECT customer_id, year, month FROM EnquiryRegister
                UNION ALL
                SELECT customer_id, year, month FROM Orders
            ) t1
            WHERE year = ? AND month = ?
            AND customer_id NOT IN (
                SELECT customer_id FROM (
                    SELECT customer_id, year, month FROM EnquiryRegister
                    UNION ALL
                    SELECT customer_id, year, month FROM Orders
                ) t2
                WHERE CAST(year AS INTEGER) < ? OR (CAST(year AS INTEGER) = ? AND 
                    CASE month 
                        WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 
                        WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 
                        WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 
                        WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 
                        ELSE 0 END < (CASE ? WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 
                                            WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 
                                            WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 
                                            WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 ELSE 0 END)
                )
            )
        ''', (year, month, int(year), int(year), month))
        count = cursor.fetchone()[0]
        print(f"New Customers (First Activity in {month} {year}): {count}")

    conn.close()

if __name__ == '__main__':
    check_db()
