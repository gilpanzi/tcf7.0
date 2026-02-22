#!/usr/bin/env python3
"""
Automatic Database Backup Script
Backs up all database files before any operations
"""

import os
import shutil
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_backup():
    """Create timestamped backup of all database files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"database_backups/auto_backup_{timestamp}"
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # List of database files to backup
    db_files = [
        'central_database/all_projects.db',
        'data/central_database/all_projects.db',
        'data/fan_pricing.db',
        'database/fan_weights.db'
    ]
    
    backed_up = []
    
    for db_file in db_files:
        if os.path.exists(db_file):
            backup_path = os.path.join(backup_dir, os.path.basename(db_file))
            shutil.copy2(db_file, backup_path)
            backed_up.append(db_file)
            logger.info(f"Backed up: {db_file} -> {backup_path}")
    
    if backed_up:
        logger.info(f"✅ Backup created: {backup_dir}")
        return backup_dir
    else:
        logger.warning("⚠️  No database files found to backup")
        return None

def restore_from_backup(backup_dir):
    """Restore database files from backup."""
    if not os.path.exists(backup_dir):
        logger.error(f"Backup directory not found: {backup_dir}")
        return False
    
    # Restore files
    for filename in os.listdir(backup_dir):
        if filename.endswith('.db'):
            src = os.path.join(backup_dir, filename)
            
            # Determine destination
            if filename == 'all_projects.db':
                # Restore to both locations
                destinations = [
                    'central_database/all_projects.db',
                    'data/central_database/all_projects.db'
                ]
            elif filename == 'fan_pricing.db':
                destinations = ['data/fan_pricing.db']
            elif filename == 'fan_weights.db':
                destinations = ['database/fan_weights.db']
            else:
                destinations = [f'database/{filename}']
            
            for dest in destinations:
                # Create directory if needed
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src, dest)
                logger.info(f"Restored: {src} -> {dest}")
    
    logger.info("✅ Database restoration completed")
    return True

def verify_database_integrity(db_path):
    """Verify database file integrity."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == 'ok':
            logger.info(f"✅ Database integrity OK: {db_path}")
            return True
        else:
            logger.error(f"❌ Database integrity FAILED: {db_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Database integrity check failed: {db_path} - {str(e)}")
        return False

if __name__ == "__main__":
    # Create backup
    backup_dir = create_backup()
    
    if backup_dir:
        print(f"Backup created: {backup_dir}")
        
        # Verify all database files
        db_files = [
            'central_database/all_projects.db',
            'data/central_database/all_projects.db',
            'data/fan_pricing.db',
            'database/fan_weights.db'
        ]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                verify_database_integrity(db_file) 