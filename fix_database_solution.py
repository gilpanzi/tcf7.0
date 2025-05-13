import sqlite3
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database_issue():
    try:
        # Check the routes.py file
        routes_file = "routes.py"
        backup_file = "routes.py.bak"
        
        logger.info(f"Creating backup of routes.py as {backup_file}")
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("Backup created. Now fixing the issue.")
        
        # Find and remove the extra NULL parameter
        original_line = "                        None  # Extra parameter for 42nd value"
        
        if original_line in content:
            logger.info("Found extra NULL parameter line in routes.py")
            # Remove this line
            new_content = content.replace(original_line + ",\n", "")
            new_content = new_content.replace(original_line, "")
            
            # Remove the extra trailing comma if needed
            new_content = re.sub(r'bought_out_margin, 0\)\),\s*\)\)', r'bought_out_margin, 0))\n                    ))', new_content)
            
            with open(routes_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("Removed extra NULL parameter from routes.py")
            return True
        else:
            # Check for any trailing comma issue
            pattern = r'(fan\.get\(\'bought_out_margin\', costs\.get\(\'bought_out_margin\', 0\)\)),\s*\)\)'
            match = re.search(pattern, content)
            
            if match:
                # Found trailing comma, removing it
                new_content = re.sub(pattern, r'\1\n                    ))', content)
                
                with open(routes_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info("Removed trailing comma after the last parameter in routes.py")
                return True
            else:
                logger.info("No specific issue found in routes.py. Manual inspection needed.")
                return False
    
    except Exception as e:
        logger.error(f"Error fixing database issue: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database fix...")
    if fix_database_issue():
        logger.info("Fix applied successfully. Restart the application to see the changes.")
    else:
        logger.info("No automatic fix applied. Manual inspection needed.") 