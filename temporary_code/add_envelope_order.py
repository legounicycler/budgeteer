from database import *
from secret import LOCAL_DATABASE_PATH

database = LOCAL_DATABASE_PATH

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    # Create the order column in the envelopes table
    c.execute("""
        ALTER TABLE envelopes
        ADD COLUMN display_order INTEGER;
        """)