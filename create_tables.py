import sqlite3
import os

def create_tables():
    # Read SQL script
    with open('database/create_tables.sql', 'r') as f:
        sql_script = f.read()
    
    # Connect to database
    db_path = 'database/fan_weights.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop existing MotorPrices table if it exists
        cursor.execute("DROP TABLE IF EXISTS MotorPrices")
        
        # Execute SQL script
        cursor.executescript(sql_script)
        conn.commit()
        print("Tables created and data inserted successfully!")
        
        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM MotorPrices")
        count = cursor.fetchone()[0]
        print(f"Total motor prices inserted: {count}")
        
        # Show sample data
        cursor.execute("""
            SELECT Brand, "Motor kW", Pole, Efficiency, Price
            FROM MotorPrices 
            WHERE Brand = 'ABB' AND Pole = 4 AND Efficiency = 'IE2'
            ORDER BY "Motor kW"
            LIMIT 5
        """)
        print("\nSample motor prices (ABB, 4-pole, IE2):")
        for row in cursor.fetchall():
            print(f"Brand: {row[0]}, KW: {row[1]}, Pole: {row[2]}, Efficiency: {row[3]}, Price: {int(row[4]):,}")
            
        # Show distribution of prices
        print("\nPrice distribution by brand and efficiency:")
        cursor.execute("""
            SELECT Brand, Efficiency, COUNT(*) as count,
                   MIN(Price) as min_price,
                   MAX(Price) as max_price,
                   ROUND(AVG(Price), 0) as avg_price
            FROM MotorPrices
            GROUP BY Brand, Efficiency
            ORDER BY Brand, Efficiency
        """)
        for row in cursor.fetchall():
            print(f"{row[0]} {row[1]}: {row[2]} motors, Price range: {int(row[3]):,} - {int(row[4]):,}, Avg: {int(row[5]):,}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    create_tables() 