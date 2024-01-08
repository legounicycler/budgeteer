import sqlite3, platform

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/opc/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    # Delete the original table
    c.execute("""
        DROP TABLE users
    """)

    # Create new table
    c.execute("""
    CREATE TABLE users (
        uuid TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL
        )
    """)