"""
This file contains functions relevant to actually manipulating values in the database
"""

import sqlite3
import datetime
from datetime import datetime
from datetime import date
import json
import platform
import sys, os

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/alimiero/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

# Going to have to CHANGE since each user has their own unique unallocated envelope
UNALLOCATED = 1

#Should this eventually be an ENUM instead?
BASIC_TRANSACTION = 0
ENVELOPE_TRANSFER = 1
ACCOUNT_TRANSFER = 2
INCOME = 3
SPLIT_TRANSACTION = 4
ENVELOPE_FILL = 5
ENVELOPE_DELETE = 6
ACCOUNT_DELETE = 7
ACCOUNT_ADJUST = 8

#Should this also eventually be an ENUM?
REMOVE = False
INSERT = True

# Temporary testing user_id
USER_ID = 1

# ------ CLASSES/DATABASE DEFINITIONS ------ #

class Transaction:
    def __init__(self, type, name, amt, date, envelope_id, account_id, grouping, note, schedule, status, user_id, a_reconcile_bal=0, e_reconcile_bal=0):
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
        self.a_reconcile_bal = a_reconcile_bal
        self.e_reconcile_bal = e_reconcile_bal
    def __repr__(self):
        return "ID:{}, TYPE:{}, NAME:{}, AMT:{}, DATE:{}, E_ID:{}, A_ID:{}, GRP:{}, NOTE:{}, SCHED:{}, STATUS:{}, U_ID:{}, A_R_BAL:{}, E_R_BAL:{}".format(self.id,self.type,self.name,self.amt,self.date,self.envelope_id,self.account_id,self.grouping,self.note,self.schedule,self.status,self.user_id,self.a_reconcile_bal,self.e_reconcile_bal)
    def __str__(self):
        return "ID:{}, TYPE:{}, NAME:{}, AMT:{}, DATE:{}, E_ID:{}, A_ID:{}, GRP:{}, NOTE:{}, SCHED:{}, STATUS:{}, U_ID:{}, A_R_BAL:{}, E_R_BAL:{}".format(self.id,self.type,self.name,self.amt,self.date,self.envelope_id,self.account_id,self.grouping,self.note,self.schedule,self.status,self.user_id,self.a_reconcile_bal,self.e_reconcile_bal)


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


def create_db():
    """
    Creates the database file
    """
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
            a_reconcile_bal INTEGER NOT NULL DEFAULT 0,
            e_reconcile_bal INTEGER NOT NULL DEFAULT 0
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
    """
    Inserts transaction into database, then updates account/envelope balances
    """
    with conn:
        
        # ---1. MAKE SURE THE RECONCILE BALANCES EXIST---
        #If there's no account/envelope associated, set the reconcile balance to 0
        if t.a_reconcile_bal is None or t.account_id is None:
            t.a_reconcile_bal = 0
        if t.e_reconcile_bal is None or t.envelope_id is None:
            t.e_reconcile_bal = 0
        
        # ---2. INSERT THE TRANSACTION INTO THE TABLE---
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (t.id, t.type, t.name, t.amt, t.date, t.envelope_id, t.account_id,  t.grouping, t.note, t.schedule, t.status, t.user_id, t.a_reconcile_bal, t.e_reconcile_bal))
        
        # ---3. UPDATE THE ACCOUNT/ENVELOPE BALANCES---
        #TODO: I think this is a way of generating a new transaction ID, but this seems bad and slow
        c.execute("SELECT id FROM transactions ORDER BY ROWID DESC LIMIT 1") #THIS LINE WILL BREAK THE RECONCILE FUNCTION IF INSERTING A TRANSACTION IS EVER NOT THE TOP ONE IN THE DATABASE
        t.id = c.fetchone()[0]
        #Only update balances if transaction is not scheduled for later
        if (t.date < datetime.now()):
            if t.account_id is not None:
                newaccountbalance = get_account_balance(t.account_id) - t.amt
                update_account_balance(t.account_id, newaccountbalance)
            if t.envelope_id is not None:
                newenvelopebalance = get_envelope_balance(t.envelope_id) - t.amt
                update_envelope_balance(t.envelope_id, newenvelopebalance)

        # ---4. UPDATE RECONCILE BALANCES---
        update_reconcile_amounts(t.account_id, t.envelope_id, t.id, INSERT)
    
    log_write('T INSERT: ' + str(t))

def get_transaction(id):
    """
    Retrieves transaction object from database given its ID
    """
    c.execute("SELECT * FROM transactions WHERE id=?", (id,))
    tdata = c.fetchone()
    t = Transaction(tdata[1],tdata[2],tdata[3],tdata[4],tdata[5],tdata[6],tdata[7],tdata[8],tdata[9],tdata[10],tdata[11],tdata[12],tdata[13])
    # converts string to datetime object
    t.date = date_parse(t.date)
    t.id = tdata[0]
    return t

def get_transactions(start, amount):
    """
    For displaying transactions on the HOME PAGE ONLY
    Given a start number and an amount of transactions to fetch, returns:
    1. A list of transaction objects for display
    2. An offset signifying how many transactions are currently displayed, or where the next start should be.
    3. limit - If this is true, there are no more transactions to fetch
    
    Note: Grouped transactions (Split transactions and envelope fills) displays as a single transaction
    with its summed total
    """
    c.execute("SELECT id from TRANSACTIONS GROUP BY grouping ORDER BY day DESC, id DESC LIMIT ? OFFSET ?", (amount, start))
    groupings = c.fetchall()
    tlist = []
    for thing in groupings:
        t = get_transaction(thing[0])

        # Set the amount for display
        if t.type == BASIC_TRANSACTION or t.type == INCOME or t.type == ACCOUNT_ADJUST or t.type == ACCOUNT_DELETE:
             t.amt = -1 * t.amt
        elif t.type == ENVELOPE_TRANSFER:
            t_ids = get_ids_from_grouping(t.grouping)
            if (t.amt > 0):
                # Get the id for the other envelope and put it in the t.account_id field for special display
                from_envelope_id = get_transaction(t_ids[0]).envelope_id
                to_envelope_id = get_transaction(t_ids[1]).envelope_id
            else:
                from_envelope_id = get_transaction(t_ids[1]).envelope_id
                to_envelope_id = get_transaction(t_ids[0]).envelope_id
            # Display format (eID -> aID) or for envelope transfers, (fromEnvelope -> toEnvelope)
            t.envelope_id = from_envelope_id # When displaying transactions, envelope ID is always displayed first.
            t.account_id = to_envelope_id    # When displaying transactions, account ID is always displayed second
            t.amt = abs(t.amt)
        elif t.type == ACCOUNT_TRANSFER:
            t_ids = get_ids_from_grouping(t.grouping)
            if (t.amt > 0):
                # Get the id for the other account and put it in the t.account_id field for special display
                from_account_id = get_transaction(t_ids[0]).account_id
                to_account_id = get_transaction(t_ids[1]).account_id
            else:
                from_account_id = get_transaction(t_ids[1]).account_id
                to_account_id = get_transaction(t_ids[0]).account_id
            # Display format (eID -> aID) or for account transfers, (fromaccount -> toaccount)
            t.envelope_id = from_account_id # When displaying transactions, envelope ID is always displayed first.
            t.account_id = to_account_id    # When displaying transactions, account ID is always displayed second
            t.amt = abs(t.amt)
        elif t.type == SPLIT_TRANSACTION:
            c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=?", (t.grouping,))
            t.amt = -1 * c.fetchone()[0] # Total the amount for all the constituent transactions
        elif t.type == ENVELOPE_FILL:
            c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=? AND envelope_id=?", (t.grouping,UNALLOCATED))
            t.amt = c.fetchone()[0] # Total the amount for the envelope fill
        
        t.amt = stringify(t.amt)
        t.a_reconcile_bal = stringify(t.a_reconcile_bal)
        t.e_reconcile_bal = stringify(t.e_reconcile_bal)
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
    """
    For displaying transactions on the ENVELOPE PAGE ONLY
    Given a start number and an amount of transactions to fetch, returns for a particular envelope:
    1. A list of transaction objects for display
    2. An offset signifying how many transactions are currently displayed, or where the next start should be.
    3. limit - If this is true, there are no more transactions to fetch
    
    Note: Grouped transactions (Split transactions and envelope fills) displays as a single transaction
    with its summed total
    """
    # TODO: (ADD LATER?) If the envelope is unallocated, group envelope fill transactions
    c.execute("SELECT id FROM transactions WHERE envelope_id=? ORDER by day DESC, id DESC LIMIT ? OFFSET ?", (envelope_id,amount,start))
    ids = c.fetchall()
    tlist = []
    for id in ids:
        t = get_transaction(id[0])
        # For display purposes, the envelope ID displays first, then the account ID
        if t.type == ENVELOPE_TRANSFER:
            t_ids = get_ids_from_grouping(t.grouping)
            if (t.amt == 0): # If amt is 0: Display the envelope order based on the order they come out of the database
                from_envelope_id = get_transaction(t_ids[1]).envelope_id
                to_envelope_id = get_transaction(t_ids[0]).envelope_id
            elif (t.amt > 0): # If amt is +: Actual amt is -, which means the envelope is being drained, which means it's FROM 
                t_ids.remove(t.id) #Remove the transaction with the positive balance
                from_envelope_id = t.envelope_id
                to_envelope_id = get_transaction(t_ids[0]).envelope_id
            elif (t.amt < 0): # If amt is -: Actual amt is +, which means the envelope is being filled, which means it's TO
                t_ids.remove(t.id) #Remove the transaction with the positive balance
                to_envelope_id = t.envelope_id
                from_envelope_id = get_transaction(t_ids[0]).envelope_id
            # Display format (eID -> aID) or for envelope transfers, (fromEnvelope -> toEnvelope)
            t.envelope_id = from_envelope_id # When displaying transactions, envelope ID is always displayed first.
            t.account_id = to_envelope_id    # When displaying transactions, account ID is always displayed second

        t.amt = stringify(t.amt * -1)
        t.a_reconcile_bal = stringify(t.a_reconcile_bal)
        t.e_reconcile_bal = stringify(t.e_reconcile_bal)
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
    """
    For displaying transactions on the ACCOUNTS PAGE ONLY
    Given a start number and an amount of transactions to fetch, returns for a particular account:
    1. A list of transaction objects for display
    2. An offset signifying how many transactions are currently displayed, or where the next start should be.
    3. limit - If this is true, there are no more transactions to fetch
    
    Note: Grouped transactions (Split transactions and envelope fills) displays as a single transaction
    with its summed total
    """
    c.execute("SELECT id, SUM(amount) FROM transactions WHERE account_id=? GROUP BY grouping ORDER by day DESC, id DESC LIMIT ? OFFSET ?", (account_id,amount,start))
    ids = c.fetchall()
    tlist = []
    for thing in ids:
        t = get_transaction(thing[0])
        if t.type == ACCOUNT_TRANSFER:
            # Get the id for the other account and put it in the t.account_id field for special display
            t_ids = get_ids_from_grouping(t.grouping)
            # Display format (eID -> aID) or for account transfers, (fromAccount -> toAccount)
            t_ids = get_ids_from_grouping(t.grouping)
            if (t.amt == 0): # If amt is 0: Display the account order based on the order they come out of the database
                from_account_id = get_transaction(t_ids[1]).account_id
                to_account_id = get_transaction(t_ids[0]).account_id
            elif (t.amt > 0): # If amt is +: Actual amt is -, which means the account is being drained, which means it's FROM 
                t_ids.remove(t.id) #Remove the transaction with the positive balance
                from_account_id = t.account_id
                to_account_id = get_transaction(t_ids[0]).account_id
            elif (t.amt < 0): # If amt is -: Actual amt is +, which means the account is being filled, which means it's TO
                t_ids.remove(t.id) #Remove the transaction with the positive balance
                to_account_id = t.account_id
                from_account_id = get_transaction(t_ids[0]).account_id
            # Display format (eID -> aID) or for account transfers, (fromaccount -> toaccount)
            t.envelope_id = from_account_id # When displaying transactions, envelope ID is always displayed first.
            t.account_id = to_account_id    # When displaying transactions, account ID is always displayed second
        t.amt = stringify(thing[1] * -1)
        t.a_reconcile_bal = stringify(t.a_reconcile_bal)
        t.e_reconcile_bal = stringify(t.e_reconcile_bal)
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
    """
    Returns a list of ALL scheduled transactions
    """
    c.execute("SELECT id FROM transactions WHERE schedule IS NOT NULL AND user_id=? ORDER by day DESC, id DESC", (user_id,))
    ids = c.fetchall()
    tlist = []
    for id in ids:
        t = get_transaction(id[0])
        tlist.append(t)
    return tlist

def delete_transaction(id):
    """
    Deletes transaction and associated grouped transactions and updates appropriate envelope/account balances
    """
    with conn:
        # 1. Get all the grouped transactions to delete
        grouping = get_grouping_from_id(id)
        if grouping is not None:
            ids = get_ids_from_grouping(grouping)
            for id in ids:                
                t = get_transaction(id)

                # 2a. If you're deleting an "ENVELOPE_DELETE" transaction, restore it so the balances can be updated
                if t.type == ENVELOPE_DELETE:
                    if t.envelope_id is not UNALLOCATED: # Don't try to restore the unallocated envelope
                        if (get_envelope(t.envelope_id).deleted is not False): # Don't try to restore an envelope that is not deleted
                            restore_envelope(t.envelope_id)
                
                # 2b. If you're deleting an "ACCOUNT_DELETE" transaction, restore it so the balances can be updated
                if t.type == ACCOUNT_DELETE:
                    print(t)
                    print(t.account_id)
                    restore_account(t.account_id)

                # 3. If it is not a transaction in the future, update envelope/account balances
                if (t.date < datetime.now()): #TODO: This will probably need to change when timezones are implemented
                    if t.envelope_id is not None:
                        if not (get_envelope(t.envelope_id).deleted == True):
                            update_envelope_balance(t.envelope_id, get_envelope_balance(t.envelope_id) + t.amt)
                        else:
                            update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + t.amt)
                    if t.account_id is not None:
                        if not (get_account(t.account_id).deleted == True):
                            update_account_balance(t.account_id, get_account_balance(t.account_id) + t.amt)
                        else:
                            update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) - t.amt)

                    # 4. Update the reconciled amounts if there is an account associated with the transaction
                    update_reconcile_amounts(t.account_id, t.envelope_id, t.id, REMOVE)
                
                # 5. Delete the actual transaction from the database
                c.execute("DELETE FROM transactions WHERE id=?", (id,))

                log_write('T DELETE: ' + str(t))
        else:
            print("That transaction doesn't exist you twit")

def new_split_transaction(t):
    """
    Takes a transaction with arrays of amt and envelope_id and creates individual transactions
    This is a grouped transaction with multiple envelopes!
    """
    grouping = gen_grouping_num()
    for i in range(len(t.amt)):
        new_t = Transaction(SPLIT_TRANSACTION, t.name, t.amt[i], t.date, t.envelope_id[i], t.account_id, grouping, t.note, t.schedule, t.status, t.user_id)
        insert_transaction(new_t)

def update_reconcile_amounts(account_id, envelope_id, transaction_id, method):
    """
    Updates the envelope and account reconcile amounts for all transactions after the given transaction
    """
    # TODO: maybe optimize later to use the update function with subqueries to avoid doing a for loop
    # with separate sql calls
    # Something like: UPDATE transactions SET a_reconcile_bal = a_reconcile_bal + ? WHERE (SUB QUERY HERE for transactions past the inserted t)
    with conn:

        # UPDATE THE ACCOUNT RECONCILE AMOUNTS
        if account_id is not None:

            # 1. Find the ID of the previous transaction in the same account
            c.execute("SELECT id FROM transactions WHERE (account_id=? AND date(day) == date((SELECT day from transactions where id=?)) AND id<?) OR (account_id=? AND day < date((SELECT day from transactions where id=?))) ORDER BY id DESC LIMIT 1", (account_id,transaction_id,transaction_id,account_id,transaction_id))
            prev_transaction_id = c.fetchone()
            if prev_transaction_id is not None:
                prev_transaction_id = prev_transaction_id[0]
            else:
                #if there is no previous transaction, use the current transaction id
                prev_transaction_id = transaction_id
            
            # 2. Fetch info for the transactions that need to be updated
            if (method == INSERT):
                # Fetches the transactions whose a_reconcile_bal's need to be updated starting from PREVIOUS transaction
                # (transactions with same account id and greater date OR same date and same account id but greater id than previous transaction)
                c.execute("SELECT id,amount,a_reconcile_bal FROM transactions WHERE (account_id=? AND (date(day) > date((SELECT day FROM transactions WHERE id=?))) OR (id>=? AND account_id=? AND date(day) == date((SELECT day FROM transactions WHERE id=?)))) ORDER BY day DESC, id DESC", (account_id,prev_transaction_id,prev_transaction_id,account_id,prev_transaction_id))
            elif (method == REMOVE):
                # Fetches the transactions whose a_reconcile_bal's need to be updated starting from the CURRENT transaction
                # # (transactions with same account id and greater date OR same date and same account id but greater id than current transaction)
                c.execute("SELECT id,amount,a_reconcile_bal FROM transactions WHERE (account_id=? AND (date(day) > date((SELECT day FROM transactions WHERE id=?))) OR (id>=? AND account_id=? AND date(day) == date((SELECT day FROM transactions WHERE id=?)))) ORDER BY day DESC, id DESC", (account_id,transaction_id,transaction_id,account_id,transaction_id))

            # 3. Put contents of query into lists
            t_ids = []
            t_amounts =[]
            t_r_bals =[]
            for row in c:
                t_ids.insert(0,row[0])
                t_amounts.insert(0,row[1])
                t_r_bals.insert(0,row[2])

            # 4. Update the reconcile val
            if (method == INSERT):
                if (transaction_id == prev_transaction_id):
                    t_r_bals[0] = -1* t_amounts[0]
                    c.execute("UPDATE transactions SET a_reconcile_bal=? WHERE id=?", (-1*t_amounts[0],t_ids[0]))
                for i in range(1,len(t_ids)):
                    t_r_bals[i] = t_r_bals[i-1] - t_amounts[i]
            elif (method == REMOVE):
                # add the t_amount of given transaction from following a_reconcile_bal's
                for i in range(1,len(t_ids)):
                    t_r_bals[i] = t_r_bals[i] + t_amounts[0]
            for i in range(1,len(t_ids)):
                c.execute("UPDATE transactions SET a_reconcile_bal=? WHERE id=?", (t_r_bals[i],t_ids[i]))
        
        # UPDATE THE ENVELOPE RECONCILE AMOUNTS
        if envelope_id is not None:

            # 1. Find the ID of the previous transaction in the same envelope
            c.execute("SELECT id FROM transactions WHERE (envelope_id=? AND date(day) == date((SELECT day from transactions where id=?)) AND id<?) OR (envelope_id=? AND day < date((SELECT day from transactions where id=?))) ORDER BY id DESC LIMIT 1", (envelope_id,transaction_id,transaction_id,envelope_id,transaction_id))
            prev_transaction_id = c.fetchone()
            if prev_transaction_id is not None:
                prev_transaction_id = prev_transaction_id[0]
            else:
                #If there is no previous transaction, use the current transaction id
                prev_transaction_id = transaction_id

            # 2. Fetch info for the transactions that need to be updated
            if (method == INSERT):
                # Fetches the transactions whose e_reconcile_bal's need to be updated starting from PREVIOUS transaction
                # (transactions with same account id and greater date OR same date and same envelope id but greater id than previous transaction)
                c.execute("SELECT id,amount,e_reconcile_bal FROM transactions WHERE (envelope_id=? AND (date(day) > date((SELECT day FROM transactions WHERE id=?))) OR (id>=? AND envelope_id=? AND date(day) == date((SELECT day FROM transactions WHERE id=?)))) ORDER BY day DESC, id DESC", (envelope_id,prev_transaction_id,prev_transaction_id,envelope_id,prev_transaction_id))
            elif (method == REMOVE):
                # Fetches the transactions whose e_reconcile_bal's need to be updated starting from the CURRENT transaction
                # # (transactions with same account id and greater date OR same date and same envelope id but greater id than current transaction)
                c.execute("SELECT id,amount,a_reconcile_bal FROM transactions WHERE (envelope_id=? AND (date(day) > date((SELECT day FROM transactions WHERE id=?))) OR (id>=? AND envelope_id=? AND date(day) == date((SELECT day FROM transactions WHERE id=?)))) ORDER BY day DESC, id DESC", (envelope_id,transaction_id,transaction_id,envelope_id,transaction_id))

            # 3. Put contents of query into lists
            t_ids = []
            t_amounts =[]
            t_r_bals =[]
            for row in c:
                t_ids.insert(0,row[0])
                t_amounts.insert(0,row[1])
                t_r_bals.insert(0,row[2])

            # 4. Update the reconcile val
            if (method == INSERT):
                if (transaction_id == prev_transaction_id):
                    t_r_bals[0] = -1* t_amounts[0]
                    c.execute("UPDATE transactions SET e_reconcile_bal=? WHERE id=?", (-1*t_amounts[0],t_ids[0]))
                for i in range(1,len(t_ids)):
                    t_r_bals[i] = t_r_bals[i-1] - t_amounts[i]
            elif (method == REMOVE):
                # add the t_amount of given transaction from following e_reconcile_bal's
                for i in range(1,len(t_ids)):
                    t_r_bals[i] = t_r_bals[i] + t_amounts[0]
            for i in range(1,len(t_ids)):
                c.execute("UPDATE transactions SET e_reconcile_bal=? WHERE id=?", (t_r_bals[i],t_ids[i]))

# ---------------ACCOUNT FUNCTIONS--------------- #

def insert_account(account):
    """
    Inserts new account and creates "initial account balance" transaction
    """
    with conn:
        c.execute("INSERT INTO accounts (name, balance, user_id) VALUES (?, ?, ?)", (account.name, 0, account.user_id))
        account_id = c.lastrowid
        income_name = 'Initial Account Balance: ' + account.name
        insert_transaction(Transaction(INCOME, income_name, -1 * account.balance, datetime.combine(date.today(), datetime.min.time()), 1, account_id, gen_grouping_num(), '', None, False, account.user_id))
        log_write('A INSERT: ' + str(get_account(account_id)))

def get_account(id):
    """
    Returns account associated with the given id
    """
    c.execute("SELECT * FROM accounts WHERE id=?", (id,))
    adata = c.fetchone()
    a = Account(adata[1], adata[2], adata[3], adata[4])
    a.id = adata[0]
    return a

def get_account_dict():
    """
    Used for displaying the accounts in the side panel and selects.
    Returns:
    1. A boolean that says whether there are accounts to render
    2. A tuple with a dictionary with keys of account_id and values of account objects.
    """
    c.execute("SELECT id FROM accounts ORDER by id ASC")
    ids = c.fetchall()
    a_dict = {}
    active_accounts = False
    for id in ids:
        a = get_account(id[0])
        a.balance = stringify(a.balance)
        a_dict[id[0]] = a
        if a.deleted == 0:
            active_accounts = True
    return (active_accounts, a_dict)

def delete_account(account_id):
    """
    Deletes an account:
    1. Creates a transaction that zeros account balance (basically a negative income)
    2. Sets account "deleted" flag to true
    """
    with conn:
        a = get_account(account_id)

        # 1. Empty the deleted account
        insert_transaction(Transaction(ACCOUNT_DELETE,f"Deleted account: {a.name}", a.balance, datetime.combine(date.today(), datetime.min.time()), UNALLOCATED, a.id, gen_grouping_num(), "", None, 0, USER_ID))

        # 2. Mark the account as deleted
        c.execute("UPDATE accounts SET deleted=1 WHERE id=?", (account_id,))
        log_write('A DELETE: ' + str(get_account(account_id)))

def restore_account(account_id):
    """
    Restores an account by setting its deleted flag to false
    * Does NOT adjust the account balances, since this is done at the transaction level
    """
    with conn:
        c.execute("UPDATE accounts SET deleted=0 WHERE id=?",(account_id,))
        log_write('A RESTORE: ' + str(get_account(account_id)))

def get_account_balance(id):
    """
    Returns account balance
    """
    c.execute("SELECT balance FROM accounts WHERE id=?", (id,))
    balance = c.fetchone()
    if balance is not None:
        return balance[0]
    else:
        #TODO: Figure out where to log this and how to throw errors
        print("That account doesn't exist you twit.")
        
def edit_account(id, new_name, new_balance):
    """
    Updates account balalnce and name, then subtracts the change in balance from the unallocated envelope
    """
    with conn:
        balance_diff = get_account_balance(id) - new_balance
        adjust_account_balance(id,balance_diff)
        c.execute("UPDATE accounts SET name=? WHERE id=?", (new_name, id))
        log_write('A EDIT: ' + str(get_account(id)))

def update_account_balance(id, balance):
    """
    Updates balance of account with given id
    """
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(balance, id))

def edit_accounts(accounts_to_edit, new_accounts, present_ids):
    """
    Compares an old and new list of accounts, then:
    1.  Updates accounts in DB if their fields are different from those in old_accounts
    2.  Adds new accounts not present in old list
    3.  Deletes old accounts not present in new list
    """
    done_something = False
    c.execute("SELECT id FROM accounts WHERE deleted=0")
    original_account_ids = c.fetchall()

    # 1. Updates info for accounts that exist in both lists
    for a in accounts_to_edit:
        edit_account(int(a.id), a.name, a.balance)
        done_something = True
    # 2. Adds new accounts not present in old list
    for a in new_accounts:
        insert_account(a)
        done_something = True
    # 3. Deletes old accounts not present in new list
    for id in original_account_ids:
        if not (id[0] in present_ids):
            delete_account(id[0])
            done_something = True
    if done_something:
        return "Accounts successfully updated!"
    else:
        return "No changes were made"

def account_transfer(name, amount, date, to_account, from_account, note, schedule, user_id):
    """
    Creates one transaction draining an account, and one transaction filling another
    """
    grouping = gen_grouping_num()
    fill = Transaction(ACCOUNT_TRANSFER, name, -1*amount, date, None, to_account, grouping, note, schedule, False, user_id, 0)
    insert_transaction(fill)
    empty = Transaction(ACCOUNT_TRANSFER, name, amount, date, None, from_account, grouping, note, schedule, False, user_id, 0)
    insert_transaction(empty)

def adjust_account_balance(id, balance_diff):
    """
    Creates ACCOUNT_ADJUST transactions for when the user manually sets the account balance in the account editor
    This transfers the difference into the unallocated envelope.
    """
    # 1. Add a transaction with an amount that will make the account balance equal to the specied balance
    insert_transaction(Transaction(ACCOUNT_ADJUST, f"{get_account(id).name}: Balance Adjustment", balance_diff, datetime.combine(date.today(), datetime.min.time()), UNALLOCATED, id, gen_grouping_num(), "", None, False, USER_ID))


# ---------------ENVELOPE FUNCTIONS--------------- #

def insert_envelope(name, budget, user_id):
    """
    Inserts an envelope into the database with given name and budget and a balance of 0
    """
    with conn:
        c.execute("INSERT INTO envelopes (name, budget, user_id) VALUES (?, ?, ?)", (name,budget,user_id))
        envelope_id = c.lastrowid
        log_write('E INSERT: ' + str(get_envelope(envelope_id)))

def get_envelope(id):
    """
    Returns an envelope object given an envelope_id
    """
    c.execute("SELECT * FROM envelopes WHERE id=?", (id,))
    edata = c.fetchone()
    e = Envelope(edata[1], edata[2], edata[3], edata[4], edata[5])
    e.id = edata[0]
    return e

def get_envelope_dict():
    """
    Used for displaying the envelopes in the side panel and selects.
    Returns:
    1. A boolean that says whether there are envelopes to render
    2. A tuple with a dictionary with keys of envelope_id and values of envelope objects.
    """
    c.execute("SELECT id FROM envelopes ORDER by id ASC")
    ids = c.fetchall()
    e_dict = {}
    active_envelopes = False
    for id in ids:
        e = get_envelope(id[0])
        e.balance = stringify(e.balance)
        e.budget = stringify(e.budget)
        e_dict[id[0]] = e
        if e.deleted == 0 and e.id != 1:
            active_envelopes = True
    return (active_envelopes, e_dict)

def delete_envelope(envelope_id):
    """
    Deletes an envelope:
    1. Creates a transaction that zeros envelope balance
    2. Creates a transaction that adds envelope balance to unallocated envelope
    3. Sets envelope "deleted" flag to true
    """
    with conn:
        if (envelope_id != UNALLOCATED): #You can't delete the unallocated envelope
            e = get_envelope(envelope_id)
            grouping = gen_grouping_num()

            # 1. Empty the deleted envelope
            t_envelope = Transaction(ENVELOPE_DELETE,f"Deleted envelope: {e.name}", e.balance, datetime.combine(date.today(), datetime.min.time()), envelope_id, None, grouping, "", None, 0, USER_ID)
            insert_transaction(t_envelope)

            # 2. Fill the unallocated envelope
            t_unallocated = Transaction(ENVELOPE_DELETE,f"Deleted envelope: {e.name}", -1*e.balance, datetime.combine(date.today(), datetime.min.time()), UNALLOCATED, None, grouping, "", None, 0, USER_ID)
            insert_transaction(t_unallocated)

            # 3. Mark the envelope as deleted
            c.execute("UPDATE envelopes SET deleted=1 WHERE id=?", (envelope_id,))
            log_write('E DELETE: ' + str(get_envelope(envelope_id)))
        else:
            print("You can't delete the 'Unallocated' envelope you moron")

def restore_envelope(envelope_id):
    """
    Restores an envelope by setting its deleted flag to false
    * Does NOT adjust the envelope balances, since this is done at the transaction level
    """
    with conn:
        if (envelope_id != UNALLOCATED):
            c.execute("UPDATE envelopes SET deleted=0 WHERE id=?",(envelope_id,))
            # Do nothing since the unallocated envelope should always be active
            log_write('E RESTORE: ' + str(get_envelope(envelope_id)))

def get_envelope_balance(id):
    """
    Returns envelope balance given envelope id
    """
    c.execute("SELECT balance FROM envelopes WHERE id=?", (id,))
    balance = c.fetchone()
    if balance is not None:
        return balance[0]
    else:
        print("That envelope doesn't exist you imbicil")

def update_envelope_balance(id, balance):
    """
    Updates envelope balance for given id.
    NOTE: This shouldn't be possible as a stand alone action
    """
    with conn:
        c.execute("UPDATE envelopes SET balance=? WHERE id=?",(balance, id))

def edit_envelope(id, name, budget):
    """
    Updates the name and budget for given envelope id
    """
    with conn:
        c.execute("UPDATE envelopes SET name=?, budget=? WHERE id=?",(name, budget, id))
    log_write('E EDIT: ' + str(get_envelope(id)))

def edit_envelopes(old_envelopes, new_envelopes):
    """
    Compares an old and new list of envelopes, then:
    1.  Updates info for envelopes that exist in both lists
    2.  Adds new envelopes not present in old list
    3.  Deletes old envelopes not present in new list
    """
    c.execute("SELECT id FROM envelopes WHERE deleted=0")
    envelope_ids = c.fetchall()
    envelope_ids.remove((1,)) # gets rid of unallocated id (1) in envelope list
    old_ids = []
    # 1. Updates info for envelopes that exist in both lists
    for e in old_envelopes:
        old_ids.append(int(e[0]))
        edit_envelope(int(e[0]), e[1], e[2])
    # 2. Adds new envelopes not present in old list
    for e in new_envelopes:
        insert_envelope(e[0], e[1], e[2])
    # 3. Deletes old envelopes not present in new list
    for id in envelope_ids:
        if not (id[0] in old_ids):
            delete_envelope(id[0])

def envelope_transfer(name, amt, date, to_envelope, from_envelope, note, schedule, user_id):
    """
    Creates a transaction to fill one envelope and another to empty the other
    """
    grouping = gen_grouping_num()
    fill = Transaction(ENVELOPE_TRANSFER, name, -1*amt, date, to_envelope, None, grouping, note, schedule, False, user_id, 0)
    insert_transaction(fill)
    empty = Transaction(ENVELOPE_TRANSFER, name, amt, date, from_envelope, None, grouping, note, schedule, False, user_id, 0)
    insert_transaction(empty)

def envelope_fill(t):
    """
    Takes an ENVELOPE_FILL transaction with an array of envelope ids and amounts and creates sub-transactions to fill the envelopes
    """
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
    """
    Sums the account balances for display
    """
    c.execute("SELECT SUM(balance) FROM accounts WHERE user_id=?", (user_id,))
    total = c.fetchone()[0]
    if not total is None:
        return stringify(total)
    else:
        return stringify(0)

def gen_grouping_num():
    """
    Creates a new and unique grouping number
    """
    # TODO: POSSIBLY CAN DO +1 in SQLITE QUERRY RATHER THAN THIS LOGIC (TEST IN THIS PROGRAM)
    c.execute("SELECT MAX(grouping) FROM transactions")
    prevnum = c.fetchone()[0]
    if prevnum is not None:
        newnum = prevnum + 1
    else:
        newnum = 1
    return newnum

def get_grouping_from_id(id):
    """
    Gets the grouping number from the given id
    """
    c.execute("SELECT grouping FROM transactions WHERE id=?", (id,))
    grouping_touple = c.fetchone()
    if (grouping_touple is None):
        print("There is no transaction with this id: ", id)
    else:
        return grouping_touple[0]

def get_ids_from_grouping(grouping):
    """
    Returns a list of ids associated with a particular grouping number
    """
    id_array = []
    c.execute("SELECT id from transactions WHERE grouping=?", (grouping,))
    id_touple = c.fetchall()
    for i in id_touple:
        id_array.append(i[0])
    return id_array

def get_grouped_json(id):
    """
    Given an id, return a json with the transaction data for each grouped transaction
    """
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
            'a_reconcile_bal': t.a_reconcile_bal,
            'e_reconcile_bal': t.e_reconcile_bal
        })
    return data

def stringify(number):
    """
    Formats number into a nice string to display
    """
    if number is None:
        string = "NAN"
    else:
        negative = number < 0
        string = '$%.2f' % abs(number / 100)
        if negative:
            string = '-' + string
    return string

def date_parse(date_str):
    """
    Converts string to datetime object
    """
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

def print_database(print_all=0,reverse=1):
    """
    Prints the contents of the database to the console.
    If the parameter print_all is 1, it will print all the transactions.
    If no parameter is provided, it will only print the envelopes and accounts
    """
    print()
    if print_all == 1:
        print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv\n")
        print("TRANSACTIONS:")
        c.execute("PRAGMA table_info(transactions)")
        colnames = ''
        for row in c:
            colnames = colnames + row[1] + ', '
        print("(" + colnames[:-2] + ")\n")
        if reverse == 1:
            c.execute("SELECT * FROM transactions ORDER BY day ASC, id ASC")
        else:
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

def health_check(interactive=False):
    """
    1. Compares the sum of all account balances to the sum of all envelope balances
    2. Ensures that all deleted envelopes and accounts have a balance of zero
    3. Checks if stored/displayed account balances equal the sum of their transactions and latest reconcile balance
    4. Checks if stored/displayed envelope balances equal the sum of their transactions and latest reconcile balance
    """
    def hidden_print(str):
        if interactive is True:
            print(str)

    def account_heal(a_id, new_balance):
        print("   Healing account", a_id)
        update_account_balance(a_id, -1*new_balance)
        print("   Account", a_id, "balance set to", -1*new_balance)
        c.execute("SELECT id from transactions WHERE account_id=? ORDER BY day ASC, id ASC LIMIT 1", (a_id,))
        first_t_id = c.fetchone()
        if first_t_id is not None:
            first_t_id = first_t_id[0]
            first_t = get_transaction(first_t_id)
            update_reconcile_amounts(first_t.account_id, first_t.envelope_id, first_t_id, INSERT)
            print("   Account", a_id, "reconcile balances updated.")
        else:
            print("   No transactions in this account!")

    def envelope_heal(e_id, new_balance):
        print("   Healing envelope", e_id)
        update_envelope_balance(e_id, -1*new_balance)
        print("   Envelope", e_id, "balance set to", -1*new_balance)
        c.execute("SELECT id from transactions WHERE envelope_id=? ORDER BY day ASC, id ASC LIMIT 1", (e_id,))
        first_t_id = c.fetchone()
        if first_t_id is not None:
            first_t_id = first_t_id[0]
            first_t = get_transaction(first_t_id)
            update_reconcile_amounts(first_t.account_id, first_t.envelope_id, first_t_id, INSERT)
            print("   Envelope", e_id, "reconcile balances updated.")
        else:
            print("   No transactions in this envelope!")

    healthy = True
    deleted_healthy = True
    bad_e_ids = []
    bad_e_amts_new = []
    bad_a_ids = []
    bad_a_amts_new = []

    # Turn print statements on or off 
    if (interactive is True):
        hidden_print("----------------------")
        hidden_print("BEGINNING HEALTH CHECK")
        hidden_print("----------------------\n")
    
    
    c.execute("SELECT user_id FROM accounts GROUP BY user_id")
    user_ids = c.fetchall()
    for row in user_ids:
        user_id = row[0]

        # ---1. CONFIRM CONSISTENCY BETWEEN SUM OF ENVELOPE BALANCES AND SUM OF ACCOUNT BALANCES---
        hidden_print(f">>> CHECKING TOTALS FOR USER ID:{user_id}")
        # Get accounts total
        c.execute("SELECT SUM(balance) FROM accounts WHERE user_id=?", (user_id,))
        accounts_total = c.fetchone()[0]
        # Get envelopes total
        c.execute("SELECT SUM(balance) FROM envelopes WHERE user_id=?", (user_id,))
        envelopes_total = c.fetchone()[0]
        hidden_print(f" Accounts total: {accounts_total}")
        hidden_print(f" Envelopes total: {envelopes_total}")
        hidden_print(f" Difference: {abs(accounts_total - envelopes_total)}")
        if (accounts_total == envelopes_total):
            hidden_print(" HEALTHY")
        else:
            hidden_print(" INCONSISTENT!!!")
            log_message = f' [A/E Sum Mismatch -> A: {accounts_total} E: {envelopes_total}] Diff: {accounts_total-envelopes_total}'
            healthy = False

        # ---2. CONFIRM THAT DELETED ENVELOPES AND ACCOUNTS ALL HAVE A BALANCE OF ZERO---
        hidden_print(f"\n>>> CHECKING BALANCES OF DELETED ENVELOPES AND ACCOUNTS FOR USER ID:{user_id}")
        c.execute("SELECT id,balance,name FROM accounts WHERE user_id=? AND deleted=1", (user_id,))
        account_info = c.fetchall()
        for account in account_info:
            if account[1] != 0:
                bad_a_ids.append(account[0])
                bad_a_amts_new.append(0)
                deleted_healthy = False
                hidden_print(f" [Deleted A Bal NOT 0 -> {account[2]}({account[0]}) balance: {account[1]}]")
        c.execute("SELECT id,balance,name FROM envelopes WHERE user_id=? AND deleted=1", (user_id,))
        envelope_info = c.fetchall()
        for envelope in envelope_info:
            if envelope[1] != 0:
                bad_e_ids.append(envelope[0])
                bad_e_amts_new.append(0)
                deleted_healthy = False
                hidden_print(f" [Deleted E Bal NOT 0 -> {envelope[2]}({envelope[0]}) balance: {envelope[1]}]")
        if deleted_healthy:
            hidden_print(" HEALTHY")
        else:
            hidden_print(" UNHEALTHY")
            healthy = False
            log_message = ' [UNHEALTHY DELETED ENVELOPE OR ACCOUNT]'
        

        # ---3. ACCOUNTS: CONFIRM THAT THESE THREE VALUES ARE THE SAME---
        #     a. Balances stored in accounts table
        #     b. Sum of all transactions in an account
        #     c. Account reconcile balance on latest transaction
        hidden_print("\n>>> CHECKING ACCOUNTS")
        c.execute("SELECT id,balance,name from accounts")
        accounts = c.fetchall()
        for row in accounts:
            a_name = row[2]
            a_id = row[0]

            # a. Get account balance according to database
            a_balance_db = -1*row[1]

            # b. Get account balance according to summed transaction totals
            c.execute("SELECT SUM(amount) from transactions WHERE account_id=? AND date(day) <= date('now', 'localtime')", (a_id,))
            a_balance_summed = c.fetchone()[0]
            if a_balance_summed is None: #If there's no transactions in the account yet, placeholder of zero
                a_balance_summed = 0

            # c. Get account balance according to latest account reconcile value
            c.execute("SELECT a_reconcile_bal FROM transactions WHERE account_id=? AND date(day) <= date('now', 'localtime') ORDER by day DESC, id DESC LIMIT 1", (a_id,))
            a_balance_reconcile_tuple = c.fetchone()
            if a_balance_reconcile_tuple is None: #If there's no transactions in the account yet, placeholder of zero
                a_balance_reconcile = 0
            else:
                a_balance_reconcile = -1*a_balance_reconcile_tuple[0]

            # d. Check for health!
            if (a_balance_db == a_balance_summed and a_balance_db == a_balance_reconcile and a_balance_summed == a_balance_reconcile):
                hidden_print(f" HEALTHY ---> (ID:{a_id}) {a_name}")
            else:
                log_message = f' [A Total Err -> Name: {a_name}, ID: {a_id}, Disp/Total/Reconcile: {a_balance_db}/{a_balance_summed}/{a_balance_reconcile}]'
                healthy = False
                bad_a_ids.append(a_id)
                bad_a_amts_new.append(a_balance_summed)
                hidden_print(f" WRONG!! ---> (ID:{a_id}) {a_name}")
                hidden_print("     Account balance VS Summed balance VS Reconcile balance")
                hidden_print(f"    {a_balance_db} vs {a_balance_summed} vs {a_balance_reconcile}")
                hidden_print(f" Difference: {abs(a_balance_summed + a_balance_db) + abs(a_balance_summed + a_balance_reconcile)}")

        # ---4. ENVELOPES: CONFIRM THAT THESE THREE VALUES ARE THE SAME---
        #     a. Balances stored in envelopes table
        #     b. Sum of all transactions in an envelope
        #     c. Envelope reconcile balance on latest transaction
        hidden_print("\n>>> CHECKING ENVELOPES")
        c.execute("SELECT id,balance,name from envelopes")
        envelopes = c.fetchall()
        for row in envelopes:
            e_name = row[2]
            e_id = row[0]

            # a. Get envelope balance according to database
            e_balance_db = -1*row[1]

            # b. Get envelope balance according to summed transaction totals
            c.execute("SELECT SUM(amount) from transactions WHERE envelope_id=? AND date(day) <= date('now', 'localtime')", (e_id,))
            e_balance_summed = c.fetchone()[0]
            if e_balance_summed is None: #If there are no transactions in the envelope yet, placeholder of zero
                e_balance_summed = 0

            # c. Get envelope balance according to latest envelope reconcile value
            c.execute("SELECT e_reconcile_bal FROM transactions WHERE envelope_id=? AND date(day) <= date('now', 'localtime') ORDER by day DESC, id DESC LIMIT 1", (e_id,))
            # NOTE: Sum of e_reconcile_bal to avoid nonetype error when no transactions are in the envelope
            e_balance_reconcile_tuple = c.fetchone()
            if e_balance_reconcile_tuple is None: #If there's no transactions in the envelope yet, placeholder of zero
                e_balance_reconcile = 0
            else:
                e_balance_reconcile = -1*e_balance_reconcile_tuple[0]

            # d. Check for health!
            if (e_balance_db == e_balance_summed and e_balance_db == e_balance_reconcile and e_balance_summed == e_balance_reconcile):
                hidden_print(f" HEALTHY ---> (ID:{e_id}) {e_name}")
            else:
                log_message = f' [E Total Err -> Name: {e_name}, ID: {e_id}, Disp/Total/Reconcile: {e_balance_db}/{e_balance_summed}/{e_balance_reconcile}]'
                healthy = False
                bad_e_ids.append(e_id)
                bad_e_amts_new.append(e_balance_summed)
                hidden_print(f" WRONG!! ---> (ID:{e_id}) {e_name}")
                hidden_print("     Envelope balance VS Summed balance VS Reconcile Balance")
                hidden_print(f"    {e_balance_db} vs {e_balance_summed} vs {e_balance_reconcile}")
                hidden_print(f" Difference: {abs(e_balance_db - e_balance_summed) + abs(e_balance_db - e_balance_reconcile)}")

        hidden_print(f"\nBad Account IDs: {bad_a_ids}")
        hidden_print(f"Bad Envelope IDs: {bad_e_ids}")

        hidden_print("\n---------------------")
        hidden_print("HEALTH CHECK COMPLETE")
        hidden_print("---------------------\n")

        if (not healthy):
            hidden_print("STATUS -> UNHEALTHY")
            log_write(log_message)
            if not interactive:
                return healthy
            else:
                if (deleted_healthy is False):
                    hidden_print("There is an error with your deleted envelopes or accounts that must be fixed manually!\n")
                else:
                    choice_valid = False
                    while (choice_valid == False):
                        choice = input("Would you like to continue healing the database? (y/n):")
                        if (choice == 'y' or choice =='Y' or choice == 'yes' or choice == 'Yes' or choice =='YES'):
                            choice_valid = True
                            hidden_print("Healing database...")
                            for i in range(0,len(bad_a_ids)):
                                account_heal(bad_a_ids[i], bad_a_amts_new[i])

                            for i in range(0,len(bad_e_ids)):
                                envelope_heal(bad_e_ids[i], bad_e_amts_new[i])
                            hidden_print("Database heal complete!")
                            log_write('-----Account healed!-----\n')
                        elif (choice == 'n' or choice == 'N' or choice =='no' or choice =='No' or choice =='NO'):
                            choice_valid = True
                            hidden_print("Database heal aborted.")
                        else:
                            hidden_print("Invalid option. Try again.")

        else:
            hidden_print("STATUS -> HEALTHY\n")
            hidden_print("(No further action required.)\n\n")
            return healthy

def log_write(text):
    """
    Writes a message to an EventLog.txt file
    """
    with open("EventLog.txt",'a') as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + " " + text+"\n")

def main():
    health_check(True)
    # print_database()

if __name__ == "__main__":
    main()
