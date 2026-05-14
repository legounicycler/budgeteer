import sqlite3, sys, os

# Adds the parent directory to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from secret import LOCAL_DATABASE_PATH

database = LOCAL_DATABASE_PATH

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    c.execute("DELETE FROM transactions WHERE id = 12870")
    c.execute("DELETE FROM transactions WHERE id = 13802")
    c.execute("UPDATE accounts SET deleted=0 WHERE id = 23")
    conn.commit()