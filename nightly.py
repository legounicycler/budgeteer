from database import *
from budgeteer import schedule_date_calc
import platform

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/alimiero/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

print("Beginning nightly.py")
log_write("----Beginning nightly.py----")

# Get all transactions with a schedule that are behind the current date
c.execute("SELECT * FROM transactions WHERE schedule IS NOT NULL AND day < datetime('now') ORDER by day DESC, id DESC")
tlist = []

# Create a transaction object for every transaction pulled from the database
for t in c:
    transaction = Transaction(t[1],t[2],t[3],date_parse(t[4]),t[5],t[6],gen_grouping_num(),t[8],t[9],t[10],t[11])
    tlist.append(transaction)
print("List of all scheduled transactions:")
print(tlist)
if len(tlist) > 0:
    print("INSERTING NEW SCHEDULED TRANSACTIONS")
    # Update the date to be the next scheduled one
    for t in tlist:
        t.date = schedule_date_calc(t.date,t.schedule)
        print("Inserting: ",t)
        insert_transaction(t)

    with conn:
        print("UPDATING OLD SCHEDULED TRANSACTIONS")
        c.execute("""UPDATE transactions SET schedule = NULL WHERE id IN (
                  SELECT id FROM transactions WHERE schedule IS NOT NULL AND day < datetime('now')
                  )""")
        log_write("UPDATED OLD SCHEDULES")
else:
    print("No scheduled transactions to update. Back to business as usual.")
    log_write("NO SCHEDULED TRANSACTIONS")
log_write("-----Ending nightly.py-----")