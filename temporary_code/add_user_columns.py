import platform, sqlite3
from datetime import datetime

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/opc/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:

    # Create the new users table
    c.execute("""
    CREATE TABLE new_users (
        uuid TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        registered_on TEXT NOT NULL,
        unallocated_e_id INTEGER NOT NULL,
        confirmed BOOLEAN NOT NULL DEFAULT 0,
        confirmed_on TEXT,
        last_login TEXT,
        FOREIGN KEY (unallocated_e_id) REFERENCES envelopes(id)
        )
    """)

    # Copy the data from the old table to the new table
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO new_users SELECT uuid, email, password_hash, password_salt, first_name, last_name, ?, unallocated_e_id, 1, ?, NULL FROM users", (today,today))

    # Drop the old table and rename the new table
    c.execute("DROP TABLE users")
    c.execute("ALTER TABLE new_users RENAME TO users")
    c.close()