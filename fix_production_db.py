#!/usr/bin/env python3
"""
Production Database Fix Script
Ensures admin interface can access database files in production environment.
"""

import sqlite3
import os
import shutil
import sys

def find_databases_with_data():
    """Find databases that contain Projects and ProjectFans data."""
    
    # Common database locations
    search_paths = [
        'fan_pricing.db',
        'database/fan_weights.db',
        'central_database/all_projects.db',
        'data/fan_pricing.db',
        'data/central_database/all_projects.db'
    ]
    
    databases_with_data = {}
    
    for db_path in search_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check for Projects table
                projects_count = 0
                project_fans_count = 0
                
                try:
                    cursor.execute("SELECT COUNT(*) FROM Projects")
                    projects_count = cursor.fetchone()[0]
                except:
                    pass
                
                try:
                    cursor.execute("SELECT COUNT(*) FROM ProjectFans")
                    project_fans_count = cursor.fetchone()[0]
                except:
                    pass
                
                if projects_count > 0 or project_fans_count > 0:
                    databases_with_data[db_path] = {
                        'projects': projects_count,
                        'project_fans': project_fans_count
                    }
                    print(f"✅ Found data in {db_path}: {projects_count} Projects, {project_fans_count} ProjectFans")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ Error reading {db_path}: {e}")
    
    return databases_with_data

def setup_admin_interface():
    """Set up database files for admin interface access."""
    
    print("🔧 Setting up database admin interface...")
    
    # Find databases with actual data
    databases = find_databases_with_data()
    
    if not databases:
        print("❌ No databases with data found!")
        return False
    
    # Create required directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/central_database', exist_ok=True)
    
    # Determine best source databases
    main_db_source = None
    central_db_source = None
    
    # Look for main database (preferably fan_pricing.db)
    for db_path in ['fan_pricing.db', 'data/fan_pricing.db']:
        if db_path in databases:
            main_db_source = db_path
            break
    
    # Look for central database
    for db_path in ['central_database/all_projects.db', 'data/central_database/all_projects.db']:
        if db_path in databases:
            central_db_source = db_path
            break
    
    # If we don't have specific databases, use the best available
    if not main_db_source:
        main_db_source = max(databases.keys(), key=lambda x: databases[x]['projects'])
    if not central_db_source:
        central_db_source = max(databases.keys(), key=lambda x: databases[x]['project_fans'])
    
    # Admin interface expects these exact paths
    admin_main_path = 'data/fan_pricing.db'
    admin_central_path = 'data/central_database/all_projects.db'
    
    try:
        # Copy to admin interface locations
        if main_db_source != admin_main_path:
            print(f"📁 Copying {main_db_source} → {admin_main_path}")
            shutil.copy2(main_db_source, admin_main_path)
        
        if central_db_source != admin_central_path:
            print(f"📁 Copying {central_db_source} → {admin_central_path}")
            shutil.copy2(central_db_source, admin_central_path)
        
        # Verify the setup
        conn = sqlite3.connect(admin_main_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Projects")
        main_projects = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ProjectFans")
        main_fans = cursor.fetchone()[0]
        conn.close()
        
        conn = sqlite3.connect(admin_central_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Projects")
        central_projects = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ProjectFans")
        central_fans = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ Admin interface ready!")
        print(f"   Main DB: {main_projects} Projects, {main_fans} ProjectFans")
        print(f"   Central DB: {central_projects} Projects, {central_fans} ProjectFans")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up admin interface: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Production Database Admin Fix")
    print("=" * 50)
    
    success = setup_admin_interface()
    
    if success:
        print("\n🎉 Database admin interface is now ready!")
        print("📊 Access your data at /db-admin/")
    else:
        print("\n❌ Failed to set up database admin interface")
        sys.exit(1) 