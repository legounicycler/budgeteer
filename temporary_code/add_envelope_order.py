from database import *
from secret import WINDOWS_DATABASE_PATH, LINUX_DATABASE_PATH
import platform

platform = platform.system()
if platform == 'Windows':
    database = WINDOWS_DATABASE_PATH
else:
    database = LINUX_DATABASE_PATH

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    # Create the order column in the envelopes table
    c.execute("""
        ALTER TABLE envelopes
        ADD COLUMN display_order INTEGER;
        """)