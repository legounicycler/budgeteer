import sqlite3, platform

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/opc/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

with conn:
    c.execute("SELECT uuid FROM users")
    newuuid = c.fetchone()[0]
    c.execute("SELECT unallocated_e_id FROM users")
    newunallocatedid = c.fetchone()[0]

    # 1. Set the unallocated envelope id to the original unallocated envelope
    c.execute("UPDATE users SET unallocated_e_id=? WHERE uuid=?", (1, newuuid))
    
    # 2. Delete the new (unused) unallocated envelope
    c.execute("DELETE FROM envelopes WHERE id=?", (newunallocatedid,))
    
    # 3. Set the user_id of all transactions, envelopes, and accounts to the new uuid
    c.execute("UPDATE transactions SET user_id=? WHERE user_id=?", (newuuid, 1))
    c.execute("UPDATE envelopes SET user_id=? WHERE user_id=?", (newuuid, 1))
    c.execute("UPDATE accounts SET user_id=? WHERE user_id=?", (newuuid, 1))

    c.close()