import os
import psycopg

conn_info = (
    f"host={os.environ['DB_HOST']} port={os.environ['DB_PORT']} "
    f"dbname={os.environ['DB_NAME']} user={os.environ['DB_USER']} "
    f"password={os.environ['DB_PASSWORD']}"
)

with psycopg.connect(conn_info) as conn:
    print(conn.execute("SELECT version()").fetchone()[0])