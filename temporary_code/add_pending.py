import platform
import sqlite3

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/opc/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    c.execute("""
        ALTER TABLE transactions
        ADD COLUMN pending BOOL NOT NULL DEFAULT 0
        """)
    
    # c.execute("UPDATE transactions SET pending=0 WHERE date(day) <= date('now', 'localtime')")
    c.execute("UPDATE transactions SET pending=1 WHERE date(day) > date('now', 'localtime')")



