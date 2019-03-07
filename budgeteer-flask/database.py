import sqlite3
import datetime

database = 'C:\\Users\\norma\Dropbox\\database.sqlite'
conn = sqlite3.connect(database, check_same_thread=False)

c = conn.cursor()

BASIC_TRANSACTION = 0
ENVELOPE_TRANSFER = 1
ACCOUNT_TRANSFER = 2
INCOME = 3
SPLIT_TRANSACTION = 4

note = 'something useful'



class Transaction:

    def __init__(self, type, name, amt, date, envelope_id, account_id, grouping, note):
        self.id = None
        self.type = type
        self.name = name
        self.amt = amt
        self.date = date
        self.envelope_id = envelope_id
        self.account_id = account_id
        self.grouping = grouping
        self.note = note

class Account:

    def __init__(self, name, balance):
        self.id = None
        self.name = name
        self.balance = balance

class Envelope:

    def __init__(self, name, balance, budget):
        self.id = None
        self.name = name
        self.balance = balance
        self.budget = budget


def create_db():
    c.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY,
            type INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            day DATE NOT NULL,
            envelope_id INTEGER,
            account_id INTEGER,
            grouping INTEGER NOT NULL DEFAULT 0,
            note TEXT NOT NULL DEFAULT ''
            )
        """)


    c.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            balance REAL NOT NULL DEFAULT 0
            )
        """)

    c.execute("""
        CREATE TABLE envelopes (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            balance REAL NOT NULL DEFAULT 0,
            budget REAL NOT NULL DEFAULT 0
            )
        """)
    insert_envelope('Unallocated', 0)


#TRANSACTION FUNCTIONS
def insert_transaction(t):
    with conn:
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (t.id, t.type, t.name, t.amt, t.date, t.envelope_id, t.account_id,  t.grouping, t.note))

        if (t.type != ENVELOPE_TRANSFER):
            newaccountbalance = get_account_balance(t.account_id) - t.amt
            update_account_balance(t.account_id, newaccountbalance)

        if (t.type != ACCOUNT_TRANSFER):
            if not (t.envelope_id is None):
                newenvelopebalance = get_envelope_balance(t.envelope_id) - t.amt
                update_envelope_balance(t.envelope_id, newenvelopebalance)

def get_transaction(id):
    with conn:
        c.execute("SELECT * FROM transactions WHERE id=?", (id,))
        tdata = c.fetchone()
        t = Transaction(tdata[1],tdata[2],tdata[3],tdata[4],tdata[5],tdata[6],tdata[7],tdata[8])
        t.id = tdata[0]
        return t

def get_all_transactions():
    with conn:
        c.execute("SELECT id FROM transactions ORDER by day DESC")
        ids = c.fetchall()
        tlist = []
        split_grouped = []
        for id in ids:
            t = get_transaction(id[0])
            if (t.grouping not in split_grouped or t.grouping == 0):
                if (t.type == SPLIT_TRANSACTION):
                    split_grouped.append(t.grouping)
                t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
                t.amt = '$%.2f' % (t.amt * -1)
                # t.type = type_to_icon(t.type)
                if not (t.account_id is None):
                    t.account_id = get_account(t.account_id).name
                if not (t.envelope_id is None):
                    t.envelope_id = get_envelope(t.envelope_id).name
                tlist.append(t)
        return tlist

def get_envelope_transactions(envelope_id):
    with conn:
        c.execute("SELECT id FROM transactions WHERE envelope_id=? ORDER by day DESC", (envelope_id,))
        ids = c.fetchall()
        tlist = []
        for id in ids:
            t = get_transaction(id[0])
            t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
            t.amt = '$%.2f' % (t.amt * -1)
            # t.type = type_to_icon(t.type)
            if not (t.account_id is None):
                t.account_id = get_account(t.account_id).name
            if not (t.envelope_id is None):
                t.envelope_id = get_envelope(t.envelope_id).name
            tlist.append(t)
        return tlist

def get_account_transactions(account_id):
    with conn:
        c.execute("SELECT id FROM transactions WHERE account_id=? ORDER by day DESC", (account_id,))
        ids = c.fetchall()
        tlist = []
        for id in ids:
            t = get_transaction(id[0])
            t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
            t.amt = '$%.2f' % (t.amt * -1)
            # t.type = type_to_icon(t.type)
            if not (t.account_id is None):
                t.account_id = get_account(t.account_id).name
            if not (t.envelope_id is None):
                t.envelope_id = get_envelope(t.envelope_id).name
            tlist.append(t)
        return tlist

def delete_transaction(id):
    with conn:
        # check if transaction exists (if not grouping is None)
        # get grouping number
        # If grouping == 0, undo transaction and delete
        # Else get ids, undo all transactions, and delete
        grouping = get_grouping_from_id(id)
        if (grouping == 0):
            t = get_transaction(id)
            if not (t.envelope_id is None):
                update_envelope_balance(t.envelope_id, get_envelope_balance(t.envelope_id) + t.amt)
            if not (t.account_id is None):
                update_account_balance(t.account_id, get_account_balance(t.account_id) + t.amt)
            c.execute("DELETE FROM transactions WHERE id=?", (id,))
        elif not (grouping is None):
            ids = get_ids_from_grouping(grouping)
            for i in ids:
                t = get_transaction(i)
                if not (t.envelope_id is None):
                    update_envelope_balance(t.envelope_id, get_envelope_balance(t.envelope_id) + t.amt)
                if not (t.account_id is None):
                    update_account_balance(t.account_id, get_account_balance(t.account_id) + t.amt)
                c.execute("DELETE FROM transactions WHERE id=?", (i,))
        else:
            print("that transaction doesn't exist you twit")


def update_transaction(id, t):
    delete_transaction(id)
    insert_transaction(t)
    #This will change the transaction id(s), but they shouldn't be referenced anywhere else


def new_split_transaction(t):
    #takes arrays of amt and envelope_id and creates individual transactions
    grouping = gen_grouping_num()
    amts = t.amt
    envelopes = t.envelope_id
    for i in range(len(amts)):
        new_t = Transaction(SPLIT_TRANSACTION, t.name, amts[i], t.date, envelopes[i], t.account_id, grouping, t.note)
        insert_transaction(new_t)




#ACCOUNT FUNCTIONS
def insert_account(name, balance):
    with conn:
        c.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, 0))
        c.execute("SELECT id FROM accounts WHERE name=?", (name,))
        account_id = c.fetchone()[0]
        income_name = 'Initial Account Fill: ' + name
        t = Transaction(INCOME, income_name, -1* balance, datetime.datetime.today(), 1, account_id, 0, '')
        insert_transaction(t)

def get_account(id):
    with conn:
        c.execute("SELECT * FROM accounts WHERE id=?", (id,))
        adata = c.fetchone()
        a = Account(adata[1], adata[2])
        a.id = adata[0]
        return a

def get_account_list():
    with conn:
        c.execute("SELECT id FROM accounts ORDER by id ASC")
        ids = c.fetchall()
        alist = []
        for id in ids:
            a= get_account(id[0])
            a.balance = '$%.2f' % a.balance
            alist.append(a)
        return alist

def delete_account(id):
    with conn:
        c.execute("DELETE FROM accounts WHERE id=?", (id,))
        #update total
        #delete all associated transactions?

def get_account_balance(id):
    c.execute("SELECT balance FROM accounts WHERE id=?", (id,))
    balance = c.fetchone()
    if not (balance is None):
        return balance[0]
    else:
        print("that account doesn't exist you twit.")

def update_account_balance(id, balance):
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(round(balance,2), id))
        #take/give difference from envelopes?


def account_transfer(name, amount, date, to_account, from_account, note):
    grouping = gen_grouping_num()
    fill = Transaction(ACCOUNT_TRANSFER, name, -1 * amount, date, None, to_account, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ACCOUNT_TRANSFER, name, amount, date, None, from_account, grouping, note)
    insert_transaction(empty)

def update_account_name(id, name):
    with conn:
        c.execute("UPDATE accounts SET name=? WHERE id=?", (name, id))



#ENVELOPE FUNCTIONS
def insert_envelope(name, budget):
    with conn:
        c.execute("INSERT INTO envelopes (name, budget) VALUES (?, ?)", (name,budget))

def get_envelope(id):
    with conn:
        c.execute("SELECT * FROM envelopes WHERE id=?", (id,))
        edata = c.fetchone()
        e = Envelope(edata[1], edata[2], edata[3])
        e.id = edata[0]
        return e

def get_envelope_list():
    with conn:
        c.execute("SELECT id FROM envelopes ORDER by id ASC")
        ids = c.fetchall()
        elist = []
        for id in ids:
            e = get_envelope(id[0])
            e.balance = '$%.2f' % e.balance
            e.budget = '$%.2f' % e.budget
            elist.append(e)
        return elist

def delete_envelope(id):
    with conn:
        if (id != 1):
            c.execute("DELETE FROM envelopes WHERE id=?", (id,))
            #archive it somehow and remove add its balance to the unallocated envelope??? (but what if it's negative tho?)
        else:
            print("You can't delete the 'Unallocated' envelope you moron")

def get_envelope_balance(id):
    c.execute("SELECT balance FROM envelopes WHERE id=?", (id,))
    balance = c.fetchone()
    if not (balance is None):
        return balance[0]
    else:
        print("that envelope doesn't exist you imbicil")


def update_envelope_balance(id, balance):
    with conn:
        c.execute("UPDATE envelopes SET balance=? WHERE id=?",(round(balance,2), id))
        #this isn't possible as a stand alone action

def update_envelope_budget(id, budget):
    with conn:
        c.execute("UPDATE envelopes SET budget=? WHERE id=?",(budget, id))

def update_envelope_name(id, name):
    with conn:
        c.execute("UPDATE envelopes SET name=? WHERE id=?", (name, id))

def envelope_transfer(name, amt, date, to_envelope, from_envelope, note):
    grouping = gen_grouping_num()
    fill = Transaction(ENVELOPE_TRANSFER, name, -1 * amt, date, to_envelope, None, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ENVELOPE_TRANSFER, name, amt, date, from_envelope, None, grouping, note)
    insert_transaction(empty)


#OTHER FUNCTIONS
def print_database():
    print()
    print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
    c.execute("SELECT * FROM transactions")
    print("Transactions:")
    for row in c:
        print(row)
    print()

    print('Accounts:')
    c.execute("SELECT * FROM accounts")
    for row in c:
        print(row)
    print()

    print('Envelopes:')
    c.execute("SELECT * FROM envelopes")
    for row in c:
        print(row)
    print()
    print("TOTAL FUNDS: ", round(get_total(),2))
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    print()


def get_total():
    with conn:
        c.execute("SELECT SUM(balance) FROM accounts")
        total = c.fetchone()[0]
        return total

def gen_grouping_num():
    with conn:
        c.execute("SELECT MAX(grouping) FROM transactions")
        prenum = c.fetchone()[0]
        if prenum != 0:
            newnum = prenum + 1
        else:
            newnum = 1

        return newnum

def get_grouping_from_id(id):
    with conn:
        c.execute("SELECT grouping FROM transactions WHERE id=?", (id,))
        grouping_touple = c.fetchone()
        if (grouping_touple is None):
            print("There is no transaction with this id: ", id)
        else:
            grouping = grouping_touple[0]
            return grouping

def get_ids_from_grouping(grouping):
    with conn:
        if (grouping == 0):
            print("Grouping = 0")
        else:
            c.execute("SELECT id from transactions WHERE grouping=?", (grouping,))
            id_touple = c.fetchall()
            id_array = []
            for i in id_touple:
                id = i[0]
                id_array.append(id)
            return id_array

def type_to_icon(x):
    return {
        0: 'local_atm',
        1: 'swap_horiz',
        2: 'swap_vert',
        3: 'vertical_align_bottom',
        4: 'call_split',
    }[x]

# def icon_to_text(x):
#     return = {
#         'local_atm': 'Basic Transaction',
#         'swap_horiz': 'Envelope Transfer',
#         'swap_vert': 'Account Transfer',
#         'vertical_align_bottom': 'Income',
#         'call_split': 'Split Transaction'
#     }[x]


def main():

    # create_db()

    # delete previous tests
    # for i in range(40):
    #     delete_transaction(i)
    # delete_envelope(1)
    # delete_envelope(2)
    # delete_envelope(3)
    # delete_account(1)
    # delete_account(2)

    # #create new testing envelopes and accounts
    # insert_account('Checking', 100)
    # insert_account('Savings', 1000)
    # insert_envelope('Food',10)
    # insert_envelope('Gas',100)

    print_database()


    # #test basic transaction
    # print("Transactions Test:")
    # t1 = Transaction(BASIC_TRANSACTION,'Target', 1.23, datetime.datetime(1999, 12, 30), 1, 1, 0, '')
    # insert_transaction(t1)
    # t2 = Transaction(BASIC_TRANSACTION,'Walmart', 19.23, datetime.datetime(2000, 8, 13), 2, 2, 0, 'Something cool')
    # insert_transaction(t2)
    # print_database()
    # get_total()

    # #test income
    # # print("Income Test:")
    # # new_income(1, 100000, 'Lottery Money', 'Yay!', 2)
    # # print_database()

    # #test envelope transfer
    # print("Envelope Transfer Test:")
    # envelope_transfer('Envelope Swapperoo', 0.77, datetime.datetime(2000, 8, 13), 1, 2, 'Will this work?')
    # envelope_transfer('Envelope Swapperoo too', 1.00, datetime.datetime(2000, 8, 13), 1, 2, 'Will this work too?')
    # print_database()

    # #account transfer test
    # print("Account Transfer Test:")
    # account_transfer("Account Swapperz", 0.77, datetime.datetime(2000, 8, 13), 1, 2, 'Note goes here')
    # print_database()


    # #delete basic transaction test
    # print("delete basic transaction test")
    # delete_transaction(3)
    # print_database()

    # #delete grouped transaction test
    # print("delete grouped transaction test (envelope swap)")
    # delete_transaction(4)
    # print_database()
    # print("delete grouped transaction test (account swap)")
    # delete_transaction(8)
    # print_database()

    # #update envelope budget test
    # update_envelope_budget(1, 10000)
    # print_database()

    # #split transaction test
    # print("Split transaction test")
    # new_split_transaction(Transaction(SPLIT_TRANSACTION,'Gooten', [10, 5], datetime.datetime(2000, 8, 13), [2, 1], 2, 0, 'Something cool'))
    # print_database()
    # print("Delete split transaction test")
    # delete_transaction(9)
    # print_database()


    #update basic transaction test
    #update_transaction(1, Transaction(BASIC_TRANSACTION,'Target', 10.23, datetime.datetime(1999, 12, 30), 'Food', 'Checking', 0, ''))

    #update transfer transaction test
    #update_transaction(4, Transaction(ENVELOPE_TRANSFER,'Swapperoo noo', 1.77, datetime.datetime(2000, 8, 13), 'Gas', 'Savings', 0, 'Something cool'))




    conn.close()

if __name__ == "__main__":
    main()