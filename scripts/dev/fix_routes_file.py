import re
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_routes_file():
    """Fix the routes.py file by removing the created_at parameter."""
    try:
        routes_file = "routes.py"
        backup_file = "routes.py.backup"
        
        # Create a backup of the routes.py file
        logger.info(f"Creating backup of {routes_file} as {backup_file}")
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # First, check if we still have the created_at column in the INSERT statement
        insert_pattern = r'INSERT INTO ProjectFans \(.*?created_at.*?\) VALUES'
        if not re.search(insert_pattern, content, re.DOTALL):
            logger.info("No 'created_at' column found in INSERT statement. It may have been already fixed.")
            
            # Check if we still have the parameter in the tuple
            param_pattern = r"datetime\.now\(\)\.strftime\('%Y-%m-%d %H:%M:%S'\)  # created_at"
            if re.search(param_pattern, content):
                logger.info("Found datetime.now() parameter for created_at. Removing it...")
                
                # First find the parameter block that ends with the created_at parameter
                param_block_pattern = r"fan\.get\('bought_out_margin', costs\.get\('bought_out_margin', 0\)\),\s+datetime\.now\(\)\.strftime\('%Y-%m-%d %H:%M:%S'\)  # created_at\s+\)\)"
                modified_content = re.sub(param_block_pattern, 
                                         "fan.get('bought_out_margin', costs.get('bought_out_margin', 0))\n                    ))", 
                                         content)
                
                # Write the modified content back to the file
                with open(routes_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                logger.info("Successfully removed datetime.now() parameter for created_at.")
                return True
            else:
                logger.info("No datetime.now() parameter found. File appears to be already fixed.")
                return True
        
        # Fix the INSERT statement
        logger.info("Removing 'created_at' column from INSERT statement...")
        
        # Remove 'created_at' from column list
        column_pattern = r'(no_of_isolators, fabrication_margin, bought_out_margin),\s+created_at\s+\)'
        modified_content = re.sub(column_pattern, r'\1\n                        )', content)
        
        # Remove the extra question mark for created_at
        values_pattern = r'(VALUES \(.*?\?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?, \?)\)\s+'
        modified_content = re.sub(values_pattern, r'\1)\n                    ', modified_content)
        
        # Remove the datetime.now() parameter
        param_pattern = r"(fan\.get\('bought_out_margin', costs\.get\('bought_out_margin', 0\)\)),\s+datetime\.now\(\)\.strftime\('%Y-%m-%d %H:%M:%S'\)  # created_at\s+\)\)"
        modified_content = re.sub(param_pattern, r'\1\n                    ))', modified_content)
        
        # Write the modified content back to the file
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        logger.info("Successfully fixed routes.py file")
        return True
    except Exception as e:
        logger.error(f"Error fixing routes.py file: {str(e)}")
        return False

if __name__ == "__main__":
    if fix_routes_file():
        print("Successfully fixed routes.py file.")
    else:
        print("Failed to fix routes.py file.") 