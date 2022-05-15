from database import *
import platform

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/alimiero/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

def add_a_reconcile_bal_column():
    c.execute("""
        ALTER TABLE transactions
        ADD COLUMN a_reconcile_bal INTEGER NOT NULL DEFAULT 0
        """)

def clear_a_reconcile_bal():
    with conn:
        c.execute("UPDATE transactions SET a_reconcile_bal=0")

def create_a_reconcile_bal():
    with conn:
        account_ids = []
        c.execute("SELECT account_id FROM transactions GROUP BY account_id")
        for row in c:
            if row[0] is not None:
                    account_ids.append(row[0])
        for a_id in account_ids:
            c.execute("SELECT id,amount,a_reconcile_bal FROM transactions WHERE account_id=? ORDER BY day DESC, id DESC", (a_id,))
            t_ids = []
            t_amounts =[]
            t_r_bals =[]
            for row in c:
                t_ids.append(row[0])
                t_amounts.append(row[1])
                t_r_bals.append(row[2])
            t_ids.reverse()
            t_amounts.reverse()
            t_r_bals.reverse()
            t_r_bals[0] = -1* t_amounts[0]
            for i in range(1,len(t_ids)):
                t_r_bals[i] = t_r_bals[i-1] - t_amounts[i]
            for i in range(0,len(t_ids)):
                t_id = t_ids[i]
                t_r_bal = t_r_bals[i]
                c.execute("UPDATE transactions SET a_reconcile_bal=? WHERE id=?", (t_r_bal,t_id))

def main():
    # Do something here, idk. I didn't actually use this file, it's just for show

if __name__ == "__main__":
    main()