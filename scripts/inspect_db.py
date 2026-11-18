import psycopg2

def inspect_db():
    try:
        conn = psycopg2.connect(
            dbname='timetable_db',
            user='postgres',
            password='Aditya@09',
            host='localhost'
        )
        cur = conn.cursor()
        
        # List all tables
        cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
        tables = cur.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        for table in tables:
            name = table[0]
            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{name}'")
            cols = cur.fetchall()
            print(f"Table '{name}': {cols}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
