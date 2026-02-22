import sqlite3
import os

def analyze_issue():
    """Analyze the database issue and fix the problem."""
    
    # First, check the database schema
    data_dir = 'data'
    central_db_dir = os.path.join(data_dir, 'central_database')
    central_db_path = os.path.join(central_db_dir, 'all_projects.db')
    
    conn = sqlite3.connect(central_db_path)
    cursor = conn.cursor()
    
    # Get column info from the table
    cursor.execute("PRAGMA table_info(ProjectFans)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"The ProjectFans table has {len(columns)} columns:")
    for i, col in enumerate(columns):
        print(f"{i+1}. {col[1]} ({col[2]})")
    
    # The VALUES placeholders in the INSERT statement
    insert_sql = "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    placeholder_count = insert_sql.count('?')
    print(f"\nThe INSERT statement has {placeholder_count} placeholders (question marks)")
    
    # Fix the issue by providing the correct SQL statement
    print("\nThe correct INSERT statement should have 43 placeholders to match the number of columns")
    print("(or 42 if we exclude the 'id' column which is auto-incremented)")
    
    print("\nCheck if 'created_at' column exists (it should be auto-populated):")
    if 'created_at' in column_names:
        print("'created_at' column exists in the table, but it may not be in the INSERT statement")
    else:
        print("'created_at' column does not exist in the table")
    
    # Close the connection
    conn.close()
    
    # Now, check the routes.py file INSERT statement
    insert_statement = """
    INSERT INTO ProjectFans (
        enquiry_number, fan_number, fan_model, size, class, arrangement,
        vendor, material, accessories, bare_fan_weight, accessory_weight,
        total_weight, fabrication_weight, bought_out_weight,
        fabrication_cost, motor_cost, vibration_isolators_cost,
        drive_pack_cost, bearing_cost, optional_items_cost,
        flex_connectors_cost, bought_out_cost, total_cost,
        fabrication_selling_price, bought_out_selling_price,
        total_selling_price, total_job_margin, vibration_isolators,
        drive_pack_kw, custom_accessories, optional_items,
        custom_option_items, motor_kw, motor_brand, motor_pole,
        motor_efficiency, motor_discount_rate, bearing_brand, shaft_diameter,
        no_of_isolators, fabrication_margin, bought_out_margin
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Extract column names from the insert statement
    column_part = insert_statement.split("(")[1].split(")")[0]
    insert_columns = [c.strip() for c in column_part.split(",")]
    
    print(f"\nNumber of columns in the INSERT statement: {len(insert_columns)}")
    
    # Check if the issue might be due to the created_at column
    print("\nPossible solution:")
    print("1. The error says 'Incorrect number of bindings supplied. The current statement uses 42, and there are 43 supplied.'")
    print("2. This suggests we're supplying 43 parameters but the SQL statement only expects 42.")
    print("3. The most likely fix is to update the routes.py file to add any missing columns or remove extra parameters.")
    
    # Generate a fix
    print("\nFix to apply in routes.py:")
    print("1. Make sure the VALUES clause has exactly 42 placeholders to match the 42 columns excluding 'id'")
    print("2. Make sure the parameter tuple has exactly 42 values")
    print("3. If 'created_at' is a column that should have a DEFAULT value, ensure it's not in the parameter list")

if __name__ == "__main__":
    analyze_issue() 