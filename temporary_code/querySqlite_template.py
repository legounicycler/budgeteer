import sqlite3, sys, os

# Adds the parent directory to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from secret import LOCAL_DATABASE_PATH

database = LOCAL_DATABASE_PATH

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    c.execute("SELECT * FROM transactions WHERE account_id = 23")
    result = c.fetchall()
    for row in result:
        print(row)