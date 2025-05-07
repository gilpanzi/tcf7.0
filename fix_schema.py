import sqlite3
import os
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(db_path, 'rb') as source:
        with open(backup_path, 'wb') as target:
            target.write(source.read())
    print(f"Created backup at: {backup_path}")
    return backup_path

def fix_schema():
    """Fix database schema issues."""
    db_path = 'database/fan_weights.db'
    
    print(f"Fixing schema for database: {db_path}")
    
    # Create backup first
    backup_path = backup_database(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Fix BearingLookup table
        print("\nFixing BearingLookup table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS BearingLookup_new (
                "Brand" TEXT NOT NULL,
                "Shaft Diameter" INTEGER NOT NULL,
                "Description" TEXT NOT NULL,
                "Bearing" REAL NOT NULL,
                "Plummer block" REAL NOT NULL,
                "Sleeve" TEXT NOT NULL,
                "Total" REAL NOT NULL,
                PRIMARY KEY ("Brand", "Shaft Diameter")
            )
        ''')
        
        # Insert the correct bearing data
        bearing_data = [
            # (Brand, Shaft Diameter, Description, Bearing, Plummer block, Sleeve, Total)
            ('SKF', 35, '22222-EKC3', 25819.00, 8939.00, '2880.15', 37638.15),
            ('SKF', 40, '22224-EKC3', 31983.00, 11171.00, '3600.19', 46754.19),
            ('SKF', 45, '22226-EKC3', 39978.00, 13964.00, '4500.24', 58442.24),
            ('SKF', 50, '22228-EKC3', 49973.00, 17455.00, '5625.30', 73053.30),
            ('NTN', 35, '22230-EKC3', 20648.00, 14450.00, '4000.00', 39098.00),
            ('NTN', 40, '22232-EKC3', 25810.00, 18062.00, '5000.00', 48872.00),
            ('NTN', 45, '22234-EKC3', 32262.00, 22578.00, '6250.00', 61090.00),
            ('NTN', 50, '22236-EKC3', 40328.00, 28222.00, '7812.50', 76362.50)
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO BearingLookup_new 
            ("Brand", "Shaft Diameter", "Description", "Bearing", "Plummer block", "Sleeve", "Total")
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', bearing_data)
        
        cursor.execute('DROP TABLE IF EXISTS BearingLookup')
        cursor.execute('ALTER TABLE BearingLookup_new RENAME TO BearingLookup')
        
        # 2. Fix DrivePackLookup table
        print("\nFixing DrivePackLookup table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DrivePackLookup_new (
                "Motor kW" REAL NOT NULL PRIMARY KEY,
                "Drive Pack" INTEGER NOT NULL
            )
        ''')
        
        # Insert the exact values from the image
        drive_pack_data = [
            (0.75, 2500),
            (1.125, 2500),
            (1.5, 3000),
            (2.2, 3000),
            (3.7, 3000),
            (5.5, 4000),
            (7.5, 4000),
            (9.3, 6000),
            (11.0, 6000),
            (15.0, 8000),
            (18.5, 8000),
            (22.0, 9000),
            (30.0, 15000),
            (37.0, 15000),
            (45.0, 28000),
            (55.0, 28000),
            (75.0, 35000),
            (90.0, 39000),
            (110.0, 48750),
            (132.0, 58500),
            (160.0, 69875),
            (180.0, 78000),
            (200.0, 87750),
            (225.0, 97500)
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO DrivePackLookup_new ("Motor kW", "Drive Pack")
            VALUES (?, ?)
        ''', drive_pack_data)
        
        cursor.execute('DROP TABLE IF EXISTS DrivePackLookup')
        cursor.execute('ALTER TABLE DrivePackLookup_new RENAME TO DrivePackLookup')
        
        # 3. Fix MotorPrices table
        print("\nFixing MotorPrices table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS MotorPrices_new (
                "Brand" TEXT NOT NULL,
                "Motor kW" REAL NOT NULL,
                "Pole" INTEGER NOT NULL,
                "Efficiency" TEXT NOT NULL,
                "Price" REAL NOT NULL,
                PRIMARY KEY ("Brand", "Motor kW", "Pole", "Efficiency")
            )
        ''')
        
        # Clean and insert data, handling any formatting issues
        cursor.execute('''
            INSERT INTO MotorPrices_new
            SELECT 
                TRIM(Brand) as Brand,
                ROUND(CAST(REPLACE(REPLACE("Motor kW", ' ', ''), ',', '.') AS REAL), 2) as "Motor kW",
                CAST(TRIM(Pole) AS INTEGER) as Pole,
                TRIM(Efficiency) as Efficiency,
                ROUND(CAST(REPLACE(REPLACE(Price, ' ', ''), ',', '.') AS REAL), 2) as Price
            FROM (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY Brand, "Motor kW", Pole, Efficiency
                    ORDER BY rowid DESC
                ) as rn
                FROM MotorPrices
                WHERE Brand IS NOT NULL 
                AND "Motor kW" IS NOT NULL 
                AND Pole IS NOT NULL 
                AND Efficiency IS NOT NULL
                AND Price IS NOT NULL
            ) tmp
            WHERE rn = 1
            AND CAST(TRIM(Pole) AS INTEGER) > 0
            AND CAST(REPLACE(REPLACE("Motor kW", ' ', ''), ',', '.') AS REAL) > 0
            AND CAST(REPLACE(REPLACE(Price, ' ', ''), ',', '.') AS REAL) > 0
        ''')
        
        cursor.execute('DROP TABLE IF EXISTS MotorPrices')
        cursor.execute('ALTER TABLE MotorPrices_new RENAME TO MotorPrices')
        
        # 4. Fix EnquiryFans table
        print("\nFixing EnquiryFans table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EnquiryFans_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_number TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                fan_number INTEGER NOT NULL,
                specifications TEXT NOT NULL,
                accessories TEXT NOT NULL,
                vendor TEXT,
                material TEXT,
                vibration_isolators TEXT,
                motor_brand TEXT,
                motor_kw REAL,
                motor_pole INTEGER,
                motor_efficiency TEXT,
                fabrication_margin REAL,
                bought_out_margin REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO EnquiryFans_new
            SELECT id,
                   enquiry_number,
                   customer_name,
                   fan_number,
                   specifications,
                   accessories,
                   vendor,
                   material,
                   vibration_isolators,
                   motor_brand,
                   CAST(NULLIF(motor_kw, '') AS REAL) as motor_kw,
                   CAST(NULLIF(motor_pole, '') AS INTEGER) as motor_pole,
                   motor_efficiency,
                   fabrication_margin,
                   bought_out_margin,
                   created_at
            FROM EnquiryFans
        ''')
        
        cursor.execute('DROP TABLE IF EXISTS EnquiryFans')
        cursor.execute('ALTER TABLE EnquiryFans_new RENAME TO EnquiryFans')
        
        # 5. Remove unnecessary tables
        print("\nRemoving unnecessary tables...")
        cursor.execute('DROP TABLE IF EXISTS AccessoryWeights')
        cursor.execute('DROP TABLE IF EXISTS OptionalItems')
        
        conn.commit()
        print("\nSchema fixes completed successfully")
        
    except Exception as e:
        print(f"Error during schema fix: {str(e)}")
        print(f"You can restore from backup: {backup_path}")
        if 'conn' in locals():
            conn.close()
        return
    
    conn.close()
    print(f"\nDatabase updated successfully. Old version backed up at: {backup_path}")

if __name__ == "__main__":
    fix_schema() 