import sqlite3
import datetime
import json

database = 'C:\\Users\\norma\Dropbox\\database.sqlite'
conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

UNALLOCATED = 1

BASIC_TRANSACTION = 0
ENVELOPE_TRANSFER = 1
ACCOUNT_TRANSFER = 2
INCOME = 3
SPLIT_TRANSACTION = 4
ENVELOPE_FILL = 5
# PLACEHOLDER = 6

# ------ CLASSES/DATABASE DEFINITIONS ------ #

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
        # schedule
        # current account balance (for easier reconciling)
        # status (reconciled or not)

class Account:
    def __init__(self, name, balance, deleted):
        self.id = None
        self.name = name
        self.balance = balance
        self.deleted = deleted

class Envelope:
    def __init__(self, name, balance, budget, deleted):
        self.id = None
        self.name = name
        self.balance = balance
        self.budget = budget
        self.deleted = deleted

# Creates the database file
def create_db():
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
            note TEXT NOT NULL DEFAULT ''
            -- user_id
            -- schedule
            -- current_account_balance
            )
        """)

    c.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0,
            deleted BOOLEAN NOT NULL DEFAULT 0
            -- user_id
            )
        """)

    c.execute("""
        CREATE TABLE envelopes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0,
            budget INTEGER NOT NULL DEFAULT 0,
            deleted BOOLEAN NOT NULL DEFAULT 0
            -- user_id
            )
        """)

    insert_envelope('Unallocated', 0)


# ---------------TRANSACTION FUNCTIONS--------------- #

def insert_transaction(t):
    # Inserts transaction into database, then updates account/envelope balances
    with conn:
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (t.id, t.type, t.name, t.amt, t.date, t.envelope_id, t.account_id,  t.grouping, t.note))
        if not (t.account_id is None):
            newaccountbalance = get_account_balance(t.account_id) - t.amt
            update_account_balance(t.account_id, newaccountbalance)
        if not (t.envelope_id is None):
            newenvelopebalance = get_envelope_balance(t.envelope_id) - t.amt
            update_envelope_balance(t.envelope_id, newenvelopebalance)

def get_transaction(id):
    # Retrieves transaction object from database given its ID
    c.execute("SELECT * FROM transactions WHERE id=?", (id,))
    tdata = c.fetchone()
    t = Transaction(tdata[1],tdata[2],tdata[3],tdata[4],tdata[5],tdata[6],tdata[7],tdata[8])
    t.id = tdata[0]
    return t

def get_transactions(start, amount):
    # returns a list transactions for display
    # (Groups split transactions and envelope fills and displays their summed total)
    c.execute("SELECT id from TRANSACTIONS GROUP BY (CASE WHEN type = 1 OR type = 2 THEN id ELSE grouping END) ORDER BY day DESC, id DESC LIMIT ? OFFSET ?", (amount, start))
    groupings = c.fetchall()
    print(groupings)
    tlist = []
    for thing in groupings:
        t = get_transaction(thing[0])
        if t.type == SPLIT_TRANSACTION:
            c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=?", (t.grouping,))
            t.amt = c.fetchone()[0]
        elif t.type == ENVELOPE_FILL:
            c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=? AND envelope_id=1", (t.grouping,))
            t.amt = c.fetchone()[0] * -1
        t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
        t.amt = stringify(t.amt * -1)
        tlist.append(t)
    # offset specifies where to start from on the next call
    offset = start + len(tlist)
    # if limit is True you're at the end of the list
    if len(tlist) < amount:
        limit = True
    else:
        limit = False
    return tlist, offset, limit

def get_envelope_transactions(envelope_id, start, amount):
    # returns a list of transactions with a certain envelope_id
    # (ADD LATER?) If the envelope is unallocated, group envelope fill transactions
    c.execute("SELECT id FROM transactions WHERE envelope_id=? ORDER by day DESC, id DESC LIMIT ? OFFSET ?", (envelope_id,amount,start))
    ids = c.fetchall()
    tlist = []
    for id in ids:
        t = get_transaction(id[0])
        t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
        t.amt = stringify(t.amt * -1)
        tlist.append(t)
    # offset specifies where to start from on the next call
    offset = start + len(tlist)
    # if limit is True you're at the end of the list
    if len(tlist) < amount:
        limit = True
    else:
        limit = False
    return tlist, offset, limit

def get_account_transactions(account_id, start, amount):
    # returns a list of transactions with certain account_id
    # (Groups split transactions and displays summed total)
    c.execute("SELECT id, SUM(amount) FROM transactions WHERE account_id=? GROUP BY grouping ORDER by day DESC, id DESC LIMIT ? OFFSET ?", (account_id,amount,start))
    ids = c.fetchall()
    tlist = []
    for thing in ids:
        t = get_transaction(thing[0])
        t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
        t.amt = stringify(thing[1] * -1)
        tlist.append(t)
    # offset specifies where to start from on the next call
    offset = start + len(tlist)
    # if limit is True you're at the end of the list
    if len(tlist) < amount:
        limit = True
    else:
        limit = False
    return tlist, offset, limit

def delete_transaction(id):
    # deletes transaction and associated grouped transactions and updates appropriate envelope/account balances
    with conn:
        grouping = get_grouping_from_id(id)
        if not (grouping is None):
            ids = get_ids_from_grouping(grouping)
            for id in ids:
                t = get_transaction(id)
                # Update envelope balance if it references an envelope
                if not (t.envelope_id is None):
                    if not (get_envelope(t.envelope_id).deleted == True):
                        update_envelope_balance(t.envelope_id, get_envelope_balance(t.envelope_id) + t.amt)
                    else:
                        update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + t.amt)
                # Update account balance if it references an account
                if not (t.account_id is None):
                    if not (get_account(t.account_id).deleted == True):
                        update_account_balance(t.account_id, get_account_balance(t.account_id) + t.amt)
                    else:
                        update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) - t.amt)
                c.execute("DELETE FROM transactions WHERE id=?", (id,))
        else:
            print("That transaction doesn't exist you twit")

def new_split_transaction(t):
    #takes a transaction with arrays of amt and envelope_id and creates individual transactions
    grouping = gen_grouping_num()
    for i in range(len(t.amt)):
        new_t = Transaction(SPLIT_TRANSACTION, t.name, t.amt[i], t.date, t.envelope_id[i], t.account_id, grouping, t.note)
        insert_transaction(new_t)


# ---------------ACCOUNT FUNCTIONS--------------- #

def insert_account(name, balance):
    #inserts new account and creates "initial account balance" transaction
    with conn:
        c.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, 0))
        account_id = c.lastrowid
        income_name = 'Initial Account Balance: ' + name
        t = Transaction(INCOME, income_name, -1 * balance, datetime.date.today(), 1, account_id, gen_grouping_num(), '')
        insert_transaction(t)

def get_account(id):
    # returns account associated with the given id
    c.execute("SELECT * FROM accounts WHERE id=?", (id,))
    adata = c.fetchone()
    a = Account(adata[1], adata[2], adata[3])
    a.id = adata[0]
    return a

def get_account_dict():
    # returns a tuple with a dictionary with keys of account_id and values of account objects
    # and a boolean that says whether there are accounts to render
    c.execute("SELECT id FROM accounts ORDER by id ASC")
    ids = c.fetchall()
    adict = {}
    active_accounts = False
    for id in ids:
        a = get_account(id[0])
        a.balance = stringify(a.balance)
        adict[id[0]] = a
        if a.deleted == 0:
            active_accounts = True
    return (active_accounts, adict)

def delete_account(account_id):
    # subtracts balance from unallocated envelope, sets account balance to 0, and sets deleted to true
    with conn:
        update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) - get_account_balance(account_id))
        c.execute("UPDATE accounts SET deleted=1,balance=0 WHERE id=?", (account_id,))

def get_account_balance(id):
    # Returns float of account balance
    c.execute("SELECT balance FROM accounts WHERE id=?", (id,))
    balance = c.fetchone()
    if not (balance is None):
        return balance[0]
    else:
        print("That account doesn't exist you twit.")

def edit_account(id, name, balance):
    #updates account balalnce and name, then subtracts the change in balance from the unallocated envelope
    with conn:
        current_balance = get_account_balance(id)
        diff = current_balance - balance
        unallocated_balance = get_envelope_balance(1)
        new_unallocated_balance = unallocated_balance - diff
        update_envelope_balance(UNALLOCATED, new_unallocated_balance)
        c.execute("UPDATE accounts SET balance=?, name=? WHERE id=?", (balance, name, id))


def update_account_balance(id, balance):
    # updates balance of account with given id
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(balance, id))

def edit_accounts(old_accounts, new_accounts):
    c.execute("SELECT id FROM accounts WHERE deleted=0")
    account_ids = c.fetchall()
    old_ids = []
    # adds id to old_ids then updates the info for the old accounts
    for a in old_accounts:
        old_ids.append(int(a[0]))
        edit_account(int(a[0]), a[1], a[2])
        print("account edited: ", a[0])
    # adds the new accounts
    for a in new_accounts:
        insert_account(a[0], a[1])
        print("account added: ", a[0])
    # deletes accounts that are missing
    for id in account_ids:
        if not (id[0] in old_ids):
            delete_account(id[0])
            print("account deleted: ", id[0])

def account_transfer(name, amount, date, to_account, from_account, note):
    # Creates one transaction draining an account, and one transaction filling another
    grouping = gen_grouping_num()
    fill = Transaction(ACCOUNT_TRANSFER, name, amount, date, None, to_account, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ACCOUNT_TRANSFER, name, -1* amount, date, None, from_account, grouping, note)
    insert_transaction(empty)


# ---------------ENVELOPE FUNCTIONS--------------- #

def insert_envelope(name, budget):
    # Inserts an envelope into the database with givne name and budget and a balnce of 0
    with conn:
        c.execute("INSERT INTO envelopes (name, budget) VALUES (?, ?)", (name,budget))

def get_envelope(id):
    # returns an envelope object given an envelope_id
    c.execute("SELECT * FROM envelopes WHERE id=?", (id,))
    edata = c.fetchone()
    e = Envelope(edata[1], edata[2], edata[3], edata[4])
    e.id = edata[0]
    return e

def get_envelope_dict():
    # returns a dictionary with key of envelope_id and value of an envelope object
    c.execute("SELECT id FROM envelopes ORDER by id ASC")
    ids = c.fetchall()
    edict = {}
    active_envelopes = False
    for id in ids:
        e = get_envelope(id[0])
        e.balance = stringify(e.balance)
        e.budget = stringify(e.budget)
        edict[id[0]] = e
        if e.deleted == 0 and e.id != 1:
            active_envelopes = True
    return (active_envelopes, edict)

def delete_envelope(envelope_id):
    # adds envelope balance to the unallocated envelope, sets balance to 0, and sets deleted to true
    with conn:
        if (envelope_id != UNALLOCATED):
            update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + get_envelope_balance(envelope_id))
            c.execute("UPDATE envelopes SET deleted=1,balance=0 WHERE id=?", (envelope_id,))
        else:
            print("You can't delete the 'Unallocated' envelope you moron")

def get_envelope_balance(id):
    # returns float of envelope balance given id
    c.execute("SELECT balance FROM envelopes WHERE id=?", (id,))
    balance = c.fetchone()
    if not (balance is None):
        return balance[0]
    else:
        print("that envelope doesn't exist you imbicil")


def update_envelope_balance(id, balance):
    # updates envelope balance for given id
    # NOTE: this isn't possible as a stand alone action
    with conn:
        c.execute("UPDATE envelopes SET balance=? WHERE id=?",(balance, id))

def edit_envelope(id, name, budget):
    # updates the name and budget for given id
    with conn:
        c.execute("UPDATE envelopes SET name=?, budget=? WHERE id=?",(name, budget, id))

def edit_envelopes(old_envelopes, new_envelopes):
    # takes info from the envelope editor form and process it accordingly
    c.execute("SELECT id FROM envelopes WHERE deleted=0")
    envelope_ids = c.fetchall()
    envelope_ids.remove((1,)) # gets rid of unallocated id (1) in envelope list
    old_ids = []
    # adds id to old_ids then updates the info for the old envelopes
    for e in old_envelopes:
        old_ids.append(int(e[0]))
        edit_envelope(int(e[0]), e[1], e[2])
    # adds the new envelopes
    for e in new_envelopes:
        insert_envelope(e[0], e[1])
    # deletes envelopes that are missing
    for id in envelope_ids:
        if not (id[0] in old_ids):
            delete_envelope(id[0])

def envelope_transfer(name, amt, date, to_envelope, from_envelope, note):
    # Creates a transaction to fill one envelope and another to empty the other
    grouping = gen_grouping_num()
    fill = Transaction(ENVELOPE_TRANSFER, name, amt, date, to_envelope, None, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ENVELOPE_TRANSFER, name, -1 * amt, date, from_envelope, None, grouping, note)
    insert_transaction(empty)

def envelope_fill(t):
    # Takes a transaction with an array of envelope ids and amounts and creates sub-transactions to fill the envelopes
    if t.type == ENVELOPE_FILL:
        grouping = gen_grouping_num()
        amts = t.amt
        envelopes = t.envelope_id
        for i in range(len(amts)):
            empty_unallocated = Transaction(ENVELOPE_FILL, t.name, amts[i], t.date, UNALLOCATED, None, grouping, t.note)
            insert_transaction(empty_unallocated)
            fill_envelope = Transaction(ENVELOPE_FILL, t.name, amts[i] * -1, t.date, envelopes[i], None, grouping, t.note)
            insert_transaction(fill_envelope)


#OTHER FUNCTIONS
def print_database():
    print()
    print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
    c.execute("SELECT * FROM transactions ORDER BY day DESC, id DESC")
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
    print("TOTAL FUNDS: ", get_total())
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    print()


def get_total():
    # Sums the account balances to get a total to display
    c.execute("SELECT SUM(balance) FROM accounts")
    total = c.fetchone()[0]
    if not total is None:
        return stringify(total)
    else:
        return stringify(0)

def gen_grouping_num():
    # Creates a new and unique grouping number
    c.execute("SELECT MAX(grouping) FROM transactions")
    prevnum = c.fetchone()[0]
    if prevnum is not None:
        newnum = prevnum + 1
    else:
        newnum = 1
    return newnum

def get_grouping_from_id(id):
    # Gets the grouping number from the given id
    c.execute("SELECT grouping FROM transactions WHERE id=?", (id,))
    grouping_touple = c.fetchone()
    if (grouping_touple is None):
        print("There is no transaction with this id: ", id)
    else:
        return grouping_touple[0]

def get_ids_from_grouping(grouping):
    # returns a list of ids associated with a particular grouping number
    id_array = []
    c.execute("SELECT id from transactions WHERE grouping=?", (grouping,))
    id_touple = c.fetchall()
    for i in id_touple:
        id_array.append(i[0])
    return id_array

def type_to_icon(x):
    # given a numeric transaction type, return the string name for the materialize icon
    return {
        0: 'local_atm',
        1: 'swap_horiz',
        2: 'swap_vert',
        3: 'vertical_align_bottom',
        4: 'call_split',
        5: 'input'
    }[x]

def get_grouped_json(id):
    # Given an id, return a json with the transaction data for each grouped transaction
    grouping = get_grouping_from_id(id)
    ids = get_ids_from_grouping(grouping)
    data = {}
    data['transactions'] = []
    for id in ids:
        t = get_transaction(id)
        data['transactions'].append({
            'id': t.id,
            'name': t.name,
            'amt': t.amt / 100,
            'date': t.date,
            'envelope_id': t.envelope_id,
            'account_id': t.account_id,
            'grouping': t.grouping,
            'note': t.note
        })
    return data

def stringify(number):
    # Formats number into a nice string to display
    negative = number < 0
    string = '$%.2f' % abs(number / 100)
    if negative:
        string = '-' + string
    return string


def main():

    # create_db()


    print_database()

    # print("Starting someid_and_grouping ~fancy~\n")
    get_transactions(7,10)

    conn.close()

if __name__ == "__main__":
    main()