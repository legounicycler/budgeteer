import sqlite3
import datetime
import json

database = 'C:\\Users\\norma\Dropbox\\database.sqlite'
conn = sqlite3.connect(database, check_same_thread=False)

UNALLOCATED = 1
BASIC_TRANSACTION = 0
ENVELOPE_TRANSFER = 1
ACCOUNT_TRANSFER = 2
INCOME = 3
SPLIT_TRANSACTION = 4
PLACEHOLDER = 5


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


def create_db():
    c = conn.cursor()
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
            name TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0,
            deleted BOOLEAN NOT NULL DEFAULT 0
            )
        """)

    c.execute("""
        CREATE TABLE envelopes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0,
            budget REAL NOT NULL DEFAULT 0,
            deleted BOOLEAN NOT NULL DEFAULT 0
            )
        """)
    insert_envelope('Unallocated', 0)


# ---------------TRANSACTION FUNCTIONS--------------- #

def insert_transaction(t):
    # Inserts transaction into database, then updates account/envelope balances
    c = conn.cursor()
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
    c = conn.cursor()
    with conn:
        c.execute("SELECT * FROM transactions WHERE id=?", (id,))
        tdata = c.fetchone()
        t = Transaction(tdata[1],tdata[2],tdata[3],tdata[4],tdata[5],tdata[6],tdata[7],tdata[8])
        t.id = tdata[0]
        return t

def get_all_transactions():
    # returns a list of all transactions with split transactions merged into one
    # Change later to take 2 inputs, where to start, and how many to fetch
    c = conn.cursor()
    with conn:
        c.execute("SELECT id FROM transactions ORDER by day DESC, id DESC")
        ids = c.fetchall()
        tlist = []
        split_grouped = []
        for id in ids:
            t = get_transaction(id[0])
            if (t.grouping not in split_grouped or t.grouping == 0):
                if (t.type == SPLIT_TRANSACTION):
                    split_grouped.append(t.grouping)
                    c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=?", (t.grouping,))
                    t.amt = c.fetchone()[0]
                t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
                t.amt = stringify(t.amt * -1)
                tlist.append(t)
        return tlist

def get_envelope_transactions(envelope_id):
    # returns a list of transactions with certain envelope_id
    # Change later to take 3 inputs: envelope_id, where to start, and how many to fetch
    c = conn.cursor()
    with conn:
        c.execute("SELECT id FROM transactions WHERE envelope_id=? ORDER by day DESC, id DESC", (envelope_id,))
        ids = c.fetchall()
        tlist = []
        for id in ids:
            t = get_transaction(id[0])
            t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
            t.amt = stringify(t.amt * -1)
            tlist.append(t)
        return tlist

def get_account_transactions(account_id):
    # returns a list of transactions with certain account_id
    # Change later to take 3 inputs: account_id, where to start, and how many to fetch
    c = conn.cursor()
    with conn:
        c.execute("SELECT id FROM transactions WHERE account_id=? ORDER by day DESC, id DESC", (account_id,))
        ids = c.fetchall()
        tlist = []
        for id in ids:
            t = get_transaction(id[0])
            t.date =  t.date[5:7] + '/' + t.date[8:10] + '/' + t.date[0:4]
            t.amt = stringify(t.amt * -1)
            tlist.append(t)
        return tlist

def delete_transaction(id):
    # deletes transaction and all grouped transactions and updates appropriate envelope/account balances
    c = conn.cursor()
    with conn:
        grouping = get_grouping_from_id(id)
        if not (grouping is None):
            ids = get_ids_from_grouping(grouping)
            if ids is None:
                ids = [id]
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
    #takes arrays of amt and envelope_id and creates individual transactions
    grouping = gen_grouping_num()
    amts = t.amt
    envelopes = t.envelope_id
    for i in range(len(amts)):
        new_t = Transaction(SPLIT_TRANSACTION, t.name, amts[i], t.date, envelopes[i], t.account_id, grouping, t.note)
        insert_transaction(new_t)


# ---------------ACCOUNT FUNCTIONS--------------- #

def insert_account(name, balance):
    #inserts new account and creates "initial account balance" transaction
    c = conn.cursor()
    with conn:
        c.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, 0))
        account_id = c.lastrowid
        income_name = 'Initial Account Balance: ' + name
        t = Transaction(INCOME, income_name, -1 * balance, datetime.date.today(), 1, account_id, 0, '')
        insert_transaction(t)

def get_account(id):
    # returns account associated with the given id
    c = conn.cursor()
    with conn:
        c.execute("SELECT * FROM accounts WHERE id=?", (id,))
        adata = c.fetchone()
        a = Account(adata[1], adata[2], adata[3])
        a.id = adata[0]
        return a

def get_account_dict():
    # returns a tuple with a dictionary with keys of account_id and values of account objects
    # and a boolean that says whether there are accounts to render
    c = conn.cursor()
    with conn:
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
    c = conn.cursor()
    with conn:
        update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) - get_account_balance(account_id))
        c.execute("UPDATE accounts SET deleted=1,balance=0 WHERE id=?", (account_id,))

def get_account_balance(id):
    # Returns float of account balance
    c = conn.cursor()
    with conn:
        c.execute("SELECT balance FROM accounts WHERE id=?", (id,))
        balance = c.fetchone()
        if not (balance is None):
            return balance[0]
        else:
            print("That account doesn't exist you twit.")

def edit_account(id, name, balance):
    #updates account balalnce and name, then subtracts the change in balance from the unallocated envelope
    c = conn.cursor()
    with conn:
        current_balance = get_account_balance(id)
        diff = current_balance - balance
        unallocated_balance = get_envelope_balance(1)
        new_unallocated_balance = unallocated_balance - diff
        update_envelope_balance(UNALLOCATED, new_unallocated_balance)
        c.execute("UPDATE accounts SET balance=?, name=? WHERE id=?", (balance, name, id))


def update_account_balance(id, balance):
    # updates balance of account with given id
    c = conn.cursor()
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(round(balance,2), id))

def edit_accounts(json_data):
    # Given json data with keys of account_id and value of other account data
    # update accounts that already exist, add new ones, and delete those that are missing from the json_data
    c = conn.cursor()
    with conn:
        c.execute("SELECT id FROM accounts WHERE deleted=0")
        account_ids = c.fetchall()
    form_ids = []
    print(json_data)
    for x in json_data:
        print(x)
        account_id = float(x)
        account_name = json_data[x][0]
        account_balance = float(json_data[x][1])
        # If an id is an integer, it already exists; if it's a decimal, it's a new one
        if (account_id % 1) == 0:
            account_id = int(account_id)
            form_ids.append(account_id)
            edit_account(account_id, account_name, account_balance)
        else:
            insert_account(account_name, account_balance)

    for id in account_ids:
        # if the id from the existing accounts isn't in the json_data, delete the account
        if not (id[0] in form_ids):
            delete_account(id[0])

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
    c = conn.cursor()
    with conn:
        c.execute("INSERT INTO envelopes (name, budget) VALUES (?, ?)", (name,budget))

def get_envelope(id):
    # returns an envelope object given an envelope_id
    c = conn.cursor()
    with conn:
        c.execute("SELECT * FROM envelopes WHERE id=?", (id,))
        edata = c.fetchone()
        e = Envelope(edata[1], edata[2], edata[3], edata[4])
        e.id = edata[0]
        return e

def get_envelope_dict():
    # returns a dictionary with key of envelope_id and value of an envelope object
    c = conn.cursor()
    with conn:
        c.execute("SELECT id FROM envelopes ORDER by id ASC")
        ids = c.fetchall()
        edict = {}
        active_envelopes = False
        for id in ids:
            e = get_envelope(id[0])
            e.balance = stringify(e.balance)
            e.budget = stringify(e.budget)
            edict[id[0]] = e
            if e.deleted == 0:
                active_envelopes = True
        return (active_envelopes, edict)

def delete_envelope(envelope_id):
    # adds envelope balance to the unallocated envelope, sets balance to 0, and sets deleted to true
    c = conn.cursor()
    with conn:
        if (envelope_id != UNALLOCATED):
            update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + get_envelope_balance(envelope_id))
            c.execute("UPDATE envelopes SET deleted=1,balance=0 WHERE id=?", (envelope_id,))
        else:
            print("You can't delete the 'Unallocated' envelope you moron")

def get_envelope_balance(id):
    # returns float of envelope balance given id
    c = conn.cursor()
    with conn:
        c.execute("SELECT balance FROM envelopes WHERE id=?", (id,))
        balance = c.fetchone()
        if not (balance is None):
            return balance[0]
        else:
            print("that envelope doesn't exist you imbicil")


def update_envelope_balance(id, balance):
    # updates envelope balance for given id
    c = conn.cursor()
    with conn:
        c.execute("UPDATE envelopes SET balance=? WHERE id=?",(round(balance,2), id))
        #this isn't possible as a stand alone action

def edit_envelope(id, name, budget):
    # updates the name and budget for given id
    c = conn.cursor()
    with conn:
        c.execute("UPDATE envelopes SET name=?, budget=? WHERE id=?",(name, budget, id))

def edit_envelopes(json_data):
    #takes a json file with keys of envelope id and values of envelope data and processes it
    c = conn.cursor()
    with conn:
        c.execute("SELECT id FROM envelopes WHERE deleted=0")
        envelope_ids = c.fetchall()
        envelope_ids.remove((1,)) # gets rid of unallocated id (1) in envelope list

    form_ids = []
    for x in json_data:
        id = float(x)
        envelope_name = json_data[x][0]
        envelope_budget = float(json_data[x][1])
        if (id % 1) == 0:
            id = int(id)
            form_ids.append(id)
            edit_envelope(id, envelope_name, envelope_budget)
        else:
            insert_envelope(envelope_name, envelope_budget)

    for id in envelope_ids:
        if not (id[0] in form_ids):
            delete_envelope(id[0])

def envelope_transfer(name, amt, date, to_envelope, from_envelope, note):
    # Creates a transaction to fill one envelope and another to empty the other
    grouping = gen_grouping_num()
    fill = Transaction(ENVELOPE_TRANSFER, name, amt, date, to_envelope, None, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ENVELOPE_TRANSFER, name, -1 * amt, date, from_envelope, None, grouping, note)
    insert_transaction(empty)


#OTHER FUNCTIONS
def print_database():
    c = conn.cursor()
    with conn:
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
    # Sums the account balances to get a total to display
    c = conn.cursor()
    with conn:
        c.execute("SELECT SUM(balance) FROM accounts")
        total = c.fetchone()[0]
        if not total is None:
            return stringify(total)
        else:
            return 0

def gen_grouping_num():
    # Creates a new and unique grouping number
    c = conn.cursor()
    with conn:
        c.execute("SELECT MAX(grouping) FROM transactions")
        prevnum = c.fetchone()[0]
        if prevnum != 0 and prevnum is not None:
            newnum = prevnum + 1
        else:
            newnum = 1
        return newnum

def get_grouping_from_id(id):
    # Gets the grouping number from the given id
    c = conn.cursor()
    with conn:
        c.execute("SELECT grouping FROM transactions WHERE id=?", (id,))
        grouping_touple = c.fetchone()
        if (grouping_touple is None):
            print("There is no transaction with this id: ", id)
        else:
            grouping = grouping_touple[0]
            return grouping

def get_ids_from_grouping(grouping):
    # returns a list of ids associated with a particular grouping number
    c = conn.cursor()
    with conn:
        id_array = []
        if (grouping != 0):
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
    }[x]

def get_grouped_json(id):
    # Given an id, return a json with the transaction data for each grouped transaction
    grouping = get_grouping_from_id(id)
    ids = get_ids_from_grouping(grouping)
    if grouping == 0:
        ids = [id]
    data = {}
    data['transactions'] = []
    for id in ids:
        t = get_transaction(id)
        data['transactions'].append({
            'id': t.id,
            'name': t.name,
            'amt': t.amt,
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
    string = '$%.2f' % abs(number)
    if negative:
        string = '-' + string
    return string


def main():

    # create_db()

    # delete previous tests
    # for i in range(40):
    # delete_transaction(i)
    # delete_envelope(1)
    # delete_envelope(2)
    # delete_envelope(3)
    # delete_account(1)
    # delete_account(2)

    # #create new testing envelopes and accounts
    # insert_account('Checking', 100)
    # insert_account('Savings', 1000)
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