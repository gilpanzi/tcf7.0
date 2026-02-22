import sqlite3
import pandas as pd
import os
import sys
import re

def clean_numeric(val):
    """Clean numeric values (remove commas, handle non-numeric)."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == '-' or s == '':
        return None
    # Remove commas
    s = s.replace(',', '')
    try:
        return float(s)
    except ValueError:
        return None

def import_motor_prices_from_excel(excel_file):
    """
    Import motor prices from an Excel file (path or file object) and replace the existing MotorPrices table.
    Handles multiple horizontal tables in the same sheet.
    """
    try:
        # Check if input is a string path
        is_path = isinstance(excel_file, str)
        
        if is_path:
            if not os.path.exists(excel_file):
                print(f"Error: Excel file not found at {excel_file}")
                return False
            print(f"Reading data from {excel_file}...")
        else:
            print(f"Reading data from uploaded file...")
            
        try:
            df = pd.read_excel(excel_file, engine='openpyxl')
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return False
            
        # Normalize columns: strip whitespace
        df.columns = df.columns.astype(str).str.strip()
        
        # Identify sets of columns
        base_cols = {
            'kw': ['Motor kW', 'Kw', 'KW', 'kw'],
            'pole': ['Pole'],
            'brand': ['Brand'],
            'eff': ['Efficiency'],
            'price': ['List Price', 'Price']
        }
        
        # Find all "Motor kW" columns (including suffixes like .1, .2)
        kw_cols = [c for c in df.columns if any(c.startswith(base) for base in base_cols['kw'])]
        
        if not kw_cols:
            print("Error: Could not find any 'Motor kW' columns.")
            print(f"Available columns: {df.columns.tolist()}")
            return False
            
        print(f"Found {len(kw_cols)} data blocks (columns: {kw_cols})")
        
        all_data = []
        
        for kw_col in kw_cols:
            suffix = ""
            match = re.search(r'(\.\d+)$', kw_col)
            if match:
                suffix = match.group(1)
            
            def find_col(types, current_suffix):
                for t in types:
                    candidate = t + current_suffix
                    if candidate in df.columns:
                        return candidate
                return None

            pole_col = find_col(base_cols['pole'], suffix)
            brand_col = find_col(base_cols['brand'], suffix)
            eff_col = find_col(base_cols['eff'], suffix)
            price_col = find_col(base_cols['price'], suffix)
            
            if not (pole_col and brand_col and eff_col and price_col):
                # Only warn if it looks like a real block, not just stray column
                pass
                continue
                
            # Extract data from this block
            block_df = df[[kw_col, pole_col, brand_col, eff_col, price_col]].copy()
            block_df.columns = ['Motor kW', 'Pole', 'Brand', 'Efficiency', 'Price']
            
            # Clean data - basic dropna
            block_df = block_df.dropna(subset=['Brand', 'Price', 'Motor kW'])
            all_data.append(block_df)
            
        if not all_data:
            print("No valid data found in any blocks.")
            return False
            
        # Combine all blocks
        final_df = pd.concat(all_data, ignore_index=True)
        print(f"Total potential records: {len(final_df)}")
        
        # Connect to database
        db_path = 'data/fan_pricing.db'
        if not os.path.exists(db_path) and os.path.exists('fan_pricing.db'):
             db_path = 'fan_pricing.db'
             
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='MotorPrices'")
        if not cursor.fetchone():
             cursor.execute("""
                CREATE TABLE MotorPrices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Brand TEXT,
                    "Motor kW" REAL,
                    Pole INTEGER,
                    Efficiency TEXT,
                    Price REAL
                )
             """)

        # Backup
        try:
            cursor.execute("SELECT COUNT(*) FROM MotorPrices")
            old_count = cursor.fetchone()[0]
        except:
            old_count = 0
            
        backup_table = f"MotorPrices_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM MotorPrices")
        except:
            pass # Table might involve complex types or be empty
        
        # Clear existing data
        cursor.execute("DELETE FROM MotorPrices")
        
        success_count = 0
        error_count = 0
        duplicate_count = 0
        
        # Log errors to file
        with open('import_errors.txt', 'w') as error_log:
            for _, row in final_df.iterrows():
                try:
                    # Parse and clean values
                    brand = str(row['Brand']).strip()
                    
                    # Skip header rows that might have been included
                    if brand.lower() == 'brand' or str(row['Motor kW']).lower().startswith('motor'):
                        continue
                        
                    kw = clean_numeric(row['Motor kW'])
                    
                    # Pole cleaning
                    pole_val = str(row['Pole']).strip()
                    if '.' in pole_val:
                        pole_val = pole_val.split('.')[0]
                    try:
                        pole = int(pole_val)
                    except:
                        pole = None
                        
                    eff = str(row['Efficiency']).strip()
                    price = clean_numeric(row['Price'])
                    
                    # Skip invalid records
                    if kw is None or price is None or pole is None:
                        error_log.write(f"Skipped invalid data: KW={kw}, Price={price}, Pole={pole}\nRow: {row.to_dict()}\n\n")
                        error_count += 1
                        continue

                    # Insert
                    cursor.execute(
                        "INSERT INTO MotorPrices (Brand, \"Motor kW\", Pole, Efficiency, Price) VALUES (?, ?, ?, ?, ?)",
                        (brand, kw, pole, eff, price)
                    )
                    success_count += 1
                    
                except sqlite3.IntegrityError:
                    # Duplicate entry found
                    duplicate_count += 1
                    error_log.write(f"Duplicate entry skipped: {brand}, {kw}kW, {pole}P, {eff}\n")
                    
                except Exception as e:
                    error_count += 1
                    error_log.write(f"Error: {e}\nRow: {row.to_dict()}\n\n")

        print(f"Import summary:")
        print(f"  - Backed up {old_count} records to {backup_table}")
        print(f"  - Imported {success_count} records")
        print(f"  - Duplicates skipped: {duplicate_count}")
        if error_count:
            print(f"  - Failed/Skipped {error_count} records. See import_errors.txt for details.")
            
        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_motor_prices_from_excel(sys.argv[1])
    else:
        print("Usage: python import_motor_prices_excel.py <file.xlsx>")
