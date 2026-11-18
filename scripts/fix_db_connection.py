import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def check_postgres():
    try:
        # Try connecting to default postgres database first
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='Aditya@09',
            host='localhost'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if timetable_db exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname='timetable_db'")
        exists = cur.fetchone()
        
        if not exists:
            print("Database 'timetable_db' does not exist. Creating it...")
            cur.execute("CREATE DATABASE timetable_db")
            print("Database 'timetable_db' created successfully.")
        else:
            print("Database 'timetable_db' already exists.")
            
        cur.close()
        conn.close()
        print("Postgres connection successful.")
        
    except Exception as e:
        print(f"Error connecting to Postgres: {e}")

if __name__ == "__main__":
    check_postgres()
