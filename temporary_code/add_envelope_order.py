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
    # Create the order column in the envelopes table
    c.execute("""
        ALTER TABLE envelopes
        ADD COLUMN display_order INTEGER;
        """)