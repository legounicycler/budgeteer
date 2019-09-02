from database import *

database = 'C:\\Users\\norma\Dropbox\\database.sqlite'
# database = '/home/anthony/database.sqlite'
conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()




print("-----FUll DATABASE-----")
print_database()
print()

print("-----SCHEDULED ONES-----")
c.execute("SELECT * FROM transactions WHERE schedule IS NOT NULL AND schedule != '' ")
for row in c:
    print(row)
print()

transactions = c.fetchall()
print(transactions)

