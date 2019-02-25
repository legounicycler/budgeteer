import sqlite3
import datetime

database = 'C:\\Users\\norma\Dropbox\\database.sqlite'
conn = sqlite3.connect(database)

c = conn.cursor()

BASIC_TRANSACTION = 0
ENVELOPE_TRANSFER = 1
ACCOUNT_TRANSFER = 2
INCOME = 3
SPLIT_TRANSACTION = 4


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

    def __init__(self, id, name, balance):
        self.id = id
        self.name = name
        self.balance = balance

class Envelope:

    def __init__(self, id, name, balance, budget):
        self.id = id
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


#TRANSACTION FUNCTIONS
def insert_transaction(t):
    with conn:
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (t.id, t.type, t.name, t.amt, t.date, t.envelope_id, t.account_id,  t.grouping, t.note))

        if (t.type != ENVELOPE_TRANSFER):
            c.execute("SELECT balance FROM accounts WHERE id=?", (t.account_id,))
            accountbalance = c.fetchone()[0] - t.amt
            update_account(t.account_id, accountbalance)

        if (t.type != ACCOUNT_TRANSFER):
            c.execute("SELECT balance FROM envelopes WHERE id=?", (t.envelope_id,))
            envelopebalance = c.fetchone()[0] - t.amt
            update_envelope_balance(t.envelope_id, envelopebalance)

def get_transaction(id):
    with conn:
        c.execute("SELECT * FROM transactions WHERE id=?", (id,))
        return c.fetchall()

def delete_transaction(id):
    with conn:
        # check if transaction exists (if not grouping is None)
        # get grouping number
        # If grouping = 0, undo transaction and delete
        # Else get ids, undo all transactions, and delete

        grouping = get_grouping_from_id(id)
        if (grouping == 0):
            #undo transaction
            c.execute("SELECT amount FROM transactions WHERE id=?", (id,))
            amt = c.fetchone()[0]
            c.execute("SELECT envelope_id FROM transactions WHERE id=?", (id,))
            envelope_id = c.fetchone()[0]
            c.execute("SELECT account_id FROM transactions WHERE id=?", (id,))
            account_id = c.fetchone()[0]
            if not (envelope_id is None):
                update_envelope_balance(envelope_id, get_envelope_balance(envelope_id) + amt)
            if not (account_id is None):
                update_account(account_id, get_account_balance(account_id) + amt)
            #delete transaction
            c.execute("DELETE FROM transactions WHERE id=?", (id,))
        elif not (grouping is None):
            #get array of ids
            ids = get_ids_from_grouping(grouping)
            for i in ids:
                #undo transaction
                c.execute("SELECT amount FROM transactions WHERE id=?", (i,))
                amt = c.fetchone()[0]
                c.execute("SELECT envelope_id FROM transactions WHERE id=?", (i,))
                envelope_id = c.fetchone()[0]
                c.execute("SELECT account_id FROM transactions WHERE id=?", (i,))
                account_id = c.fetchone()[0]
                if not (envelope_id is None):
                    update_envelope_balance(envelope_id, get_envelope_balance(envelope_id) + amt)
                if not (account_id is None):
                    update_account(account_id, get_account_balance(account_id) + amt)
                #delete transaction
                c.execute("DELETE FROM transactions WHERE id=?", (i,))


def update_transaction(id, t):
    #check for grouping
    #delete old transactions
    #add updated transactions
    with conn:
        c.execute("SELECT * FROM transactions WHERE id=?",(id,))
        pass

def new_split_transaction(t):
    #take arrays of amt and envelope and create individual transactions
    grouping = gen_grouping_num()
    amts = t.amt
    envelopes = t.envelope_id
    for i in range(len(amts)):
        new_t = Transaction(SPLIT_TRANSACTION, t.name, amts[i], t.date, envelopes[i], t.account_id, grouping, t.note)
        insert_transaction(new_t)

def retrieve_transaction(id):
    with conn:
        c.execute("SELECT * FROM transactions WHERE id=?",(id,))



#ACCOUNT FUNCTIONS
def insert_account(name, balance):
    with conn:
        c.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, balance))

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
        print("This account doesn't exist you twit.")

def update_account(id, balance):
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(round(balance,2), id))

def new_income(account_id, amount, name, note, envelope_id):
    with conn:
        t = Transaction(INCOME, name, -1 * amount, datetime.datetime.today(), envelope_id, account_id, 0, note)
        insert_transaction(t)
def account_transfer(name, to, From, amount, note):
    grouping = gen_grouping_num()
    fill = Transaction(ACCOUNT_TRANSFER, name, -1 * amount, datetime.datetime.today(), None, to, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ACCOUNT_TRANSFER, name, amount, datetime.datetime.today(), None, From, grouping, note)
    insert_transaction(empty)



#ENVELOPE FUNCTIONS
def insert_envelope(name, budget):
    with conn:
        c.execute("INSERT INTO envelopes (name, budget) VALUES (?, ?)", (name,budget))

def delete_envelope(id):
    with conn:
        c.execute("DELETE FROM envelopes WHERE id=?", (id,))
        #delete all transactions from that envelope (but what happens if there's a split transaction?)

def get_envelope_balance(id):
    c.execute("SELECT balance FROM envelopes WHERE id=?", (id,))
    balance = c.fetchone()
    if not (balance is None):
        return balance[0]


def update_envelope_balance(id, balance):
    with conn:
        c.execute("UPDATE envelopes SET balance=? WHERE id=?",(round(balance,2), id))

def update_envelope_budget(id, budget):
    with conn:
        c.execute("UPDATE envelopes SET budget=? WHERE id=?",(budget, id))

def envelope_transfer(name, to, From, amount, note):
    grouping = gen_grouping_num()
    fill = Transaction(ENVELOPE_TRANSFER, name, -1 * amount, datetime.datetime.today(), to, None, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ENVELOPE_TRANSFER, name, amount, datetime.datetime.today(), From, None, grouping, note)
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



def main():

    #create_db()

    #delete previous tests
    for i in range(40):
        delete_transaction(i)
    delete_envelope(1)
    delete_envelope(2)
    delete_account(1)
    delete_account(2)

    #create new testing envelopes and accounts
    insert_envelope('Food',10)
    insert_envelope('Gas',100)
    insert_account('Checking', 100)
    insert_account('Savings', 1000)
    update_envelope_balance(1,500)
    update_envelope_balance(2,600)

    print_database()


    #test basic transaction
    print("Transactions Test:")
    t1 = Transaction(BASIC_TRANSACTION,'Target', 1.23, datetime.datetime(1999, 12, 30), 1, 1, 0, '')
    insert_transaction(t1)
    t2 = Transaction(BASIC_TRANSACTION,'Walmart', 19.23, datetime.datetime(2000, 8, 13), 2, 2, 0, 'Something cool')
    insert_transaction(t2)
    print_database()
    get_total()

    #test income
    print("Income Test:")
    new_income(1, 100000, 'Lottery Money', 'Yay!', 2)
    print_database()

    #test envelope transfer
    print("Envelope Transfer Test:")
    envelope_transfer('Envelope Swapperoo', 1, 2, 0.77, 'Will this work?')
    envelope_transfer('Envelope Swapperoo too', 1, 2, 1.00, 'Will this work too?')
    print_database()

    #account transfer test
    print("Account Transfer Test:")
    account_transfer("Account Swapperz", 1, 2, 0.77, 'Note goes here')
    print_database()


    #delete basic transaction test
    print("delete basic transaction test")
    delete_transaction(3)
    print_database()

    #delete grouped transaction test
    print("delete grouped transaction test (envelope swap)")
    delete_transaction(4)
    print_database()
    print("delete grouped transaction test (account swap)")
    delete_transaction(8)
    print_database()

    #update envelope budget test
    update_envelope_budget(1, 10000)
    print_database()

    #split transaction test
    print("Split transaction test")
    new_split_transaction(Transaction(SPLIT_TRANSACTION,'Gooten', [10, 5], datetime.datetime(2000, 8, 13), [2, 1], 2, 0, 'Something cool'))
    print_database()
    print("Delete split transaction test")
    delete_transaction(9)
    print_database()

    #update basic transaction test
    #update_transaction(1, Transaction(BASIC_TRANSACTION,'Target', 10.23, datetime.datetime(1999, 12, 30), 'Food', 'Checking', 0, ''))

    #update transfer transaction test
    #update_transaction(4, Transaction(ENVELOPE_TRANSFER,'Swapperoo noo', 1.77, datetime.datetime(2000, 8, 13), 'Gas', 'Savings', 0, 'Something cool'))




    conn.close()

if __name__ == "__main__":
    main()