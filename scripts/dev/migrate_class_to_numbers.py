import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_roman_numeral(s):
    """Check if a string is a Roman numeral."""
    roman_numerals = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
                     'HP', 'H'}  # Including special cases
    return str(s).upper() in roman_numerals

def roman_to_int(roman):
    """Convert Roman numeral to integer."""
    roman_values = {
        'I': '1',
        'II': '2',
        'III': '3',
        'IV': '4',
        'V': '5',
        'VI': '6',
        'VII': '7',
        'VIII': '8',
        'IX': '9',
        'X': '10',
        'HP': '1',  # Map HP to class 1
        'H': '1'    # Map H to class 1
    }
    return roman_values.get(str(roman).upper(), str(roman))

def migrate_class_column():
    """Migrate the Class column from Roman numerals to numbers."""
    try:
        # Connect to the database
        conn = sqlite3.connect('database/fan_weights.db')
        cursor = conn.cursor()
        
        # Get all records from FanWeights table
        cursor.execute('SELECT "Fan Model", "Fan Size", "Class", "Arrangement" FROM FanWeights')
        records = cursor.fetchall()
        logger.info(f"Found {len(records)} total records")
        
        # Update each record
        updates = 0
        for record in records:
            fan_model, fan_size, class_value, arrangement = record
            
            # Only convert if it's a Roman numeral
            if is_roman_numeral(class_value):
                numeric_value = roman_to_int(class_value)
                if numeric_value != class_value:
                    logger.info(f"Converting Class from {class_value} to {numeric_value} for Fan Model: {fan_model}, Size: {fan_size}, Arrangement: {arrangement}")
                    cursor.execute(
                        'UPDATE FanWeights SET "Class" = ? WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?',
                        (numeric_value, fan_model, fan_size, class_value, arrangement)
                    )
                    updates += 1
        
        # Commit the changes
        conn.commit()
        logger.info(f"Successfully migrated {updates} records from Roman numerals to numbers")
        
        # Verify the changes
        cursor.execute('SELECT DISTINCT "Class", COUNT(*) as count FROM FanWeights GROUP BY "Class" ORDER BY CAST("Class" AS INTEGER)')
        class_counts = cursor.fetchall()
        logger.info("\nClass distribution after migration:")
        for class_value, count in class_counts:
            logger.info(f"Class {class_value}: {count} records")
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting Class column migration...")
    migrate_class_column()
    logger.info("Migration completed") 