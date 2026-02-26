import os
import sys

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection
from services.customer_matcher import find_best_match, clean_company_name
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_customers(cursor):
    cursor.execute("SELECT id, primary_name FROM Customers")
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def deduplicate_and_link_customers():
    """Scan Enquiries, Orders, and Projects to populate Customers table and link them."""
    logger.info("Starting customer deduplication and linking...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Collect all distinct customer names from our data sources
        customer_names = set()
        
        cursor.execute("SELECT DISTINCT customer_name FROM EnquiryRegister WHERE customer_name IS NOT NULL")
        for row in cursor.fetchall():
            customer_names.add(row[0].strip())
            
        cursor.execute("SELECT DISTINCT customer_name FROM Orders WHERE customer_name IS NOT NULL")
        for row in cursor.fetchall():
            customer_names.add(row[0].strip())
            
        cursor.execute("SELECT DISTINCT customer_name FROM Projects WHERE customer_name IS NOT NULL")
        for row in cursor.fetchall():
            customer_names.add(row[0].strip())
            
        logger.info(f"Found {len(customer_names)} distinct raw customer names.")
        
        # 2. Process names and insert/link
        existing_customers = get_all_customers(cursor)
        
        # Optimization: Pre-calculate cleaned names for existing customers
        from services.customer_matcher import clean_company_name
        for ec in existing_customers:
            ec['cleaned'] = clean_company_name(ec['primary_name'])
        
        batch_size = 50
        names_list = list(customer_names)
        logger.info(f"Processing {len(names_list)} names in batches of {batch_size}...")
        
        for i in range(0, len(names_list), batch_size):
            batch = names_list[i : i + batch_size]
            for raw_name in batch:
                if not raw_name: continue
                    
                match_id, score = find_best_match(raw_name, existing_customers, threshold=0.88)
                
                if match_id and score >= 0.88:
                    cursor.execute('''
                        INSERT OR IGNORE INTO CustomerAliases (customer_id, alias_name)
                        VALUES (?, ?)
                    ''', (match_id, raw_name))
                    assigned_id = match_id
                else:
                    cursor.execute("SELECT id FROM Customers WHERE primary_name = ?", (raw_name,))
                    existing_row = cursor.fetchone()
                    if not existing_row:
                        logger.info(f"Creating new customer profile for: {raw_name}")
                        cursor.execute('INSERT INTO Customers (primary_name) VALUES (?)', (raw_name,))
                        assigned_id = cursor.lastrowid
                        new_cust = {'id': assigned_id, 'primary_name': raw_name, 'cleaned': clean_company_name(raw_name)}
                        existing_customers.append(new_cust)
                        cursor.execute('INSERT OR IGNORE INTO CustomerAliases (customer_id, alias_name) VALUES (?, ?)', (assigned_id, raw_name))
                    else:
                        assigned_id = existing_row[0]
                
                # Link raw names to the assigned customer ID
                cursor.execute('UPDATE EnquiryRegister SET customer_id = ? WHERE customer_name = ?', (assigned_id, raw_name))
                cursor.execute('UPDATE Orders SET customer_id = ? WHERE customer_name = ?', (assigned_id, raw_name))
                cursor.execute('UPDATE Projects SET customer_id = ? WHERE customer_name = ?', (assigned_id, raw_name))
            
            # Commit after each batch to avoid holding huge locks and show progress
            conn.commit()
            logger.info(f"Progress: {min(i + batch_size, len(names_list))}/{len(names_list)} names processed.")
            
        # 4. Rebuild CustomerYearBindings from latest Enquiries and Orders
        logger.info("Rebuilding CustomerYearBindings from Enquiries and Orders...")
        cursor.execute("DELETE FROM CustomerYearBindings") # Clear table to start fresh
        
        # Enquiries
        cursor.execute('''
            INSERT OR IGNORE INTO CustomerYearBindings (customer_id, year, region, sales_engineer)
            SELECT customer_id, year, region, sales_engineer 
            FROM EnquiryRegister 
            WHERE customer_id IS NOT NULL AND year IS NOT NULL
            GROUP BY customer_id, year, region, sales_engineer
        ''')
        
        # Orders
        cursor.execute('''
            INSERT OR IGNORE INTO CustomerYearBindings (customer_id, year, region, sales_engineer)
            SELECT customer_id, year, region, sales_engineer 
            FROM Orders 
            WHERE customer_id IS NOT NULL AND year IS NOT NULL
            GROUP BY customer_id, year, region, sales_engineer
        ''')
        
        # 5. Cleanup Orphaned Customers (No Enquiries AND No Orders)
        logger.info("Cleaning up orphaned customers without orders or enquiries...")
        cursor.execute('''
            DELETE FROM Customers 
            WHERE id NOT IN (SELECT DISTINCT customer_id FROM EnquiryRegister WHERE customer_id IS NOT NULL)
            AND id NOT IN (SELECT DISTINCT customer_id FROM Orders WHERE customer_id IS NOT NULL)
        ''')
        
        # Cascade delete aliases and year bindings for orphaned customers
        cursor.execute('''
            DELETE FROM CustomerAliases 
            WHERE customer_id NOT IN (SELECT id FROM Customers)
        ''')
        
        cursor.execute('''
            DELETE FROM CustomerYearBindings
            WHERE customer_id NOT IN (SELECT id FROM Customers)
        ''')
            
        conn.commit()
    logger.info("Customer deduplication complete!")

if __name__ == "__main__":
    deduplicate_and_link_customers()
