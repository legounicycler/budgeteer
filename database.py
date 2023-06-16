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
    database = '/home/opc/database.sqlite'

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
    def __init__(self, type, name, amt, date, envelope_id, account_id, grouping, note, schedule, status, user_id):
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
    def __repr__(self):
        return "ID:{}, TYPE:{}, NAME:{}, AMT:{}, DATE:{}, E_ID:{}, A_ID:{}, GRP:{}, NOTE:{}, SCHED:{}, STATUS:{}, U_ID:{}".format(self.id,self.type,self.name,self.amt,self.date,self.envelope_id,self.account_id,self.grouping,self.note,self.schedule,self.status,self.user_id)
    def __str__(self):
        return "ID:{}, TYPE:{}, NAME:{}, AMT:{}, DATE:{}, E_ID:{}, A_ID:{}, GRP:{}, NOTE:{}, SCHED:{}, STATUS:{}, U_ID:{}".format(self.id,self.type,self.name,self.amt,self.date,self.envelope_id,self.account_id,self.grouping,self.note,self.schedule,self.status,self.user_id)


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
    def __init__(self, name, balance, budget, deleted, user_id, display_order):
        self.id = None
        self.name = name
        self.balance = balance
        self.budget = budget
        self.deleted = deleted
        self.user_id = user_id
        self.display_order = display_order
    def __repr__(self):
        return "ID:{}, NAME:{}, BAL:{}, BUDG:{}, DEL:{}, U_ID:{}, DISP:{}".format(self.id,self.name,self.balance,self.budget,self.deleted,self.user_id,self.display_order)
    def __str__(self):
        return "ID:{}, NAME:{}, BAL:{}, BUDG:{}, DEL:{}, U_ID:{}, DISP:{}".format(self.id,self.name,self.balance,self.budget,self.deleted,self.user_id,self.display_order)

# ----- Helper functions ----- #
def unpack(list_of_tuples):
    unpacked_array = []
    for item in list_of_tuples:
        unpacked_array.append(item[0])
    return unpacked_array

# ---------------TRANSACTION FUNCTIONS--------------- #

def insert_transaction(t):
    """
    Inserts transaction into database, then updates account/envelope balances
    """
    with conn:
        # ---1. INSERT THE TRANSACTION INTO THE TABLE---
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)",
        (t.id, t.type, t.name, t.amt, t.date, t.envelope_id, t.account_id,  t.grouping, t.note, t.schedule, t.status, t.user_id))
        
        # ---2. UPDATE THE ACCOUNT/ENVELOPE BALANCES---
        if (t.date < datetime.now()): #Only update balances if transaction is not scheduled for later
            if t.account_id is not None:
                newaccountbalance = get_account_balance(t.account_id) - t.amt
                update_account_balance(t.account_id, newaccountbalance)
            if t.envelope_id is not None:
                newenvelopebalance = get_envelope_balance(t.envelope_id) - t.amt
                update_envelope_balance(t.envelope_id, newenvelopebalance)

    log_write('T INSERT: ' + str(t))

def get_transaction(id):
    """
    Retrieves transaction object from database given its ID
    """
    c.execute("SELECT * FROM transactions WHERE id=?", (id,))
    tdata = c.fetchone()
    t = Transaction(tdata[1],tdata[2],tdata[3],tdata[4],tdata[5],tdata[6],tdata[7],tdata[8],tdata[9],tdata[10],tdata[11])
    t.date = date_parse(t.date) # Convert string to datetime object
    t.id = tdata[0]
    return t

def get_home_transactions(start, amount):
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
    for id in groupings:
        t = get_transaction(id[0])

        # Set the amount for display
        if t.type == BASIC_TRANSACTION or t.type == INCOME or t.type == ACCOUNT_ADJUST or t.type == ACCOUNT_DELETE:
             t.amt = -1 * t.amt
        elif t.type == ENVELOPE_TRANSFER:
            # Get the id for the other envelope and put it in the t.account_id field for special display in the .transaction-details div
            t_ids = get_ids_from_grouping(t.grouping)
            if (t.amt > 0):
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
            # Get the id for the other account and put it in the t.account_id field for special display in the .transaction-details div
            t_ids = get_ids_from_grouping(t.grouping)
            if (t.amt > 0):
                from_account_id = get_transaction(t_ids[0]).account_id
                to_account_id = get_transaction(t_ids[1]).account_id
            else:
                from_account_id = get_transaction(t_ids[1]).account_id
                to_account_id = get_transaction(t_ids[0]).account_id
            # Display format (eID -> aID) or for account transfers, (fromAccount -> toAccount)
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
    c.execute("SELECT id FROM transactions WHERE envelope_id=? ORDER by day DESC, id DESC LIMIT ? OFFSET ?", (envelope_id, amount, start))
    ids = unpack(c.fetchall())
    tlist = []
    for id in ids:
        t = get_transaction(id)
        # For display purposes, the envelope ID displays first, then the account ID in the .transaction-details div
        if t.type == ENVELOPE_TRANSFER:
            t_ids = get_ids_from_grouping(t.grouping)
            if (t.amt == 0): # If amt is 0: Display the envelope order based on the order they come out of the database
                from_envelope_id = get_transaction(t_ids[1]).envelope_id
                to_envelope_id = get_transaction(t_ids[0]).envelope_id
            elif (t.amt > 0): # If amt is positive: Actual amt is negative, which means the envelope is being drained, which means it's FROM 
                t_ids.remove(t.id) #Remove the transaction with the positive balance
                from_envelope_id = t.envelope_id
                to_envelope_id = get_transaction(t_ids[0]).envelope_id
            elif (t.amt < 0): # If amt is negative: Actual amt is positive, which means the envelope is being filled, which means it's TO
                t_ids.remove(t.id) #Remove the transaction with the positive balance
                to_envelope_id = t.envelope_id
                from_envelope_id = get_transaction(t_ids[0]).envelope_id
            # Display format (eID -> aID) or for envelope transfers, (fromEnvelope -> toEnvelope)
            t.envelope_id = from_envelope_id # When displaying transactions, envelope ID is always displayed first.
            t.account_id = to_envelope_id    # When displaying transactions, account ID is always displayed second

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
            # Get the id for the other account and put it in the t.account_id field for special display in the .transaction-details div
            t_ids = get_ids_from_grouping(t.grouping)
            # Display format (eID -> aID) or for account transfers, (fromAccount -> toAccount)
            t_ids = get_ids_from_grouping(t.grouping)
            if (t.amt == 0): # If amt is 0: Display the account order based on the order they come out of the database
                from_account_id = get_transaction(t_ids[1]).account_id
                to_account_id = get_transaction(t_ids[0]).account_id
            elif (t.amt > 0): # If amt is positive: Actual amt is negative, which means the account is being drained, which means it's FROM 
                t_ids.remove(t.id) #Remove the transaction with the positive balance
                from_account_id = t.account_id
                to_account_id = get_transaction(t_ids[0]).account_id
            elif (t.amt < 0): # If amt is negative: Actual amt is positive, which means the account is being filled, which means it's TO
                t_ids.remove(t.id) #Remove the transaction with the positive balance
                to_account_id = t.account_id
                from_account_id = get_transaction(t_ids[0]).account_id
            # Display format (eID -> aID) or for account transfers, (fromaccount -> toaccount)
            t.envelope_id = from_account_id # When displaying transactions, envelope ID is always displayed first.
            t.account_id = to_account_id    # When displaying transactions, account ID is always displayed second
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

def delete_transaction(t_id):
    """
    Deletes transaction and associated grouped transactions and updates appropriate envelope/account balances
    """
    with conn:
        # 1. Get all the grouped transactions to delete
        ids = get_grouped_ids_from_id(t_id)
        for id in ids:                
            t = get_transaction(id)
            # 2a. If you're deleting an "ENVELOPE_DELETE" transaction, restore the envelope
            if t.type == ENVELOPE_DELETE:
                if t.envelope_id is not UNALLOCATED: # Don't try to restore the unallocated envelope since it can't be deleted
                    if (get_envelope(t.envelope_id).deleted is not False): # Don't try to restore an envelope that is not deleted
                        restore_envelope(t.envelope_id)
            
            # 2b. If you're deleting an "ACCOUNT_DELETE" transaction, restore the account
            if t.type == ACCOUNT_DELETE:
                if (get_account(t.account_id).deleted is not False): # Don't try to restore an account that is not deleted
                    restore_account(t.account_id)

            # 4. If it is not a transaction in the future, update envelope/account balances
            if (t.date < datetime.now()): #TODO: This will probably need to change when timezones are implemented
                if t.envelope_id is not None:
                    if bool(get_envelope(t.envelope_id).deleted) is not True:
                        update_envelope_balance(t.envelope_id, get_envelope_balance(t.envelope_id) + t.amt)
                    else:
                        update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) + t.amt)
                        # When deleting a transaction referencing a deleted envelope, you must also update the amount of the
                        # ENVELOPE_DELETE transactions so the deleted envelope maintains a balance of $0.
                        # i.e. If you delete a $1 transaction in a deleted envelope, the money does not go back into the envelope since it's deleted
                        #      instead, it goes to the unallocated envelope, but now the sum of transactions in your deleted envelopes will not be $0
                        #      unless you change the amount ENVELOPE_DELETE transaction(s) (which drains the deleted envelope balance down to 0).

                        # Step 1. Get both the ID's for the ENVELOPE_DELETE transactions of the deleted envelope referenced by the transaction
                        c.execute("""SELECT id FROM transactions WHERE grouping = (
                                        SELECT grouping FROM transactions WHERE (type=? AND envelope_id=?)
                                    )""", (ENVELOPE_DELETE, t.envelope_id)
                                    )
                        e_delete_ids = unpack(c.fetchall())

                        # Step 2. Get the ENVELOPE_DELETE transactions
                        for e_delete_id in e_delete_ids:
                            e_delete_t = get_transaction(e_delete_id)

                            # Step 3. Change the amount by which you will adjust the transaction amount depending on whether
                            #         it was filling or draining the envelopes in the ENVELOPE_DELETE transaction.
                            if e_delete_t.envelope_id == UNALLOCATED:
                                amt = t.amt*-1
                            else:
                                amt = t.amt

                            # Step 4. Update the ENVELOPE_DELETE transaction amount
                            c.execute("UPDATE transactions SET amount=? WHERE id=?",(e_delete_t.amt + amt, e_delete_id))
                            log_write('T UPDATE: ' + str(e_delete_t))
                        
                if t.account_id is not None:
                    if bool(get_account(t.account_id).deleted) is not True:
                        update_account_balance(t.account_id, get_account_balance(t.account_id) + t.amt)
                    else:
                        update_envelope_balance(UNALLOCATED, get_envelope_balance(UNALLOCATED) - t.amt)

                        # When deleting a transaction referencing a deleted account, you must also update the amount of the
                        # ACCOUNT_DELETE transactions so the deleted account maintains a balance of $0.
                        # i.e. If you delete a $1 transaction in a deleted account, the money does not go back into the account since it's deleted
                        #      instead, it goes to the unallocated envelope, but now the sum of transactions in your deleted account will not be $0
                        #      unless you change the amount ACCOUNT_DELETE transaction (which drains the deleted account balance down to 0).

                        # Step 1. Get the id of the ACCOUNT_DELETE transaction
                        c.execute("""SELECT id FROM transactions WHERE (type=? AND account_id=?)""", (ACCOUNT_DELETE, t.account_id))
                        a_delete_id = c.fetchone()[0]
                        print(a_delete_id)
                        a_delete_t = get_transaction(a_delete_id)
                        print(a_delete_t)

                        # Step 2. Update the ACCOUNT_DELETE transaction amount
                        c.execute("UPDATE transactions SET amount=? WHERE id=?",(a_delete_t.amt + t.amt, a_delete_id))
                        log_write('T UPDATE: ' + str(a_delete_t))

            # 6. Delete the actual transaction from the database
            c.execute("DELETE FROM transactions WHERE id=?", (id,))
            log_write('T DELETE: ' + str(t))

def new_split_transaction(t):
    """
    Takes a transaction with arrays of amt and envelope_id and creates individual transactions
    This is a grouped transaction with multiple envelopes!
    """
    # 1. Combine/sum subtransactions from the same envelope
    compressed_e_ids = []
    compressed_amts = []
    for i in range(len(t.envelope_id)):
        if t.envelope_id[i] not in compressed_e_ids:
            compressed_e_ids.append(t.envelope_id[i])
            compressed_amts.append(t.amt[i])
        else:
            n = compressed_e_ids.index(t.envelope_id[i])
            compressed_amts[n] = compressed_amts[n] + t.amt[i]

    # 2. Generate shared grouping number
    grouping = gen_grouping_num()

    # 3. Insert the transaction
    if len(compressed_e_ids) == 1: #If every part of the split transaction went to the same envelope, it's basically a normal transaction
        insert_transaction(Transaction(BASIC_TRANSACTION, t.name, compressed_amts[0], t.date, compressed_e_ids[0], t.account_id, grouping, t.note, t.schedule, t.status, t.user_id))
    else:
        for i in range(len(compressed_e_ids)):
            insert_transaction(Transaction(SPLIT_TRANSACTION, t.name, compressed_amts[i], t.date, compressed_e_ids[i], t.account_id, grouping, t.note, t.schedule, t.status, t.user_id))

# ---------------ACCOUNT FUNCTIONS--------------- #

def insert_account(account):
    """
    Inserts new account and creates "initial account balance" transaction
    """
    with conn:
        c.execute("INSERT INTO accounts (name, balance, user_id) VALUES (?, ?, ?)", (account.name, 0, account.user_id))
    account_id = c.lastrowid
    income_name = 'Initial Account Balance: ' + account.name
    log_write('A INSERT: ' + str(get_account(account_id)))
    insert_transaction(Transaction(INCOME, income_name, -1 * account.balance, datetime.combine(date.today(), datetime.min.time()), 1, account_id, gen_grouping_num(), '', None, False, account.user_id))

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
        adjust_account_balance(id, balance_diff)
        c.execute("UPDATE accounts SET name=? WHERE id=?", (new_name, id))
        log_write('A EDIT: ' + str(get_account(id)))

def update_account_balance(id, balance):
    """
    Updates balance of account with given id
    NOTE: This shouldn't be possible as a stand alone action. It should always follow a transaction adjusting the balance.
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
    insert_transaction(Transaction(ACCOUNT_TRANSFER, name, -1*amount, date, None, to_account, grouping, note, schedule, False, user_id)) #Fill
    insert_transaction(Transaction(ACCOUNT_TRANSFER, name, amount, date, None, from_account, grouping, note, schedule, False, user_id))  #Empty

def adjust_account_balance(id, balance_diff):
    """
    Creates ACCOUNT_ADJUST transactions for when the user manually sets the account balance in the account editor
    This transfers the difference into the unallocated envelope.
    """
    # 1. Add a transaction with an amount that will make the account balance equal to the specied balance
    insert_transaction(Transaction(ACCOUNT_ADJUST, f"{get_account(id).name}: Balance Adjustment", balance_diff, datetime.combine(date.today(), datetime.min.time()), UNALLOCATED, id, gen_grouping_num(), "", None, False, USER_ID))


# ---------------ENVELOPE FUNCTIONS--------------- #

def insert_envelope(e):
    """
    Inserts an envelope into the database with given name and budget and the default balance of 0
    """
    with conn:
        c.execute("INSERT INTO envelopes (name, budget, user_id, display_order) VALUES (?, ?, ?, ?)", (e.name, e.budget, e.user_id, e.display_order))
        log_write('E INSERT: ' + str(get_envelope(c.lastrowid)))

def get_envelope(id):
    """
    Returns an envelope object given an envelope_id
    """
    c.execute("SELECT * FROM envelopes WHERE id=?", (id,))
    edata = c.fetchone()
    e = Envelope(edata[1], edata[2], edata[3], edata[4], edata[5], edata[6])
    e.id = edata[0]
    return e

def get_envelope_dict():
    """
    Used for displaying the envelopes in the side panel and selects.
    Returns:
    1. A boolean that says whether there are envelopes to render
    2. A tuple with a dictionary with keys of envelope_id and values of envelope objects.
    3. A string displaying the total budget for all envelopes
    """
    c.execute("SELECT id FROM envelopes ORDER by display_order ASC, id ASC")
    ids = unpack(c.fetchall())
    e_dict = {}
    active_envelopes = False
    budget_total = 0
    for id in ids:
        e = get_envelope(id)
        e.balance = stringify(e.balance)
        e_dict[id] = e
        if e.deleted == 0 and e.id != 1:
            active_envelopes = True
            budget_total = budget_total + e.budget
        e.budget = stringify(e.budget)
    return (active_envelopes, e_dict, stringify(budget_total))

def get_envelope_order():
    """
    Used for determining when the envelope order has changed within the envelope editor.
    Returns:
    1. A dictionary with keys of envelope id and values of display order
    """
    with conn:
        c.execute("SELECT id,display_order FROM envelopes WHERE deleted=0 AND id!=? ORDER BY id ASC", (UNALLOCATED,))
        tuple_array = c.fetchall()
        display_dict = dict()
        for id, display_order in tuple_array:
            display_dict.setdefault(id,[]).append(display_order)
        return display_dict

def delete_envelope(envelope_id):
    """
    Deletes an envelope:
    1. Creates a transaction that zeros envelope balance
    2. Creates a transaction that adds envelope balance to unallocated envelope
    3. Sets envelope "deleted" flag to true
    4. Sets display_order of deleted envelope to NULL
    """
    with conn:
        if (envelope_id != UNALLOCATED): #You can't delete the unallocated envelope
            e = get_envelope(envelope_id)
            grouping = gen_grouping_num()

            # 1. Empty the deleted envelope
            insert_transaction(Transaction(ENVELOPE_DELETE,f"Deleted envelope: {e.name}", e.balance, datetime.combine(date.today(), datetime.min.time()), envelope_id, None, grouping, "", None, 0, USER_ID))

            # 2. Fill the unallocated envelope
            insert_transaction(Transaction(ENVELOPE_DELETE,f"Deleted envelope: {e.name}", -1*e.balance, datetime.combine(date.today(), datetime.min.time()), UNALLOCATED, None, grouping, "", None, 0, USER_ID))

            # 3. Mark the envelope as deleted
            c.execute("UPDATE envelopes SET deleted=1 WHERE id=?", (envelope_id,))
            log_write('E DELETE: ' + str(get_envelope(envelope_id)))

            # 4. Set display_order of deleted envelope to NULL
            c.execute("UPDATE envelopes SET display_order=NULL WHERE id=?", (envelope_id,))
        else:
            print("You can't delete the 'Unallocated' envelope you moron")

def restore_envelope(envelope_id):
    """
    Restores an envelope by setting its deleted flag to false
    * Does NOT adjust the envelope balances, since this is done at the transaction level
    """
    with conn:
        c.execute("UPDATE envelopes SET deleted=0 WHERE id=?",(envelope_id,))
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
    NOTE: This shouldn't be possible as a stand alone action. It should always follow a transaction adjusting the balance.
    """
    with conn:
        c.execute("UPDATE envelopes SET balance=? WHERE id=?",(balance, id))

def edit_envelope(id, new_name, new_budget, new_order):
    """
    Updates the name, budget, and order for given envelope id
    """
    with conn:
        c.execute("UPDATE envelopes SET name=?, budget=?, display_order=? WHERE id=?",(new_name, new_budget, new_order, id))
    log_write('E EDIT: ' + str(get_envelope(id)))

def edit_envelopes(envelopes_to_edit, new_envelopes, present_ids):
    """
    Inputs:
    1.  envelopes_to_edit: A list of envelope objects that have different names, budgets, or orders than what is stored in the database
    2.  new_envelopes: A lit of brand new envelope objects to be inserted into the database
    3.  present_ids: A list of all id's present in the envelope editor modal (notably missing any that were deleted by the user)
    """
    done_something = False
    c.execute("SELECT id FROM envelopes WHERE deleted=0")
    original_envelope_ids = unpack(c.fetchall())

    # 1. Updates info for envelopes
    for e in envelopes_to_edit:
        edit_envelope(int(e.id), e.name, e.budget, e.display_order)
        done_something = True
    # 2. Adds new envelopes
    for e in new_envelopes:
        insert_envelope(e)
        done_something = True
    # 3. Deletes any envelopes in the database that are no longer in the present_ids submitted from the form
    for id in original_envelope_ids:
        if not id in present_ids and id != UNALLOCATED:
            delete_envelope(id)
            done_something = True
    if done_something:
        return "Envelopes successfully updated!"
    else:
        return "No changes were made"

def envelope_transfer(name, amt, date, to_envelope, from_envelope, note, schedule, user_id):
    """
    Creates a transaction to fill one envelope and another to empty the other
    """
    grouping = gen_grouping_num()
    insert_transaction(Transaction(ENVELOPE_TRANSFER, name, -1*amt, date, to_envelope, None, grouping, note, schedule, False, user_id)) #Fill
    insert_transaction(Transaction(ENVELOPE_TRANSFER, name, amt, date, from_envelope, None, grouping, note, schedule, False, user_id))  #Empty

def envelope_fill(t):
    """
    Takes an ENVELOPE_FILL transaction with an array of envelope ids and amounts and creates sub-transactions to fill the envelopes
    """
    if t.type == ENVELOPE_FILL:
        grouping = gen_grouping_num()
        amts = t.amt
        envelopes = t.envelope_id
        for i in range(len(amts)):
            # Empty the unallocated envelope
            insert_transaction(Transaction(ENVELOPE_FILL, t.name, amts[i], t.date, UNALLOCATED, None, grouping, t.note, t.schedule, False, t.user_id))
            # Fill the other envelopes
            insert_transaction(Transaction(ENVELOPE_FILL, t.name, amts[i] * -1, t.date, envelopes[i], None, grouping, t.note, t.schedule, False, t.user_id))
    else:
        print("You can't pass a transaction into this function that's not an ENVELOPE_FILL you absolute numbskull!")


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
    Returns a new and unique grouping number
    """
    # TODO: POSSIBLY CAN DO +1 in SQLITE QUERRY RATHER THAN THIS LOGIC (TEST IN THIS PROGRAM)
    c.execute("SELECT MAX(grouping) FROM transactions")
    prevnum = c.fetchone()[0]
    if prevnum is not None:
        newnum = prevnum + 1
    else:
        newnum = 1
    return newnum

def get_grouping_from_id(t_id):
    """
    Returns the grouping number from the transaction with the given id
    """
    c.execute("SELECT grouping FROM transactions WHERE id=?", (t_id,))
    grouping_touple = c.fetchone()
    if (grouping_touple is None):
        print("There is no transaction with this id: ", t_id)
    else:
        return grouping_touple[0]

def get_ids_from_grouping(grouping):
    """
    Returns a list of ids associated with a particular grouping number
    """
    c.execute("SELECT id from transactions WHERE grouping=?", (grouping,))
    return unpack(c.fetchall())

def get_grouped_ids_from_id(t_id):
    """
    Returns a list of ids for all transactions with the same grouping number as the transaction with the given id
    """
    c.execute("SELECT id from transactions WHERE grouping = (SELECT grouping FROM transactions WHERE id=?)", (t_id,))
    return unpack(c.fetchall())


def get_grouped_json(t_id):
    """
    Given an id, return a json with the transaction data for each grouped transaction
    """
    ids = get_grouped_ids_from_id(t_id)
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
    """
    Formats amount numbers into a string with a "$" and "-" if necessary for display
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
        # TODO: Change to actually throw an error instead of just crashing things by
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
    c.execute("SELECT * FROM envelopes ORDER BY display_order ASC, id ASC")
    for row in c:
        print(row)
    print()
    print("TOTAL FUNDS: ", get_total(USER_ID))
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n")

def health_check(interactive=False):
    """
    1. Compares the sum of all account balances to the sum of all envelope balances
    2. Ensures that all deleted envelopes and accounts have a balance of zero
    3. Checks if stored/displayed account balances equal the sum of their transactions
    4. Checks if stored/displayed envelope balances equal the sum of their transactions
    """
    def hidden_print(str):
        if interactive is True:
            print(str)

    def account_heal(a_id, new_balance):
        print("   Healing account", a_id)
        update_account_balance(a_id, -1*new_balance)
        print("   Account", a_id, "balance set to", -1*new_balance)

    def envelope_heal(e_id, new_balance):
        print("   Healing envelope", e_id)
        update_envelope_balance(e_id, -1*new_balance)
        print("   Envelope", e_id, "balance set to", -1*new_balance)

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
    user_ids = unpack(c.fetchall())
    for user_id in user_ids:
        
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


        # ---3. ACCOUNTS: CONFIRM THAT THESE VALUES ARE THE SAME---
        #     a. Balances stored in accounts table
        #     b. Sum of all transactions in an account
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

            # c. Check for health!
            if (a_balance_db == a_balance_summed):
                hidden_print(f" HEALTHY ---> (ID:{a_id}) {a_name}")
            else:
                log_message = f' [A Total Err -> Name: {a_name}, ID: {a_id}, Disp vs Total: {a_balance_db} vs {a_balance_summed}]'
                healthy = False
                bad_a_ids.append(a_id)
                bad_a_amts_new.append(a_balance_summed)
                hidden_print(f" WRONG!! ---> (ID:{a_id}) {a_name}")
                hidden_print("     Account balance VS Summed balance")
                hidden_print(f"    {a_balance_db} vs {a_balance_summed}")
                hidden_print(f" Difference: {abs(a_balance_summed + a_balance_db)}")

        # ---4. ENVELOPES: CONFIRM THAT THESE THREE VALUES ARE THE SAME---
        #     a. Balances stored in envelopes table
        #     b. Sum of all transactions in an envelope
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

            # c. Check for health!
            if (e_balance_db == e_balance_summed):
                hidden_print(f" HEALTHY ---> (ID:{e_id}) {e_name}")
            else:
                log_message = f' [E Total Err -> Name: {e_name}, ID: {e_id}, Disp vs Total: {e_balance_db} vs {e_balance_summed}]'
                healthy = False
                bad_e_ids.append(e_id)
                bad_e_amts_new.append(e_balance_summed)
                hidden_print(f" WRONG!! ---> (ID:{e_id}) {e_name}")
                hidden_print("     Envelope balance VS Summed balance")
                hidden_print(f"    {e_balance_db} vs {e_balance_summed}")
                hidden_print(f" Difference: {abs(e_balance_db - e_balance_summed)}")

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
    print_database()

if __name__ == "__main__":
    main()
