import psycopg2
def list_tables():
    conn = psycopg2.connect(dbname='timetable_db', user='postgres', password='Aditya@09', host='localhost')
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
    print([t[0] for t in cur.fetchall()])
    cur.close()
    conn.close()
if __name__ == "__main__":
    list_tables()
