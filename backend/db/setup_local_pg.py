import psycopg2

def setup():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/postgres")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname='bhoomi'")
    if not cur.fetchone():
        cur.execute("CREATE ROLE bhoomi WITH LOGIN SUPERUSER PASSWORD 'changeme'")
        print("Role 'bhoomi' created.")
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname='bhoomisetu'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE bhoomisetu OWNER bhoomi")
        print("Database 'bhoomisetu' created.")
    conn.close()

    # Connect to bhoomisetu database to install extensions
    conn_bhoomi = psycopg2.connect("postgresql://bhoomi:changeme@localhost:5432/bhoomisetu")
    conn_bhoomi.autocommit = True
    cur_bhoomi = conn_bhoomi.cursor()
    cur_bhoomi.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    cur_bhoomi.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    print("Installed uuid-ossp and pg_trgm extensions.")
    conn_bhoomi.close()
    print("Local database setup complete!")

if __name__ == "__main__":
    setup()
