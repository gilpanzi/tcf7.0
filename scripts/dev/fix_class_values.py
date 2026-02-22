import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_class_values():
    """Clean up class values by removing whitespace and newlines."""
    try:
        # Connect to the database
        conn = sqlite3.connect('database/fan_weights.db')
        cursor = conn.cursor()
        
        # Get all records with whitespace in class values
        cursor.execute('SELECT "Fan Model", "Fan Size", "Class", "Arrangement" FROM FanWeights')
        records = cursor.fetchall()
        
        # Update each record
        updates = 0
        for record in records:
            fan_model, fan_size, class_value, arrangement = record
            cleaned_value = class_value.strip() if isinstance(class_value, str) else class_value
            
            if cleaned_value != class_value:
                logger.info(f"Cleaning Class value from '{class_value}' to '{cleaned_value}' for Fan Model: {fan_model}, Size: {fan_size}, Arrangement: {arrangement}")
                cursor.execute(
                    'UPDATE FanWeights SET "Class" = ? WHERE "Fan Model" = ? AND "Fan Size" = ? AND "Class" = ? AND "Arrangement" = ?',
                    (cleaned_value, fan_model, fan_size, class_value, arrangement)
                )
                updates += 1
        
        # Commit the changes
        conn.commit()
        logger.info(f"Successfully cleaned {updates} class values")
        
        # Show final class distribution
        cursor.execute('SELECT DISTINCT "Class", COUNT(*) as count FROM FanWeights GROUP BY "Class" ORDER BY CAST("Class" AS INTEGER)')
        class_counts = cursor.fetchall()
        logger.info("\nFinal class distribution:")
        for class_value, count in class_counts:
            logger.info(f"Class {class_value}: {count} records")
        
    except Exception as e:
        logger.error(f"Error cleaning class values: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting class value cleanup...")
    fix_class_values()
    logger.info("Cleanup completed") 