import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def clear_data():
    try:
        conn = psycopg2.connect(
            dbname='timetable_db',
            user='postgres',
            password='Aditya@09',
            host='localhost'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # List of tables to clear in order (considering foreign keys)
        # Or just use TRUNCATE CASCADE if supported and preferred
        tables = [
            'courses',
            'batches',
            'student_groups',
            'rooms',
            'teachers',
            'globalbreaks',
            'timeslots'
        ]
        
        print("Clearing data from tables...")
        for table in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"Cleared table: {table}")
            except Exception as e:
                print(f"Error clearing {table}: {e}")
                conn.rollback()

        cur.close()
        conn.close()
        print("All data cleared successfully.")
        
    except Exception as e:
        print(f"Error connecting to Postgres: {e}")

if __name__ == "__main__":
    clear_data()
