import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def create_bearing_lookup_table():
    """Create and populate the BearingLookup table with data."""
    try:
        # Standardize to data/ directory
        import os
        db_path = os.path.join('data', 'fan_pricing.db')
        os.makedirs('data', exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Connected to database")
        
        # Check if table exists and drop it if it does
        cursor.execute("DROP TABLE IF EXISTS BearingLookup")
        logger.info("Dropped existing BearingLookup table if it existed")
        
        # Create the table
        cursor.execute('''
        CREATE TABLE BearingLookup (
            Brand TEXT,
            ShaftDiameter INTEGER,
            Description TEXT,
            Bearing INTEGER,
            PlummerBlock REAL,
            Sleeve REAL,
            Total REAL
        )
        ''')
        logger.info("Created BearingLookup table")
        
        # SKF bearings data
        skf_data = [
            ('SKF', 0, '', 0, 0, 0, 0),
            ('SKF', 25, '22206-EKC3', 0, 631, 148, 6279),
            ('SKF', 30, '22207-EKC3', 5819, 1357.3, 234, 7410.3),
            ('SKF', 35, '22208-EKC3', 6290, 1446.2, 250.9, 7987.1),
            ('SKF', 40, '22209-EKC3', 6661, 1507.8, 273, 8441.8),
            ('SKF', 45, '22210-EKC3', 7395, 1708.7, 349.05, 9452.75),
            ('SKF', 50, '22211-EKC3', 7634, 1925, 406.9, 9965.9),
            ('SKF', 55, '22212-EKC3', 8357, 2303.7, 443.95, 11104.65),
            ('SKF', 60, '22213-EKC3', 8449, 2680.3, 542.75, 11672.05),
            ('SKF', 65, '22215-EKC3', 10699, 3052, 780.65, 14531.65),
            ('SKF', 70, '22216-EKC3', 11872, 3777.2, 938.6, 16587.8),
            ('SKF', 75, '22217-EKC3', 14885, 3916.5, 1051.7, 19853.2),
            ('SKF', 80, '22218-EKC3', 15962, 5861.1, 1408.55, 23231.65),
            ('SKF', 90, '22220-EKC3', 20779, 7259.7, 1969.5, 30008.2),
            ('SKF', 100, '22222-EKC3', 25819, 8939, 2880.15, 37638.15),
            ('SKF', 30, '', 0, 0, 11.725, 11725),
        ]
        
        # Dodge bearings data
        dodge_data = [
            ('Dodge', 35, '', 0, 0, 12.404, 12404),
            ('Dodge', 40, '', 0, 0, 12.632, 12632),
            ('Dodge', 45, '', 0, 0, 13.599, 13599),
            ('Dodge', 50, '', 0, 0, 16.501, 16501),
            ('Dodge', 55, '', 0, 0, 18.606, 18606),
            ('Dodge', 60, '', 0, 0, 20.711, 20711),
            ('Dodge', 65, '', 0, 0, 25.435, 25435),
            ('Dodge', 70, '', 0, 0, 29.987, 29987),
            ('Dodge', 75, '', 0, 0, 33.685, 33685),
            ('Dodge', 80, '', 0, 0, 38.408, 38408),
            ('Dodge', 85, '', 0, 0, 46.828, 46828),
            ('Dodge', 90, '', 0, 0, 51.096, 51096),
            ('Dodge', 100, '', 0, 0, 66.215, 66215),
            ('Dodge', 110, '', 0, 0, 80.433, 80433),
            ('Dodge', 115, '', 0, 0, 99.982, 99982),
            ('Dodge', 125, '', 0, 0, 111.963, 111963),
            ('Dodge', 135, '', 0, 0, 278.726, 278726),
            ('Dodge', 140, '', 0, 0, 335.561, 335561),
        ]
        
        # NTN bearings data
        ntn_data = [
            ('NTN', 25, '22206-EKC3', 2442, 631, 148, 3221),
            ('NTN', 30, '22207-EKC3', 2547, 1357.3, 234, 4138.3),
            ('NTN', 35, '22208-EKC3', 2779, 1446.2, 250.9, 4476.1),
            ('NTN', 40, '22209-EKC3', 3050, 1507.8, 273, 4830.8),
            ('NTN', 45, '22210-EKC3', 3808, 1708.7, 349.05, 5865.75),
            ('NTN', 50, '22211-EKC3', 3015, 1925, 406.9, 5346.9),
            ('NTN', 55, '22212-EKC3', 3699, 2303.7, 443.95, 6446.65),
            ('NTN', 60, '22213-EKC3', 3860, 2680.3, 542.75, 7083.05),
            ('NTN', 65, '22215-EKC3', 4034, 3052, 780.65, 7866.65),
            ('NTN', 70, '22216-EKC3', 4466, 3777.2, 938.6, 9181.8),
            ('NTN', 75, '22217-EKC3', 4645, 3916.5, 1051.7, 9613.2),
            ('NTN', 80, '22218-EKC3', 5208, 5861.1, 1408.55, 12477.65),
            ('NTN', 90, '22220-EKC3', 6679, 7259.7, 1969.5, 15908.2),
            ('NTN', 100, '22222-EKC3', 10194, 8939, 2880.15, 22013.15),
            ('NTN', 110, '22224-EKC3', 11872, 10924.2, 2880.15, 25676.35),
            ('NTN', 115, '22226-EKC3', 13930, 14069.3, 3361.15, 31360.45),
            ('NTN', 125, '22228-EKC3', 16059, 13000, 4000, 33059),
            ('NTN', 130, '22230-EKC3', 20648, 14450, 4000, 39098),
        ]
        
        # Insert all data
        cursor.executemany('INSERT INTO BearingLookup VALUES (?, ?, ?, ?, ?, ?, ?)', skf_data)
        cursor.executemany('INSERT INTO BearingLookup VALUES (?, ?, ?, ?, ?, ?, ?)', dodge_data)
        cursor.executemany('INSERT INTO BearingLookup VALUES (?, ?, ?, ?, ?, ?, ?)', ntn_data)
        
        # Commit the changes
        conn.commit()
        logger.info("Successfully inserted all bearing data")
        
        # Verify data by selecting a few rows
        cursor.execute("SELECT COUNT(*) FROM BearingLookup")
        count = cursor.fetchone()[0]
        logger.info(f"Total records in BearingLookup: {count}")
        
        cursor.execute("SELECT DISTINCT Brand FROM BearingLookup")
        brands = cursor.fetchall()
        logger.info(f"Brands in BearingLookup: {[brand[0] for brand in brands]}")
        
        # Close the connection
        conn.close()
        logger.info("Database connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error creating bearing lookup table: {str(e)}")
        return False

if __name__ == "__main__":
    if create_bearing_lookup_table():
        print("BearingLookup table created and populated successfully.")
    else:
        print("Failed to create BearingLookup table.") 