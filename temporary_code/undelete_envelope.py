import sqlite3
import sys
import os

# Adds the parent directory to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from secret import LOCAL_DATABASE_PATH

database = LOCAL_DATABASE_PATH

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    c.execute("UPDATE envelopes SET deleted=0 WHERE id='16' AND user_id='6c3b68ba-2fd3-4afd-a4bb-d550f212888a'")
    conn.commit()