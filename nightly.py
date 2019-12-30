from database import *
from budgeteer import schedule_date_calc
import platform

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\Dropbox\\database.sqlite'
else:
    database = '/home/alimiero/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

c.execute("SELECT * FROM transactions WHERE schedule IS NOT NULL AND day < datetime('now') ORDER by day DESC, id DESC")
tlist = []
for t in c:
    transaction = Transaction(t[1],t[2],t[3],date_parse(t[4]),t[5],t[6],gen_grouping_num(),t[8],t[9],t[10],t[11])
    tlist.append(transaction)
print("INSERTING NEW SCHEDULED TRANSACTIONS")
for t in tlist:
    t.date = schedule_date_calc(t.date,t.schedule)
    print("Inserting:",t)
    insert_transaction(t)

with conn:
    print("UPDATING OLD SCHEDULED TRANSACTIONS")
    c.execute("""UPDATE transactions SET schedule = NULL WHERE id IN (
              SELECT id FROM transactions WHERE schedule IS NOT NULL AND day < datetime('now')
              )""")