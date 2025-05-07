import sqlite3
import logging

def check_vendors():
    try:
        # Connect to the database
        conn = sqlite3.connect('database/fan_weights.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all vendor data
        cursor.execute('SELECT * FROM VendorWeightDetails ORDER BY Vendor, WeightStart')
        vendors = cursor.fetchall()

        print("\nVendor Weight Details:")
        print("=" * 80)
        print(f"{'Vendor':<20} {'Weight Range':<20} {'MS Price':<15} {'SS304 Price':<15}")
        print("-" * 80)

        for row in vendors:
            weight_range = f"{row['WeightStart']} - {row['WeightEnd']}"
            print(f"{row['Vendor']:<20} {weight_range:<20} {row['MSPrice']:<15} {row['SS304Price']:<15}")

        print("\nTotal vendors:", len(set(row['Vendor'] for row in vendors)))
        print("Total price ranges:", len(vendors))

    except Exception as e:
        print(f"Error checking vendor data: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_vendors() 