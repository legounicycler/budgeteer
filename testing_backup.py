import sqlite3
import datetime

database = 'C:\\Users\\norma\Dropbox\\database.sqlite'
conn = sqlite3.connect(database)

c = conn.cursor()

BASIC_TRANSACTION = 0
ENVELOPE_TRANSFER = 1
ACCOUNT_TRANSFER = 2
INCOME = 3




#change envelopes/accounts to id system
#rename envelope/accounts in Transaction to envelope_id etc.
#foreign keys



class Transaction:

    def __init__(self, type, name, amt, date, envelope, account, note):
        self.id = None
        self.type = type
        self.name = name
        self.amt = amt
        self.date = date
        self.envelope = envelope
        self.account = account
        self.note = note

class Account:

    def __init__(self, name, balance):
        self.id = None
        self.name = name
        self.balance = balance

class Envelope:

    def __init__(self, name, balance):
        self.id = None
        self.name = name
        self.balance = balance


def create_db():
    c.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY,
            type INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            day DATE NOT NULL,
            envelope INTEGER NOT NULL,
            account INTEGER NOT NULL,
            note TEXT NOT NULL DEFAULT ''
            )
            """)


    c.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0
            )
        """)

    c.execute("""
        CREATE TABLE envelopes (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0
            )
        """)


#TRANSACTION FUNCTIONS
def insert_transaction(t):
    with conn:
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (t.id, t.type, t.name, t.amt, t.date, t.envelope, t.account, t.note))

        if (t.type != ENVELOPE_TRANSFER):
            c.execute("SELECT balance FROM accounts WHERE name=?", (t.account,))
            accountbalance = c.fetchone()[0] - t.amt
            update_account(t.account, accountbalance)

        if (t.type != ACCOUNT_TRANSFER):
            c.execute("SELECT balance FROM envelopes WHERE name=?", (t.envelope,))
            envelopebalance = c.fetchone()[0] - t.amt
            update_envelope(t.envelope, envelopebalance)

def get_transaction(id):
    c.execute("SELECT * FROM transactions WHERE id=?", (id,))
    return c.fetchall()

def delete_transaction(id):
    with conn:
        c.execute("DELETE FROM transactions WHERE id=?", (id,))

def update_transaction(id):
    pass



#ACCOUNT FUNCTIONS
def new_account(name, balance):
    with conn:
        c.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, balance))

def delete_account(name):
    with conn:
        c.execute("DELETE FROM accounts WHERE name=?", (name,))

def update_account(id, balance):
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(balance, id))

def account_transfer(name, to, From, amount, note):
    pass

def new_income(account, amount, name, note, envelope):
    with conn:
        t = Transaction(INCOME, name, -1 * amount, datetime.datetime.today(), envelope, account, note)
        insert_transaction(t)
def account_transfer(name, to, From, amount, note):
    fill = Transaction(ACCOUNT_TRANSFER, name, -1 * amount, datetime.datetime.today(), None, to, note)
    insert_transaction(fill)
    empty = Transaction(ACCOUNT_TRANSFER, name, amount, datetime.datetime.today(), None, From, note)
    insert_transaction(empty)



#ENVELOPE FUNCTIONS
def new_envelope(name):
    with conn:
        c.execute("INSERT INTO envelopes (name) VALUES (?)", (name,))

def delete_envelope(name):
    with conn:
        c.execute("DELETE FROM envelopes WHERE name=?", (name,))

def update_envelope(id, balance):
    with conn:
        c.execute("UPDATE envelopes SET balance=? WHERE id=?",(balance, id))

def envelope_transfer(name, to, From, amount, note):
    fill = Transaction(ENVELOPE_TRANSFER, name, -1 * amount, datetime.datetime.today(), to, None, note)
    insert_transaction(fill)
    empty = Transaction(ENVELOPE_TRANSFER, name, amount, datetime.datetime.today(), From, None, note)
    insert_transaction(empty)


#OTHER FUNCTIONS
def print_database():
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

def get_account_id(name):
    with conn:
        c.execute("SELECT id FROM accounts WHERE name=?", (name,))
        return c.fetchone()[0]

def get_envelope_id(name):
    with conn:
        c.execute("SELECT id FROM envelopes WHERE name=?", (name,))
        return c.fetchone()[0]

def get_total():
    with conn:
        c.execute("SELECT SUM(balance) FROM accounts;" )
        total = c.fetchone()[0]
        print(total) #temporary for debugging purposes
        return total


def main():

    #delete previous tests
    delete_envelope('Food')
    delete_envelope('Gas')
    delete_envelope('fun')
    delete_account('Checking')
    delete_account('Savings')
    delete_transaction(0)
    delete_transaction(1)
    delete_transaction(2)
    delete_transaction(3)
    delete_transaction(4)
    delete_transaction(5)
    delete_transaction(6)
    delete_transaction(7)
    delete_transaction(8)
    delete_transaction(9)
    delete_transaction(10)
    delete_transaction(11)
    delete_transaction(12)

    #create new testing envelopes and accounts
    new_envelope('Food')
    new_envelope('Gas')
    new_account('Checking', 100)
    new_account('Savings', 1000)
    update_envelope('Food',500)
    update_envelope('Gas',600)

    print_database()
    get_total()

    #get id tests
    print("GET ID TEST:")
    print(get_account_id('Checking'))
    print(get_envelope_id('Gas'))

    #test basic transaction
    print("Transactions Test:")
    t1 = Transaction(BASIC_TRANSACTION,'Target', 1.23, datetime.datetime(1999, 12, 30), 'Food', 'Checking', '')
    insert_transaction(t1)
    t2 = Transaction(BASIC_TRANSACTION,'Walmart', 19.23, datetime.datetime(2000, 8, 13), 'Gas', 'Savings', 'Something cool')
    insert_transaction(t2)
    print_database()

    #test income
    print("Income Test:")
    new_income('Checking', 100000, 'Lottery Money', 'Yay!', 'Gas')
    print_database()

    #test envelope transfer
    print("Envelope Transfer Test:")
    envelope_transfer('Swapperoo', 'Food', 'Gas', 0.77, 'Will this work?')
    print_database()

    #account transfer test
    print("Account Transfer Test:")
    account_transfer("Swapperz", 'Checking', 'Savings', 0.77, 'Note goes here')
    print_database()



    conn.close()

if __name__ == "__main__":
    main()