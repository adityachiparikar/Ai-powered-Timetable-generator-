
import sys
import os
import psycopg2

# Add backend to path so we can import app code
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.core.config import settings
    print(f"URI: {settings.SQLALCHEMY_DATABASE_URI}")
    
    # Check if we can connect directly
    print("Attempting raw connection...")
    user = settings.POSTGRES_USER
    password = settings.POSTGRES_PASSWORD
    host = settings.POSTGRES_SERVER
    db = settings.POSTGRES_DB
    
    print(f"Host: {host}, User: {user}, DB: {db}")
    
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db
    )
    print("✅ Raw connection successful!")
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
