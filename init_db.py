"""
Initialize database and create first admin user.
"""

import sys
sys.path.insert(0, r'c:\Users\Akhil\OneDrive\Desktop\Decision Analyst')

# Skip Groq initialization for database setup
import os
os.environ['SKIP_GROQ'] = '1'

from app import app, db
from backend.models import User, Asset, Liability, FinancialGoal, Scenario, HealthMetric

def init_database():
    """Initialize database and create tables."""
    with app.app_context():
        try:
            # Create all tables (this will add new columns to existing tables)
            db.create_all()
            print("✓ Database tables created/updated successfully")
            print("  - User table now includes google_sub column for OAuth")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create default admin user
            admin = User(
                username='admin',
                email='admin@decisionanalyst.com',
                first_name='Admin',
                last_name='User'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin user created")
            print("  Username: admin")
            print("  Password: admin123")
            print("  ⚠ IMPORTANT: Change this password immediately!")
        else:
            print("✓ Admin user already exists")
        
        print("\n✓ Database initialization complete!")
        print("\nYou can now run the application with: python app.py")

if __name__ == '__main__':
    init_database()
