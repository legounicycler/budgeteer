import sqlite3, platform
from secret import WINDOWS_DATABASE_PATH, LINUX_DATABASE_PATH

platform = platform.system()
if platform == 'Windows':
    database = WINDOWS_DATABASE_PATH
else:
    database = LINUX_DATABASE_PATH

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
        last_name TEXT NOT NULL,
        unallocated_e_id INTEGER NOT NULL,
        FOREIGN KEY (unallocated_e_id) REFERENCES envelopes(id)
        )
    """)

    c.close()