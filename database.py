import sqlite3
import datetime
from datetime import datetime
from datetime import date
import json
import platform

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\Dropbox\\database.sqlite'
else:
    database = '/home/alimiero/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

# Going to have to CHANGE since each user has their own unique unallocated envelope
UNALLOCATED = 1

BASIC_TRANSACTION = 0
ENVELOPE_TRANSFER = 1
ACCOUNT_TRANSFER = 2
INCOME = 3
SPLIT_TRANSACTION = 4
ENVELOPE_FILL = 5
PLACEHOLDER = 6

REMOVE = False
INSERT = True

# Temporary testing user_id
USER_ID = 1

# ------ CLASSES/DATABASE DEFINITIONS ------ #

class Transaction:
    def __init__(self, type, name, amt, date, envelope_id, account_id, grouping, note, schedule, status, user_id, reconcile_balance):
        self.id = None
        self.type = type
        self.name = name
        self.amt = amt
        self.date = date
        self.envelope_id = envelope_id
        self.account_id = account_id
        self.grouping = grouping
        self.note = note
        self.schedule = schedule
        self.status = status
        self.user_id = user_id
        self.reconcile_balance = reconcile_balance
    def __repr__(self):
        return "ID:{}, TYPE:{}, NAME:{}, AMT:{}, DATE:{}, E_ID:{}, A_ID:{}, GRP:{}, NOTE:{}, SCHED:{}, STATUS:{}, U_ID:{}, R_AMT:{}".format(self.id,self.type,self.name,self.amt,self.date,self.envelope_id,self.account_id,self.grouping,self.note,self.schedule,self.status,self.user_id,self.reconcile_balance)
    def __str__(self):
        return "ID:{}, TYPE:{}, NAME:{}, AMT:{}, DATE:{}, E_ID:{}, A_ID:{}, GRP:{}, NOTE:{}, SCHED:{}, STATUS:{}, U_ID:{}, R_AMT:{}".format(self.id,self.type,self.name,self.amt,self.date,self.envelope_id,self.account_id,self.grouping,self.note,self.schedule,self.status,self.user_id,self.reconcile_balance)


class Account:
    def __init__(self, name, balance, deleted, user_id):
        self.id = None
        self.name = name
        self.balance = balance
        self.deleted = deleted
        self.user_id = user_id
    def __repr__(self):
        return "ID:{}, NAME:{}, BAL:{}, DEL:{}, U_ID:{}".format(self.id,self.name,self.balance,self.deleted,self.user_id)
    def __str__(self):
        return "ID:{}, NAME:{}, BAL:{}, DEL:{}, U_ID:{}".format(self.id,self.name,self.balance,self.deleted,self.user_id)


class Envelope:
    def __init__(self, name, balance, budget, deleted, user_id):
        self.id = None
        self.name = name
        self.balance = balance
        self.budget = budget
        self.deleted = deleted
        self.user_id = user_id
    def __repr__(self):
        return "ID:{}, NAME:{}, BAL:{}, BUDG:{}, DEL:{}, U_ID:{}".format(self.id,self.name,self.balance,self.budget,self.deleted,self.user_id)
    def __str__(self):
        return "ID:{}, NAME:{}, BAL:{}, BUDG:{}, DEL:{}, U_ID:{}".format(self.id,self.name,self.balance,self.budget,self.deleted,self.user_id)


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
            note TEXT NOT NULL DEFAULT '',
            schedule TEXT,
            status BOOLEAN NOT NULL DEFAULT 0,
            user_id NOT NULL,
            reconcile_balance INTEGER NOT NULL DEFAULT 0
            )
        """)

    c.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0,
            deleted BOOLEAN NOT NULL DEFAULT 0,
            user_id INTEGER NOT NULL
            )
        """)

    c.execute("""
        CREATE TABLE envelopes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0,
            budget INTEGER NOT NULL DEFAULT 0,
            deleted BOOLEAN NOT NULL DEFAULT 0,
            user_id INTEGER NOT NULL
            )
        """)

    c.execute("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
            )
        """)

    insert_envelope('Unallocated', 0, USER_ID)


# ---------------TRANSACTION FUNCTIONS--------------- #

def insert_transaction(t):
    # Inserts transaction into database, then updates account/envelope balances
    with conn:
        #if there's no account associated, set the reconcile_balance to 0
        if t.reconcile_balance is None or t.account_id is None:
            t.reconcile_balance = 0
        #insert the transaction
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (t.id, t.type, t.name, t.amt, t.date, t.envelope_id, t.account_id,  t.grouping, t.note, t.schedule, t.status, t.user_id, t.reconcile_balance))
        #THIS LINE WILL BREAK THE RECONCILE FUNCTION IF INSERTING A TRANSACTION IS EVER NOT THE TOP ONE IN THE DATABASE
        c.execute("SELECT id FROM transactions ORDER BY ROWID DESC LIMIT 1")
        t.id = c.fetchone()[0]
        #update envelope/account balances if transaction is not scheduled for later
        if (t.date < datetime.now()):
            if not (t.account_id is None):
                newaccountbalance = get_account_balance(t.account_id) - t.amt
                update_account_balance(t.account_id, newaccountbalance)
            if not (t.envelope_id is None):
                newenvelopebalance = get_envelope_balance(t.envelope_id) - t.amt
                update_envelope_balance(t.envelope_id, newenvelopebalance)
    # Update the reconciled amounts if there is an account associated with the transaction
    if t.account_id is not None:
        update_reconcile_amounts(t.account_id, t.id, INSERT)
    log_write('T INSERT: ' + str(t)+ '\n')

def get_transaction(id):
    # Retrieves transaction object from database given its ID
    c.execute("SELECT * FROM transactions WHERE id=?", (id,))
    tdata = c.fetchone()
    t = Transaction(tdata[1],tdata[2],tdata[3],tdata[4],tdata[5],tdata[6],tdata[7],tdata[8],tdata[9],tdata[10],tdata[11],tdata[12])
    # converts string to datetime object
    t.date = date_parse(t.date)
    t.id = tdata[0]
    return t

def get_transactions(start, amount):
    # returns a list transactions for display
    # (Groups split transactions and envelope fills and displays their summed total)
    c.execute("SELECT id from TRANSACTIONS GROUP BY (CASE WHEN type = 1 OR type = 2 THEN id ELSE grouping END) ORDER BY day DESC, id DESC LIMIT ? OFFSET ?", (amount, start))
    groupings = c.fetchall()
    tlist = []
    for thing in groupings:
        t = get_transaction(thing[0])
        if t.type == SPLIT_TRANSACTION:
            c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=?", (t.grouping,))
            t.amt = c.fetchone()[0]
        elif t.type == ENVELOPE_FILL:
            c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=? AND envelope_id=1", (t.grouping,))
            t.amt = c.fetchone()[0] * -1
        t.amt = stringify(t.amt * -1)
        t.reconcile_balance = stringify(t.reconcile_balance)
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
        t.amt = stringify(t.amt * -1)
        t.reconcile_balance = stringify(t.reconcile_balance)
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
        t.amt = stringify(thing[1] * -1)
        t.reconcile_balance = stringify(t.reconcile_balance)
        tlist.append(t)
    # offset specifies where to start from on the next call
    offset = start + len(tlist)
    # if limit is True you're at the end of the list
    if len(tlist) < amount:
        limit = True
    else:
        limit = False
    return tlist, offset, limit

def get_scheduled_transactions(user_id):
    c.execute("SELECT id FROM transactions WHERE schedule IS NOT NULL AND user_id=? ORDER by day DESC, id DESC", (user_id,))
    ids = c.fetchall()
    tlist = []
    for id in ids:
        t = get_transaction(id[0])
        tlist.append(t)
    return tlist

def delete_transaction(id):
    # deletes transaction and associated grouped transactions and updates appropriate envelope/account balances
    with conn:
        grouping = get_grouping_from_id(id)
        if not (grouping is None):
            ids = get_ids_from_grouping(grouping)
            for id in ids:
                t = get_transaction(id)
                # if it is not a scheduled transaction, update envelope/account balances
                if (t.date < datetime.now()):
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
                # Update the reconciled amounts if there is an account associated with the transaction
                if t.account_id is not None:
                    update_reconcile_amounts(t.account_id, t.id, REMOVE)

                # Delete the actual transaction from the database
                c.execute("DELETE FROM transactions WHERE id=?", (id,))
                log_write('T DELETE: ' + str(t)+ '\n')
        else:
            print("That transaction doesn't exist you twit")
def new_split_transaction(t):
    #takes a transaction with arrays of amt and envelope_id and creates individual transactions
    grouping = gen_grouping_num()
    for i in range(len(t.amt)):
        new_t = Transaction(SPLIT_TRANSACTION, t.name, t.amt[i], t.date, t.envelope_id[i], t.account_id, grouping, t.note, t.schedule, t.status, t.user_id, t.reconcile_balance)
        insert_transaction(new_t)


# ---------------ACCOUNT FUNCTIONS--------------- #

def insert_account(name, balance, user_id):
    #inserts new account and creates "initial account balance" transaction
    with conn:
        c.execute("INSERT INTO accounts (name, balance, user_id) VALUES (?, ?, ?)", (name, 0, user_id))
        account_id = c.lastrowid
        income_name = 'Initial Account Balance: ' + name
        t = Transaction(INCOME, income_name, -1 * balance, datetime.combine(date.today(), datetime.min.time()), 1, account_id, gen_grouping_num(), '', None, False, user_id, 0)
        insert_transaction(t)
        log_write('A INSERT: ' + str(get_account(account_id))+ '\n')

def get_account(id):
    # returns account associated with the given id
    c.execute("SELECT * FROM accounts WHERE id=?", (id,))
    adata = c.fetchone()
    a = Account(adata[1], adata[2], adata[3], adata[4])
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
        log_write('A DELETE: ' + str(get_account(account_id))+ '\n')

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
        log_write('A EDIT: ' + str(get_account(id))+ '\n')

def update_account_balance(id, balance):
    # updates balance of account with given id
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(balance, id))

def edit_accounts(old_accounts, new_accounts):
    # updates database given 2 lists of account objects
    c.execute("SELECT id FROM accounts WHERE deleted=0")
    account_ids = c.fetchall()
    old_ids = []
    # adds id to old_ids then updates the info for the old accounts
    for a in old_accounts:
        old_ids.append(int(a[0]))
        edit_account(int(a[0]), a[1], a[2])
    # adds the new accounts
    for a in new_accounts:
        insert_account(a[0], a[1], a[2])
    # deletes accounts that are missing
    for id in account_ids:
        if not (id[0] in old_ids):
            delete_account(id[0])

def account_transfer(name, amount, date, to_account, from_account, note, schedule, user_id):
    # Creates one transaction draining an account, and one transaction filling another
    grouping = gen_grouping_num()
    fill = Transaction(ACCOUNT_TRANSFER, name, -1*amount, date, None, to_account, grouping, note, schedule, False, user_id, 0)
    insert_transaction(fill)
    empty = Transaction(ACCOUNT_TRANSFER, name, amount, date, None, from_account, grouping, note, schedule, False, user_id, 0)
    insert_transaction(empty)

def update_reconcile_amounts(account_id, transaction_id, method):
    # changes the reconcile amounts after a given transaction
    # maybe optimize later to use the update function with subqueries to avoid doing a for loop
    #   with separate sql calls
    #   UPDATE transactions SET reconcile_balance = reconcile_balance + ? WHERE (SUB QUERY HERE for transactions past the inserted t)
    with conn:
        #find the ID of the previous transaction and set it to transaction_id
        c.execute("SELECT id FROM transactions WHERE (account_id=? AND date(day) == date((SELECT day from transactions where id=?)) AND id<?) OR (account_id=? AND day < date((SELECT day from transactions where id=?))) ORDER BY id DESC LIMIT 1", (account_id,transaction_id,transaction_id,account_id,transaction_id))
        prev_transaction_id = c.fetchone()
        if prev_transaction_id is not None:
            prev_transaction_id = prev_transaction_id[0]
        else:
            #if there is no previous transaction, use the current transaction id
            prev_transaction_id = transaction_id

        if (method == INSERT):
            # Fetches the transactions whose r_balances need to be updated starting from previous transaction
            # (transactions with same account id and greater date OR same date and same account id but greater id than previous transaction)
            c.execute("SELECT id,amount,reconcile_balance FROM transactions WHERE (account_id=? AND (date(day) > date((SELECT day FROM transactions WHERE id=?))) OR (id>=? AND account_id=? AND date(day) == date((SELECT day FROM transactions WHERE id=?)))) ORDER BY day DESC, id DESC", (account_id,prev_transaction_id,prev_transaction_id,account_id,prev_transaction_id))
        elif (method == REMOVE):
            # Fetches the transactions whose r_balances need to be updated starting from the current transaction
            # # (transactions with same account id and greater date OR same date and same account id but greater id than current transaction)
            c.execute("SELECT id,amount,reconcile_balance FROM transactions WHERE (account_id=? AND (date(day) > date((SELECT day FROM transactions WHERE id=?))) OR (id>=? AND account_id=? AND date(day) == date((SELECT day FROM transactions WHERE id=?)))) ORDER BY day DESC, id DESC", (account_id,transaction_id,transaction_id,account_id,transaction_id))

        # Create lists for the collected transactions
        #   If the suggested optimization above is implemented, this section would go away
        t_ids = []
        t_amounts =[]
        t_r_bals =[]
        for row in c:
            t_ids.insert(0,row[0])
            t_amounts.insert(0,row[1])
            t_r_bals.insert(0,row[2])
        if (method == INSERT):
            if (transaction_id == prev_transaction_id):
                t_r_bals[0] = -1* t_amounts[0]
                c.execute("UPDATE transactions SET reconcile_balance=? WHERE id=?", (-1*t_amounts[0],t_ids[0]))
            for i in range(1,len(t_ids)):
                t_r_bals[i] = t_r_bals[i-1] - t_amounts[i]
        elif (method == REMOVE):
            # add the t_amount of given transaction from following r_balances
            for i in range(1,len(t_ids)):
                t_r_bals[i] = t_r_bals[i] + t_amounts[0]
        for i in range(1,len(t_ids)):
            c.execute("UPDATE transactions SET reconcile_balance=? WHERE id=?", (t_r_bals[i],t_ids[i]))


# ---------------ENVELOPE FUNCTIONS--------------- #

def insert_envelope(name, budget, user_id):
    # Inserts an envelope into the database with givne name and budget and a balnce of 0
    with conn:
        c.execute("INSERT INTO envelopes (name, budget, user_id) VALUES (?, ?, ?)", (name,budget,user_id))
        envelope_id = c.lastrowid
        log_write('E INSERT: ' + str(get_envelope(envelope_id))+ '\n')

def get_envelope(id):
    # returns an envelope object given an envelope_id
    c.execute("SELECT * FROM envelopes WHERE id=?", (id,))
    edata = c.fetchone()
    e = Envelope(edata[1], edata[2], edata[3], edata[4], edata[5])
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
        log_write('E DELETE: ' + str(get_account(envelope_id))+ '\n')

def get_envelope_balance(id):
    # returns float of envelope balance given id
    c.execute("SELECT balance FROM envelopes WHERE id=?", (id,))
    balance = c.fetchone()
    if not (balance is None):
        return balance[0]
    else:
        print("That envelope doesn't exist you imbicil")

def update_envelope_balance(id, balance):
    # updates envelope balance for given id
    # NOTE: this isn't possible as a stand alone action
    with conn:
        c.execute("UPDATE envelopes SET balance=? WHERE id=?",(balance, id))

def edit_envelope(id, name, budget):
    # updates the name and budget for given id
    with conn:
        c.execute("UPDATE envelopes SET name=?, budget=? WHERE id=?",(name, budget, id))
        log_write('E EDIT: ' + str(get_account(id))+ '\n')

def edit_envelopes(old_envelopes, new_envelopes):
    # updates database given 2 lists of envelope objects from envelope editor
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
        insert_envelope(e[0], e[1], e[2])
    # deletes envelopes that are missing
    for id in envelope_ids:
        if not (id[0] in old_ids):
            delete_envelope(id[0])

def envelope_transfer(name, amt, date, to_envelope, from_envelope, note, schedule, user_id):
    # Creates a transaction to fill one envelope and another to empty the other
    grouping = gen_grouping_num()
    fill = Transaction(ENVELOPE_TRANSFER, name, -1*amt, date, to_envelope, None, grouping, note, schedule, False, user_id, 0)
    insert_transaction(fill)
    empty = Transaction(ENVELOPE_TRANSFER, name, amt, date, from_envelope, None, grouping, note, schedule, False, user_id, 0)
    insert_transaction(empty)

def envelope_fill(t):
    # Takes a transaction with an array of envelope ids and amounts and creates sub-transactions to fill the envelopes
    if t.type == ENVELOPE_FILL:
        grouping = gen_grouping_num()
        amts = t.amt
        envelopes = t.envelope_id
        for i in range(len(amts)):
            empty_unallocated = Transaction(ENVELOPE_FILL, t.name, amts[i], t.date, UNALLOCATED, None, grouping, t.note, t.schedule, False, t.user_id, 0)
            insert_transaction(empty_unallocated)
            fill_envelope = Transaction(ENVELOPE_FILL, t.name, amts[i] * -1, t.date, envelopes[i], None, grouping, t.note, t.schedule, False, t.user_id, 0)
            insert_transaction(fill_envelope)


# ------ OTHER FUNCTIONS ------ #

def get_total(user_id):
    # Sums the account balances for display
    c.execute("SELECT SUM(balance) FROM accounts WHERE user_id=?", (user_id,))
    total = c.fetchone()[0]
    if not total is None:
        return stringify(total)
    else:
        return stringify(0)

def gen_grouping_num():
    # Creates a new and unique grouping number
    # POSSIBLY CAN DO +1 in SQLITE QUERRY RATHER THAN THIS LOGIC (TEST IN THIS PROGRAM)
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
            'note': t.note,
            'reconcile_balance': t.reconcile_balance
        })
    return data

def stringify(number):
    # Formats number into a nice string to display
    negative = number < 0
    string = '$%.2f' % abs(number / 100)
    if negative:
        string = '-' + string
    return string

def date_parse(date_str):
    # converts string to datetime object
    if len(date_str) == 10:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    elif len(date_str)==19:
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    elif len(date_str)==26:
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
    else:
        # Change to actually throw an error instead of just crashing things by
        # returning the wrong data type
        date = None
        print("DATE PARSE ERROR: ", date_str)
    return date

def print_database():
    print()
    print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv\n")
    print("TRANSACTIONS:")
    c.execute("PRAGMA table_info(transactions)")
    colnames = ''
    for row in c:
        colnames = colnames + row[1] + ', '
    print("(" + colnames[:-2] + ")\n")
    c.execute("SELECT * FROM transactions ORDER BY day DESC, id DESC")
    for row in c:
        print(row)
    print()

    print('ACCOUNTS:')
    c.execute("PRAGMA table_info(accounts)")
    colnames = ''
    for row in c:
        colnames = colnames + row[1] + ', '
    print("(" + colnames[:-2] + ")\n")
    c.execute("SELECT * FROM accounts")
    for row in c:
        print(row)
    print()

    print('ENVELOPES:')
    c.execute("PRAGMA table_info(envelopes)")
    colnames = ''
    for row in c:
        colnames = colnames + row[1] + ', '
    print("(" + colnames[:-2] + ")\n")
    c.execute("SELECT * FROM envelopes")
    for row in c:
        print(row)
    print()
    print("TOTAL FUNDS: ", get_total(USER_ID))
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n")


# TEMPORARY FUNCTIONS
def add_reconcile_balance_column():
    c.execute("""
        ALTER TABLE transactions
        ADD COLUMN reconcile_balance INTEGER NOT NULL DEFAULT 0
        """)

def clear_reconcile_balance():
    with conn:
        c.execute("UPDATE transactions SET reconcile_balance=0")

def create_reconcile_balance():
    with conn:
        account_ids = []
        c.execute("SELECT account_id FROM transactions GROUP BY account_id")
        for row in c:
            if row[0] is not None:
                    account_ids.append(row[0])
        for a_id in account_ids:
            c.execute("SELECT id,amount,reconcile_balance FROM transactions WHERE account_id=? ORDER BY day DESC, id DESC", (a_id,))
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
                c.execute("UPDATE transactions SET reconcile_balance=? WHERE id=?", (t_r_bal,t_id))

def health_check():
    healthy = True
    log_message = ''
    #Check if the envelope sum and account sum are consistent
    c.execute("SELECT user_id FROM accounts GROUP BY user_id")
    user_ids = c.fetchall()
    for row in user_ids:
        user_id = row[0]
        # Get accounts total
        c.execute("SELECT SUM(balance) FROM accounts WHERE user_id=?", (user_id,))
        accounts_total = c.fetchone()[0]
        # Get envelopes total
        c.execute("SELECT SUM(balance) FROM envelopes WHERE user_id=?", (user_id,))
        envelopes_total = c.fetchone()[0]
        if (accounts_total != envelopes_total):
            log_message = f'{log_message} [A/E Sum Mismatch -> A: {accounts_total} E: {envelopes_total}] Diff: {accounts_total-envelopes_total}\n'
            healthy = False

        # Check if stored account totals equal the sum of their transactions
        c.execute("SELECT id,balance,name from accounts")
        accounts = c.fetchall()
        for row in accounts:
            account_name = row[2]
            account_id = row[0]
            # get account balance according to database
            account_balance = row[1]
            # get account balance according to summed transaction totals
            c.execute("SELECT SUM(amount) from transactions WHERE account_id=? AND date(day) <= date('now')", (account_id,))
            a_balance = c.fetchone()[0]
            if a_balance is None:
                a_balance = 0
            if (-1*account_balance != a_balance):
                log_message = f'{log_message} [A Total Err -> Name: {account_name}, ID: {account_id}, Disp/Total: {account_balance}/{a_balance}] Diff: {abs(a_balance + account_balance)}\n'
                healthy = False

        # Check if stored envelope totals equals the sum of their transactions
        c.execute("SELECT id,balance,name from envelopes")
        envelopes = c.fetchall()
        for row in envelopes:
            envelope_name = row[2]
            envelope_id = row[0]
            # get envelope balance according to database
            envelope_balance = row[1]
            # get envelope balance according to summed transaction totals
            c.execute("SELECT SUM(amount) from transactions WHERE envelope_id=? AND date(day) <= date('now')", (envelope_id,))
            e_balance = c.fetchone()[0]
            if e_balance is None:
                e_balance = 0
            if (-1*envelope_balance != e_balance):
                log_message = f'{log_message} [E Total Err -> Name: {envelope_name}, ID: {envelope_id}, Disp/Total: {envelope_balance}/{e_balance}] Diff: {abs(e_balance + envelope_balance)}\n'
                healthy = False

        log_write(log_message)
        return healthy

def log_write(text):
    with open("EventLog.txt",'a') as f:
        f.write(text)


def main():
    print_database()

if __name__ == "__main__":
    main()
