from database import *
import platform

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/alimiero/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

#Adds the envelope reconcile balance column to the transactions table
def add_e_reconcile_bal_column():
    with conn:
        c.execute("""
            ALTER TABLE transactions
            ADD e_reconcile_bal INTEGER NOT NULL DEFAULT 0
            """)

#Reset the reconcile balances to zero during testing
def clear_e_reconcile_bal():
    with conn:
        c.execute("UPDATE transactions SET e_reconcile_bal=0")

#Populates the envelope reconcile balance column with the proper numbers
def create_e_reconcile_bal():
    with conn:
        envelope_ids = []
        c.execute("SELECT envelope_id FROM transactions GROUP BY envelope_id")
        for row in c:
            if row[0] is not None:
                    envelope_ids.append(row[0])
        for a_id in envelope_ids:
            c.execute("SELECT id,amount,e_reconcile_bal FROM transactions WHERE envelope_id=? ORDER BY day DESC, id DESC", (a_id,))
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
                c.execute("UPDATE transactions SET e_reconcile_bal=? WHERE id=?", (t_r_bal,t_id))

#Renames the old reconcile_balance column which was only meant for account reconcile balances
def rename_reconcile_bal():
    with conn:
        c.execute("""ALTER TABLE transactions RENAME TO transactions_old;""")

        c.execute("""
                    CREATE TABLE transactions (
                        id INTEGER PRIMARY KEY,
                        type INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        amount INTEGER NOT NULL,
                        day DATE NOT NULL,
                        envelope_id INTEGER,
                        account_id INTEGER,
                        grouping INTEGER NOT NULL,
                        note TEXT NOT NULL DEFAULT '',
                        schedule TEXT,
                        status BOOLEAN NOT NULL DEFAULT 0,
                        user_id NOT NULL,
                        a_reconcile_bal INTEGER NOT NULL DEFAULT 0
                    );
                """)

        c.execute("""
                    INSERT INTO transactions (id, type, name, amount, day, envelope_id, account_id, grouping, note, schedule, status, user_id, a_reconcile_bal)
                    SELECT id, type, name, amount, day, envelope_id, account_id, grouping, note, schedule, status, user_id, reconcile_balance
                    FROM transactions_old;
                """)

        c.execute("""DROP TABLE transactions_old""")

def main():
    rename_reconcile_bal()       # 1. Rename the old column which was previously just for accounts
    add_e_reconcile_bal_column() # 2. Add an envelope reconcile balance column
    create_e_reconcile_bal()     # 3. Populate the numbers with their proper values


if __name__ == "__main__":
    main()
