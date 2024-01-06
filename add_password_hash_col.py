from database import *
import platform

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/opc/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    # Create new table
    c.execute("""
    CREATE TABLE users_new (
        user_id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL
        )
    """)

    # Copy data from old table
    c.execute("""
        INSERT INTO users_new (user_id, email)
        SELECT user_id, email FROM users
    """)

    # Delete the original table
    c.execute("""
        DROP TABLE users
    """)

    # Rename the new table to original name
    c.execute("""
        ALTER TABLE users_new RENAME TO users
    """)