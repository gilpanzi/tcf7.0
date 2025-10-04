#!/usr/bin/env python3
"""
Script to update user passwords from plain text to hashed versions.
Run this before going live to secure user passwords.
"""

import sqlite3
import os
from security_utils import hash_password

def update_user_passwords():
    """Update all user passwords to hashed versions."""
    try:
        # Connect to database
        db_path = 'data/fan_pricing.db'
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute('SELECT id, username, password FROM users')
        users = cursor.fetchall()
        
        print(f"Found {len(users)} users to update:")
        
        for user_id, username, current_password in users:
            # Hash the current password
            hashed_password = hash_password(current_password)
            
            # Update the password
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', 
                         (hashed_password, user_id))
            
            print(f"✓ Updated password for user: {username}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("\n✅ All user passwords have been successfully hashed!")
        print("🔒 Users can now log in with their original passwords.")
        print("⚠️  Make sure to update the login verification to use verify_password()")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating passwords: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔐 User Password Security Update")
    print("=" * 40)
    
    response = input("This will hash all user passwords. Continue? (y/N): ")
    if response.lower() == 'y':
        update_user_passwords()
    else:
        print("Operation cancelled.")
