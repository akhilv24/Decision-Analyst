"""
Database migration to add profile_picture field to users table.
"""

import sys
sys.path.insert(0, r'c:\Users\Akhil\OneDrive\Desktop\Decision Analyst')

import os
os.environ['SKIP_GROQ'] = '1'

import sqlite3
from datetime import datetime

def migrate_database():
    """Add profile_picture column to users table."""
    db_path = r'c:\Users\Akhil\OneDrive\Desktop\Decision Analyst\instance\decision_analyst.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print("Existing columns in users table:", existing_columns)
        
        # Add profile_picture column if it doesn't exist
        if 'profile_picture' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255)")
            print("✓ Added column: profile_picture")
        else:
            print("✓ Column already exists: profile_picture")
        
        conn.commit()
        conn.close()
        
        print("\n✓ Database migration complete!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)

