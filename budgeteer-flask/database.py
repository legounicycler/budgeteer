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
            if not (t.envelope_id is None or get_envelope(t.envelope_id).deleted == True):
                update_envelope_balance(t.envelope_id, get_envelope_balance(t.envelope_id) + t.amt)
            if not (t.account_id is None or get_account(t.account_id).deleted == True):
                update_account_balance(t.account_id, get_account_balance(t.account_id) + t.amt)
            if get_envelope(t.envelope_id).deleted == True:
                update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + t.amt)
            c.execute("DELETE FROM transactions WHERE id=?", (id,))
        elif not (grouping is None):
            ids = get_ids_from_grouping(grouping)
            for i in ids:
                t = get_transaction(i)
                if not (t.envelope_id is None or get_envelope(t.envelope_id).deleted == True):
                    update_envelope_balance(t.envelope_id, get_envelope_balance(t.envelope_id) + t.amt)
                if not (t.account_id is None or get_account(t.account_id).deleted == True):
                    update_account_balance(t.account_id, get_account_balance(t.account_id) + t.amt)
                if get_envelope(t.envelope_id).deleted == True:
                    update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + t.amt)
                c.execute("DELETE FROM transactions WHERE id=?", (i,))
        else:
            print("that transaction doesn't exist you twit")


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
        #inserts new account and creates primary account fill transaction
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
        a = Account(adata[1], adata[2], adata[3])
        a.id = adata[0]
        return a

# def get_account_list():
#     with conn:
#         c.execute("SELECT id FROM accounts ORDER by id ASC")
#         ids = c.fetchall()
#         alist = []
#         for id in ids:
#             a= get_account(id[0])
#             a.balance = '$%.2f' % a.balance
#             alist.append(a)
#         return alist

def get_account_dict():
    with conn:
        c.execute("SELECT id FROM accounts ORDER by id ASC")
        ids = c.fetchall()
        adict = {}
        for id in ids:
            a = get_account(id[0])
            a.balance = '$%.2f' % a.balance
            adict[id[0]] = a
        return adict

def delete_account(account_id):
    with conn:
        update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + get_envelope_balance(account_id))
        c.execute("UPDATE accounts SET deleted=1,balance=0 WHERE id=?", (account_id,))
        print("account deleted ", account_id)

def get_account_balance(id):
    c.execute("SELECT balance FROM accounts WHERE id=?", (id,))
    balance = c.fetchone()
    if not (balance is None):
        return balance[0]
    else:
        print("that account doesn't exist you twit.")

def edit_account(id, name, balance):
    #updates account balalnce, account name, and unallocated balance
    #This could probably be one query instead of having 3 separate update functions
    current_balance = get_account_balance(id)
    diff = current_balance - balance
    unallocated_balance = get_envelope_balance(1)
    new_unallocated_balance = unallocated_balance - diff
    update_account_balance(id, balance)
    update_envelope_balance(UNALLOCATED, new_unallocated_balance)
    update_account_name(id, name)


def update_account_name(id, name):
    with conn:
        c.execute("UPDATE accounts SET name=? WHERE id=?", (name, id))


def update_account_balance(id, balance):
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(round(balance,2), id))

def edit_accounts(json_data):
    with conn:
        c.execute("SELECT id FROM accounts")
        existing_accounts = c.fetchall()
        account_ids = []
        for i in existing_accounts:
            account_ids.append(i[0])
        print(account_ids)

    print(json_data)
    form_ids = []
    for x in json_data:
        id = float(x)
        account_name = json_data[x][0]
        account_balance = float(json_data[x][1])
        if (id % 1) == 0:
            id = int(id)
            form_ids.append(id)
            edit_account(id, account_name, account_balance)
        else:
            insert_account(account_name, account_balance)

    for x in account_ids:
        if not (x in form_ids):
            delete_account(x)

def account_transfer(name, amount, date, to_account, from_account, note):
    grouping = gen_grouping_num()
    fill = Transaction(ACCOUNT_TRANSFER, name, amount, date, None, to_account, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ACCOUNT_TRANSFER, name, -1* amount, date, None, from_account, grouping, note)
    insert_transaction(empty)


#ENVELOPE FUNCTIONS
def insert_envelope(name, budget):
    with conn:
        c.execute("INSERT INTO envelopes (name, budget) VALUES (?, ?)", (name,budget))

def get_envelope(id):
    with conn:
        c.execute("SELECT * FROM envelopes WHERE id=?", (id,))
        edata = c.fetchone()
        e = Envelope(edata[1], edata[2], edata[3], edata[4])
        e.id = edata[0]
        return e

def get_envelope_dict():
    with conn:
        c.execute("SELECT id FROM envelopes ORDER by id ASC")
        ids = c.fetchall()
        edict = {}
        for id in ids:
            e = get_envelope(id[0])
            e.balance = '$%.2f' % e.balance
            e.budget = '$%.2f' % e.budget
            edict[id[0]] = e
        return edict

def delete_envelope(envelope_id):
    with conn:
        if (envelope_id != 1):
            update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + get_envelope_balance(envelope_id))
            c.execute("UPDATE envelopes SET deleted=1,balance=0 WHERE id=?", (envelope_id,))
            print("Envelope deleted: ", envelope_id)
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

def edit_envelope(id, name, budget):
    update_envelope_name(id, name)
    update_envelope_budget(id, budget)

def edit_envelopes(json_data):
    with conn:
        c.execute("SELECT id FROM envelopes")
        existing_envelopes = c.fetchall()
        envelope_ids = []
        for i in existing_envelopes:
            envelope_ids.append(i[0])
        envelope_ids.pop() # gets rid of unallocated id (1) in envelope list
        print(envelope_ids)

    print(json_data)
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

    for x in envelope_ids:
        if not (x in form_ids):
            delete_envelope(x)

def envelope_transfer(name, amt, date, to_envelope, from_envelope, note):
    grouping = gen_grouping_num()
    fill = Transaction(ENVELOPE_TRANSFER, name, amt, date, to_envelope, None, grouping, note)
    insert_transaction(fill)
    empty = Transaction(ENVELOPE_TRANSFER, name, -1 * amt, date, from_envelope, None, grouping, note)
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
        if not total is None:
            return total
        else:
            return 0

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

def get_grouped_json(id):
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
    update_envelope_balance(1, 0)
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