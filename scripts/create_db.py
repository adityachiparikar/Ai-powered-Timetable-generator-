
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.core.config import settings
import os
from dotenv import load_dotenv

def create_database():
    # Load .env explicitly to ensure we have latest values
    load_dotenv("backend/.env")
    
    # Connect to default 'postgres' database
    try:
        # Use settings or env vars directly
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "Aditya@09")
        host = os.getenv("POSTGRES_SERVER", "localhost")
        
        print(f"Connecting to PostgreSQL at {host} as {user}...")
        con = psycopg2.connect(dbname="postgres", user=user, host=host, password=password)
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'timetable_db'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating database 'timetable_db'...")
            cursor.execute("CREATE DATABASE timetable_db")
            print("✅ Database created successfully!")
        else:
            print("ℹ️ Database 'timetable_db' already exists.")
            
        cursor.close()
        con.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    create_database()
