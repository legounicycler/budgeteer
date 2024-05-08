"""
This file contains functions relevant to actually manipulating values in the database
"""

# Library imports
import sqlite3, datetime, platform, hashlib, secrets, calendar, copy
from datetime import datetime, timedelta, date
from flask_login import UserMixin
from enum import Enum

# Custom Imports
from exceptions import *
from logging import *
from filters import balanceformat

app_platform = platform.system()
if app_platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/opc/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

class TType(Enum):
    BASIC_TRANSACTION = (0, "Basic Transaction", "local_atm")
    ENVELOPE_TRANSFER = (1, "Envelope Transfer", "swap_horiz")
    ACCOUNT_TRANSFER = (2, "Account Transfer", "swap_vert")
    INCOME = (3, "Income", "vertical_align_top")
    SPLIT_TRANSACTION = (4, "Split Transaction", "call_split")
    ENVELOPE_FILL = (5, "Envelope Fill", "input")
    ENVELOPE_DELETE = (6, "Envelope Delete", "layers_clear")
    ACCOUNT_DELETE = (7, "Account Delete", "lmoney_off")
    ACCOUNT_ADJUST = (8, "Account Adjust", "build")

    def __init__(self, id, desc, icon):
        self.id = id # Integer value (used in database)
        self.desc = desc # Human readable name (used in hover text)
        self.icon = icon # Materialize icon name
    
    @classmethod
    def from_int(cls, value):
        for t in cls:
            if t.value[0] == value:
                return t
        raise ValueError(f"ERROR: {value} is not a valid TType value!")

    

# region ---------------CLASS DEFINITIONS---------------

class Transaction:
    def __init__(self, type: 'TType', name, amt, date, envelope_id, account_id, grouping, note, schedule, status, user_id, pending):
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
        self.pending = pending
    def __repr__(self):
        return "ID:{}, TYPE:{}, NAME:{}, AMT:{}, DATE:{}, E_ID:{}, A_ID:{}, GRP:{}, NOTE:{}, SCHED:{}, STATUS:{}, U_ID:{}, PENDING:{}".format(self.id,self.type,self.name,self.amt,self.date,self.envelope_id,self.account_id,self.grouping,self.note,self.schedule,self.status,self.user_id,self.pending)
    def __str__(self):
        return "ID:{}, TYPE:{}, NAME:{}, AMT:{}, DATE:{}, E_ID:{}, A_ID:{}, GRP:{}, NOTE:{}, SCHED:{}, STATUS:{}, U_ID:{}, PENDING:{}".format(self.id,self.type,self.name,self.amt,self.date,self.envelope_id,self.account_id,self.grouping,self.note,self.schedule,self.status,self.user_id,self.pending)

class Account:
    def __init__(self, id, name, balance, deleted, user_id, display_order):
        self.id = id
        self.name = name
        self.balance = balance
        self.deleted = deleted
        self.user_id = user_id
        self.display_order = display_order
    def __repr__(self):
        return "ID:{}, NAME:{}, BAL:{}, DEL:{}, U_ID:{}, DISP:{}".format(self.id,self.name,self.balance,self.deleted,self.user_id,self.display_order)
    def __str__(self):
        return "ID:{}, NAME:{}, BAL:{}, DEL:{}, U_ID:{}, DISP:{}".format(self.id,self.name,self.balance,self.deleted,self.user_id,self.display_order)

class Envelope:
    def __init__(self, id, name, balance, budget, deleted, user_id, display_order):
        self.id = id
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

class User(UserMixin):
    def __init__(self, uuid, email, password_hash, password_salt, first_name, last_name, registered_on, unallocated_e_id=None, confirmed=False, confirmed_on=None):
        self.id = uuid
        self.email = email
        self.password_hash = password_hash
        self.password_salt = password_salt
        self.first_name = first_name
        self.last_name = last_name
        self.registered_on = registered_on
        self.unallocated_e_id = unallocated_e_id
        self.confirmed = confirmed
        self.confirmed_on = confirmed_on
    def hash_password(password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
        return hashed_password, salt
    def check_password(self, password):
        return User.hash_password(password, self.password_salt)[0] == self.password_hash
    def __repr__(self):
        return '<UUID: {}, EMAIL: {}, PWD_HASH: {}, SALT: {}, FIRST: {}, LAST: {}, U_EID: {}, REG_ON: {}, CONF: {}, CONF_ON: {}>'.format(self.id, self.email, self.password_hash, self.password_salt, self.first_name, self.last_name, self.unallocated_e_id, self.registered_on, self.confirmed, self.confirmed_on)
    def __str__(self):
        return '<UUID: {}, EMAIL: {}, PWD_HASH: {}, SALT: {}, FIRST: {}, LAST: {}, U_EID: {}, REG_ON: {}, CONF: {}, CONF_ON: {}>'.format(self.id, self.email, self.password_hash, self.password_salt, self.first_name, self.last_name, self.unallocated_e_id, self.registered_on, self.confirmed, self.confirmed_on)

# endregion CLASS DEFINITIONS

# region ---------------HELPER FUNCTIONS---------------
def unpack(list_of_tuples):
    unpacked_array = []
    for item in list_of_tuples:
        unpacked_array.append(item[0])
    return unpacked_array

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
        raise TimestampParseError(f"ERROR: Timestamp {date_str} could not be parsed!")
    return date

def add_months(sourcedate, months):
  """
  Adds an integer amount of months to a given date.
  Returns the new date.
  """
  month = sourcedate.month - 1 + months
  year = sourcedate.year + month // 12
  month = month % 12 + 1
  day = min(sourcedate.day, calendar.monthrange(year,month)[1])
  return date(year, month, day)

def schedule_date_calc(tdate, schedule, timestamp, should_consider_timestamp):
  """
  Calculates the upcoming transaction date for a scheduled transaction based on its frequency and the user's timestamp.
  Returns the date of the next transaction.
  If should_consider_timestamp is true, the next date will be the first valid date after the timestamp. Otherwise, it will be the first valid date after the transaction date.
  """
  date_is_pending = False
  while not date_is_pending:
    if (schedule=="daily"):
      nextdate = tdate + timedelta(days=1)
    elif (schedule=="weekly"):
      nextdate = tdate + timedelta(days=7)
    elif (schedule=="biweekly"):
      nextdate = tdate + timedelta(days=14)
    elif (schedule=="monthly"):
      nextdate = add_months(tdate,1)
    elif (schedule=="endofmonth"):
      lastmonthday = calendar.monthrange(tdate.year, tdate.month)[1]
      if (tdate.day == lastmonthday):
        nextdate = add_months(tdate,1)
      else:
        nextdate = date(tdate.year, tdate.month, lastmonthday)
    elif (schedule=="semianually"):
      nextdate = add_months(tdate,6)
    elif (schedule=="anually"):
      nextdate = add_months(tdate,12)
    else:
      raise InvalidFormDataError("ERROR: Invalid schedule option!")
    
    nextdate = datetime.combine(nextdate, datetime.min.time())
    if nextdate > timestamp:
      date_is_pending = True
    else:
      tdate = nextdate
      if not should_consider_timestamp:
        break
  return nextdate

def is_pending(date, timestamp):
  if date > timestamp:
    return True
  else:
    return False

# endregion HELPER FUNCTIONS

# region ---------------TRANSACTION FUNCTIONS--------------- 

def insert_transaction(t):
    """
    Inserts transaction into database, then applies it to the envelope/account totals if it is not pending
    """
    with conn:
        # ---1. INSERT THE TRANSACTION INTO THE TABLE---
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)",
        (t.id, t.type.id, t.name, t.amt, t.date, t.envelope_id, t.account_id, t.grouping, t.note, t.schedule, t.status, t.user_id, t.pending))
        
        # ---2. UPDATE THE ACCOUNT/ENVELOPE BALANCES---
        if not t.pending: #Only update balances if transaction is not pending
            apply_transaction(t.account_id, t.envelope_id, t.amt)

    log_write('T INSERT: ' + str(t))

def apply_transaction(a_id, e_id, amt):
    """
    Subtract the amount of the transaction from the envelope and account it is associated with
    """
    if a_id is not None:
        newaccountbalance = get_account_balance(a_id) - amt
        update_account_balance(a_id, newaccountbalance)
    if e_id is not None:
        newenvelopebalance = get_envelope_balance(e_id) - amt
        update_envelope_balance(e_id, newenvelopebalance)

def unapply_transaction(a_id, e_id, amt):
    """
    Add the amount of the transaction from the envelope and account it is associated with
    """
    if a_id is not None:
        newaccountbalance = get_account_balance(a_id) + amt
        update_account_balance(a_id, newaccountbalance)
    if e_id is not None:
        newenvelopebalance = get_envelope_balance(e_id) + amt
        update_envelope_balance(e_id, newenvelopebalance)

def get_transaction(id):
    """
    Retrieves transaction object from database given its ID
    """
    c.execute("SELECT * FROM transactions WHERE id=?", (id,))
    tdata = c.fetchone()
    if tdata is None:
        raise TransactionNotFoundError(f"Transaction with ID {id} not found!")
    t = Transaction(TType.from_int(tdata[1]),tdata[2],tdata[3],tdata[4],tdata[5],tdata[6],tdata[7],tdata[8],tdata[9],tdata[10],tdata[11],tdata[14]) #Last is 14 because e_reconcile and a_reconcile columns exist in table
    t.date = date_parse(t.date) # Convert string to datetime object
    t.id = tdata[0]
    return t

# TODO: When start or amount isn't a valid integer, this should throw an error and not crash because of a bad sqlite3.IntegrityError: datatype mismatch
def get_home_transactions(uuid, start, amount):
    """
    For displaying transactions on the HOME PAGE ONLY
    Given a start number and an amount of transactions to fetch, returns:
    1. A list of transaction objects for display
    2. An offset signifying how many transactions are currently displayed, or where the next start should be.
    3. limit - If this is true, there are no more transactions to fetch
    
    Note: Grouped transactions (Split transactions and envelope fills) displays as a single transaction
    with its summed total
    """
    u = get_user_by_uuid(uuid)
    
    c.execute("SELECT id from TRANSACTIONS WHERE user_id=? GROUP BY grouping ORDER BY day DESC, id DESC LIMIT ? OFFSET ?", (uuid, amount, start))
    groupings = c.fetchall()
    tlist = []
    for id in groupings:
        t = get_transaction(id[0])

        # Set the amount for display
        if t.type == TType.BASIC_TRANSACTION or t.type == TType.INCOME or t.type == TType.ACCOUNT_ADJUST or t.type == TType.ACCOUNT_DELETE:
             t.amt = -1 * t.amt
        elif t.type == TType.ENVELOPE_TRANSFER:
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
        elif t.type == TType.ACCOUNT_TRANSFER:
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
        elif t.type == TType.SPLIT_TRANSACTION:
            c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=?", (t.grouping,))
            t.amt = -1 * c.fetchone()[0] # Total the amount for all the constituent transactions
        elif t.type == TType.ENVELOPE_FILL:
            c.execute("SELECT SUM(amount) FROM transactions WHERE grouping=? AND envelope_id=?", (t.grouping,u.unallocated_e_id))
            t.amt = c.fetchone()[0] # Total the amount for the envelope fill
        
        t.amt = t.amt/100
        tlist.append(t)

    # offset specifies where to start from on the next call
    offset = start + len(tlist)
    # if limit is True you're at the end of the list
    if len(tlist) < amount:
        limit = True
    else:
        limit = False
    return tlist, offset, limit

def get_envelope_transactions(uuid, envelope_id, start, amount):
    """
    For displaying transactions on the ENVELOPE PAGE ONLY
    Given a start number and an amount of transactions to fetch, returns for a particular envelope:
    1. A list of transaction objects for display
    2. An offset signifying how many transactions are currently displayed, or where the next start should be.
    3. limit - If this is true, there are no more transactions to fetch
    
    Note: Grouped transactions (Split transactions and envelope fills) displays as a single transaction
    with its summed total
    """

    # Make sure envelope exists and uuid matches envelope uuid
    c.execute("SELECT user_id FROM envelopes WHERE id=?",(envelope_id,))
    db_uuid = c.fetchone()
    if not db_uuid:
        raise EnvelopeNotFoundError(f"Envelope with ID {envelope_id} not found!")
    if uuid != db_uuid[0]:
        raise UnauthorizedAccessError(f"Provided uuid '{uuid}' does not match requested envelope uuid '{db_uuid}'!")

    c.execute("SELECT id FROM transactions WHERE envelope_id=? ORDER by day DESC, id DESC LIMIT ? OFFSET ?", (envelope_id, amount, start))
    ids = unpack(c.fetchall())
    tlist = []
    for id in ids:
        t = get_transaction(id)
        # For display purposes, the envelope ID displays first, then the account ID in the .transaction-details div
        if t.type == TType.ENVELOPE_TRANSFER:
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

        t.amt = t.amt * -1 / 100
        tlist.append(t)

    # offset specifies where to start from on the next call
    offset = start + len(tlist)
    # if limit is True you're at the end of the list
    if len(tlist) < amount:
        limit = True
    else:
        limit = False
    return tlist, offset, limit

def get_account_transactions(uuid, account_id, start, amount):
    """
    For displaying transactions on the ACCOUNTS PAGE ONLY
    Given a start number and an amount of transactions to fetch, returns for a particular account:
    1. A list of transaction objects for display
    2. An offset signifying how many transactions are currently displayed, or where the next start should be.
    3. limit - If this is true, there are no more transactions to fetch
    
    Note: Grouped transactions (Split transactions and envelope fills) displays as a single transaction
    with its summed total
    """
    # Make sure account exists and uuid matches account uuid
    c.execute("SELECT user_id FROM accounts WHERE id=?",(account_id,))
    db_uuid = c.fetchone()
    if not db_uuid:
        raise AccountNotFoundError(f"Account with ID {account_id} not found!")
    if uuid != db_uuid[0]:
        raise UnauthorizedAccessError(f"Provided uuid '{uuid}' does not match requested account uuid '{db_uuid}'!")

    c.execute("SELECT id, SUM(amount) FROM transactions WHERE account_id=? GROUP BY grouping ORDER by day DESC, id DESC LIMIT ? OFFSET ?", (account_id,amount,start))
    ids = c.fetchall()
    tlist = []
    for thing in ids:
        t = get_transaction(thing[0])
        if t.type == TType.ACCOUNT_TRANSFER:
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
        t.amt = thing[1] * -1 / 100
        tlist.append(t)
    
    # offset specifies where to start from on the next call
    offset = start + len(tlist)
    # if limit is True you're at the end of the list
    if len(tlist) < amount:
        limit = True
    else:
        limit = False
    return tlist, offset, limit

def delete_transaction(uuid, t_id):
    """
    Deletes transaction and associated grouped transactions and updates appropriate envelope/account balances
    """
    u = get_user_by_uuid(uuid)

    with conn:
        if get_transaction(t_id).user_id != uuid:
            raise UnauthorizedAccessError(f"User with uuid {uuid} does not have permission to delete transaction with id {t_id}")

        # 1. Get all the grouped transactions to delete
        ids = get_grouped_ids_from_id(t_id)
        for id in ids:                
            t = get_transaction(id)
            # 2a. If you're deleting an "ENVELOPE_DELETE" transaction, restore the envelope
            if t.type == TType.ENVELOPE_DELETE:
                if t.envelope_id is not u.unallocated_e_id: # Don't try to restore the unallocated envelope since it can't be deleted
                    if (get_envelope(t.envelope_id).deleted is not False): # Don't try to restore an envelope that is not deleted
                        restore_envelope(t.envelope_id)
            
            # 2b. If you're deleting an "ACCOUNT_DELETE" transaction, restore the account
            if t.type == TType.ACCOUNT_DELETE:
                if (get_account(t.account_id).deleted is not False): # Don't try to restore an account that is not deleted
                    restore_account(t.account_id)

            # 4. If the transaction is not pending, update envelope/account balances
            if not t.pending:
                if t.envelope_id is not None:
                    if bool(get_envelope(t.envelope_id).deleted) is not True:
                        update_envelope_balance(t.envelope_id, get_envelope_balance(t.envelope_id) + t.amt)
                    else:
                        update_envelope_balance(u.unallocated_e_id, get_envelope_balance(u.unallocated_e_id) + t.amt)
                        # When deleting a transaction referencing a deleted envelope, you must also update the amount of the
                        # ENVELOPE_DELETE transactions so the deleted envelope maintains a balance of $0.
                        # i.e. If you delete a $1 transaction in a deleted envelope, the money does not go back into the envelope since it's deleted
                        #      instead, it goes to the unallocated envelope, but now the sum of transactions in your deleted envelopes will not be $0
                        #      unless you change the amount ENVELOPE_DELETE transaction(s) (which drains the deleted envelope balance down to 0).

                        # Step 1. Get both the ID's for the ENVELOPE_DELETE transactions of the deleted envelope referenced by the transaction
                        c.execute("""SELECT id FROM transactions WHERE grouping = (
                                        SELECT grouping FROM transactions WHERE (type=? AND envelope_id=?)
                                    )""", (TType.ENVELOPE_DELETE, t.envelope_id)
                                    )
                        e_delete_ids = unpack(c.fetchall())

                        # Step 2. Get the ENVELOPE_DELETE transactions
                        for e_delete_id in e_delete_ids:
                            e_delete_t = get_transaction(e_delete_id)

                            # Step 3. Change the amount by which you will adjust the transaction amount depending on whether
                            #         it was filling or draining the envelopes in the ENVELOPE_DELETE transaction.
                            if e_delete_t.envelope_id == u.unallocated_e_id:
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
                        update_envelope_balance(u.unallocated_e_id, get_envelope_balance(u.unallocated_e_id) - t.amt)

                        # When deleting a transaction referencing a deleted account, you must also update the amount of the
                        # ACCOUNT_DELETE transactions so the deleted account maintains a balance of $0.
                        # i.e. If you delete a $1 transaction in a deleted account, the money does not go back into the account since it's deleted
                        #      instead, it goes to the unallocated envelope, but now the sum of transactions in your deleted account will not be $0
                        #      unless you change the amount ACCOUNT_DELETE transaction (which drains the deleted account balance down to 0).

                        # Step 1. Get the id of the ACCOUNT_DELETE transaction
                        c.execute("""SELECT id FROM transactions WHERE (type=? AND account_id=?)""", (TType.ACCOUNT_DELETE, t.account_id))
                        a_delete_id = c.fetchone()[0]
                        a_delete_t = get_transaction(a_delete_id)

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
        insert_transaction(Transaction(TType.BASIC_TRANSACTION, t.name, compressed_amts[0], t.date, compressed_e_ids[0], t.account_id, grouping, t.note, t.schedule, t.status, t.user_id, t.pending))
    else:
        for i in range(len(compressed_e_ids)):
            insert_transaction(Transaction(TType.SPLIT_TRANSACTION, t.name, compressed_amts[i], t.date, compressed_e_ids[i], t.account_id, grouping, t.note, t.schedule, t.status, t.user_id, t.pending))

# TODO: When implementing unit testing, test what happens if the timestamp is not in the correct format
def check_pending_transactions(uuid, timestamp):
    """
    Given a timestamp passed in from the user's browser, apply or unapply the pending transactions in the database and set the pending flag accordingly
    """
    with conn:

        # 1. Apply pending transactions that are before the timestamp
        c.execute("SELECT id FROM transactions WHERE pending=1 AND user_id=? AND date(day) <= date(?)",(uuid, timestamp[0:10],)) 
        t_ids = c.fetchall()
        if len(t_ids) != 0:
            for id in t_ids:
                t = get_transaction(id[0])
                apply_transaction(t.account_id, t.envelope_id, t.amt)
                c.execute("UPDATE transactions SET pending=0,schedule=null WHERE id=?",(t.id,))
                
                # 1.1 Create scheduled transactions if the transaction is scheduled
                if (t.schedule is not None):
                    
                    isPending = False
                    next_t = t
                    
                    # Keep creating scheduled transactions until you create one with a date after the timestamp
                    while isPending == False:
                        scheduled_t = create_scheduled_transaction(next_t, date_parse(timestamp), False)
                        isPending = scheduled_t.pending
                        next_t = copy.deepcopy(scheduled_t)
                        if isPending == False:
                            scheduled_t.schedule = None  # Clear out the schedule field if it's not a pending transaction
                        insert_transaction(scheduled_t)
        
        # 2. Unapply pending transactions that are after the timestamp
        c.execute("SELECT id,account_id,envelope_id,amount FROM transactions WHERE pending=0 AND user_id=? AND date(day) > date(?)",(uuid, timestamp[0:10],))
        t_data_list = c.fetchall()
        if len(t_data_list) != 0:
            for (id, a_id, e_id, amt) in t_data_list:
                unapply_transaction(a_id, e_id, amt)
                c.execute("UPDATE transactions SET pending=1 WHERE id=?",(id,))
    
    return None

def create_scheduled_transaction(t, timestamp, should_consider_timestamp):
    """
    Given a transaction, create a new transaction with the same parameters, but with a new date
    """
    nextdate = schedule_date_calc(t.date, t.schedule, timestamp, should_consider_timestamp)
    return Transaction(t.type, t.name, t.amt, nextdate, t.envelope_id, t.account_id, gen_grouping_num(), t.note, t.schedule, t.status, t.user_id, is_pending(nextdate, timestamp))

# endregion TRANSACTION FUNCTIONS

# region ---------------ACCOUNT FUNCTIONS---------------

def insert_account(a):
    """
    Inserts new account and creates "initial account balance" transaction
    """
    u = get_user_by_uuid(a.user_id)
    with conn:
        c.execute("INSERT INTO accounts (name, balance, user_id, display_order) VALUES (?, ?, ?, ?)", (a.name, 0, a.user_id, a.display_order))
    account_id = c.lastrowid
    income_name = 'Initial Account Balance: ' + a.name
    log_write('A INSERT: ' + str(get_account(account_id)))
    insert_transaction(Transaction(TType.INCOME, income_name, -1 * a.balance, datetime.combine(date.today(), datetime.min.time()), u.unallocated_e_id, account_id, gen_grouping_num(), '', None, False, a.user_id, False))

def get_account(id):
    """
    Returns account associated with the given id
    """
    c.execute("SELECT * FROM accounts WHERE id=?", (id,))
    adata = c.fetchone()
    if adata is None:
        raise AccountNotFoundError(f"Account with ID {id} not found!")
    a = Account(*adata)
    return a

def get_user_account_dict(uuid):
    """
    Used for displaying the accounts in the side panel and selects.
    Returns:
    1. A boolean that says whether there are accounts to render
    2. A tuple with a dictionary with keys of account_id and values of account objects.
    """
    c.execute("SELECT id FROM accounts where user_id=? ORDER by display_order ASC, id ASC", (uuid,))
    ids = unpack(c.fetchall())
    a_dict = {}
    active_accounts = False
    for id in ids:
        a = get_account(id)
        a.balance = a.balance/100
        a_dict[id] = a
        if a.deleted == 0:
            active_accounts = True
    return (active_accounts, a_dict)

def get_user_account_order(uuid):
    """
    Used for determining when the account order has changed within the account editor.
    Returns:
    1. A dictionary with keys of account id and values of display order
    """
    with conn:
        c.execute("SELECT id,display_order FROM accounts WHERE (deleted=0 AND user_id=?) ORDER BY id ASC",(uuid,))
        tuple_array = c.fetchall()
        if tuple_array is None:
            raise OtherError(f"ERROR: Account order unable to be retrieved for given uuid: {uuid}") 
        display_dict = dict(tuple_array)
        return display_dict

def delete_account(account_id):
    """
    Deletes an account:
    1. Creates a transaction that zeros account balance (basically a negative income)
    2. Sets account "deleted" flag to true
    3. Sets display_order to NULL
    """
    
    with conn:
        a = get_account(account_id)
        u = get_user_by_uuid(a.user_id)

        # 1. Empty the deleted account
        insert_transaction(Transaction(TType.ACCOUNT_DELETE, f"Deleted account: {a.name}", a.balance, datetime.combine(date.today(), datetime.min.time()), u.unallocated_e_id, a.id, gen_grouping_num(), "", None, 0, a.user_id, False))

        # 2. Mark the account as deleted
        c.execute("UPDATE accounts SET deleted=1 WHERE id=?", (account_id,))
        log_write('A DELETE: ' + str(get_account(account_id)))

        #3. Set the displaly_order to NULL
        c.execute("UPDATE accounts SET display_order=NULL WHERE id=?", (account_id,))

def restore_account(account_id):
    """
    Restores an account by setting its deleted flag to false
    * Does NOT adjust the account balances, since this is done at the transaction level
    """
    with conn:
        a = get_account(account_id)
        c.execute("SELECT MAX(display_order) FROM accounts WHERE user_id=?", (a.user_id,))
        max_disp_order = c.fetchone()[0]
        if max_disp_order is not None:
            new_disp_order = max_disp_order + 1
        else:
            new_disp_order = 0
        c.execute("UPDATE accounts SET deleted=0, display_order=? WHERE id=?",(new_disp_order, account_id))
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
        raise AccountNotFoundError(f"Account with ID {id} not found!")
        
def update_account_balance(id, balance):
    """
    Updates balance of account with given id
    NOTE: This shouldn't be possible as a stand alone action. It should always follow a transaction adjusting the balance.
    """
    with conn:
        c.execute("UPDATE accounts SET balance=? WHERE id=?",(balance, id))

def edit_account(id, new_name, new_balance, new_order, timestamp):
    """
    Updates account balalnce and name, then subtracts the change in balance from the unallocated envelope
    """
    with conn:
        balance_diff = get_account_balance(id) - new_balance
        if balance_diff != 0:
            adjust_account_balance(id, balance_diff, new_name, timestamp)
        c.execute("UPDATE accounts SET name=?, display_order=? WHERE id=?", (new_name, new_order, id))
        log_write('A EDIT: ' + str(get_account(id)))

def edit_accounts(uuid, accounts_to_edit, new_accounts, present_ids, timestamp):
    """
    Compares an old and new list of accounts, then:
    1.  Updates accounts in DB if their fields are different from those in old_accounts
    2.  Adds new accounts not present in old list
    3.  Deletes old accounts not present in new list
    """
    done_something = False
    c.execute("SELECT id FROM accounts WHERE deleted=0 AND user_id=?",(uuid,))
    original_account_ids = unpack(c.fetchall())

    # 1. Updates info for accounts that exist in both lists
    for a in accounts_to_edit:
        edit_account(int(a.id), a.name, a.balance, a.display_order, timestamp)
        done_something = True
    # 2. Adds new accounts not present in old list
    for a in new_accounts:
        insert_account(a)
        done_something = True
    # 3. Deletes old accounts not present in new list
    for id in original_account_ids:
        if not (id in present_ids):
            delete_account(id)
            done_something = True
    if done_something:
        return "Accounts updated!"
    else:
        return "No changes were made"

def account_transfer(name, amount, date, to_account, from_account, note, schedule, user_id, pending):
    """
    Creates one transaction draining an account, and one transaction filling another
    """
    grouping = gen_grouping_num()
    insert_transaction(Transaction(TType.ACCOUNT_TRANSFER, name, -1*amount, date, None, to_account, grouping, note, schedule, False, user_id, pending)) #Fill
    insert_transaction(Transaction(TType.ACCOUNT_TRANSFER, name, amount, date, None, from_account, grouping, note, schedule, False, user_id, pending))  #Empty

def adjust_account_balance(a_id, balance_diff, name, date):
    """
    Creates ACCOUNT_ADJUST transactions for when the user manually sets the account balance in the account editor
    This transfers the difference into the unallocated envelope.
    The name input exists so that your ACCOUNT_ADJUST transaction will match the name of the account if you renamed it at the same time
    as adjusting the balance.
    """
    a = get_account(a_id)
    u = get_user_by_uuid(a.user_id)

    # 1. Create the transaction note
    if balance_diff > 0:
        note = f"{balanceformat(balance_diff/100)} was deducted from this account AND the Unallocated envelope."
    else:
        note = f"{balanceformat(-1*balance_diff/100)} was added to this account AND the Unallocated envelope."
    # 2. Add a transaction with an amount that will make the account balance equal to the specied balance
    insert_transaction(Transaction(TType.ACCOUNT_ADJUST, f"{name}: Balance Adjustment", balance_diff, date, u.unallocated_e_id, a_id, gen_grouping_num(), note, None, False, a.user_id, False))

# endregion ACCOUNT FUNCTIONS

# region ---------------ENVELOPE FUNCTIONS---------------

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
    if edata is None:
        raise EnvelopeNotFoundError(f"Envelope with ID {id} not found!")
    e = Envelope(*edata)
    return e

def get_user_envelope_dict(uuid):
    """
    Used for displaying the envelopes in the side panel and selects.
    Returns:
    1. A boolean that says whether there are envelopes to render
    2. A tuple with a dictionary with keys of envelope_id and values of envelope objects.
    3. A string displaying the total budget for all envelopes
    """
    u = get_user_by_uuid(uuid)
    c.execute("SELECT id FROM envelopes WHERE user_id=? ORDER by display_order ASC, id ASC", (uuid,))
    ids = unpack(c.fetchall())
    e_dict = {}
    active_envelopes = False
    budget_total = 0
    for id in ids:
        e = get_envelope(id)
        e.balance = e.balance/100
        e.budget = e.budget/100
        e_dict[id] = e
        if e.deleted == 0 and e.id != u.unallocated_e_id:
            active_envelopes = True
            budget_total = budget_total + e.budget
    return (active_envelopes, e_dict, budget_total)

def get_user_envelope_order(uuid):
    """
    Used for determining when the envelope order has changed within the envelope editor.
    Returns:
    1. A dictionary with keys of envelope id and values of display order
    """
    with conn:
        u = get_user_by_uuid(uuid)
        c.execute("SELECT id,display_order FROM envelopes WHERE (deleted=0 AND user_id=? AND id!=?) ORDER BY id ASC", (uuid, u.unallocated_e_id,))
        tuple_array = c.fetchall()
        if tuple_array is None:
            raise OtherError(f"ERROR: Envelope order unable to be retrieved for given uuid: {uuid}") 
        display_dict = dict(tuple_array)
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
        e = get_envelope(envelope_id)
        u = get_user_by_uuid(e.user_id)
        if (envelope_id != u.unallocated_e_id): #You can't delete the unallocated envelope
            
            grouping = gen_grouping_num()

            # 1. Empty the deleted envelope
            insert_transaction(Transaction(TType.ENVELOPE_DELETE,f"Deleted envelope: {e.name}", e.balance, datetime.combine(date.today(), datetime.min.time()), envelope_id, None, grouping, "", None, 0, e.user_id, False))

            # 2. Fill the unallocated envelope
            insert_transaction(Transaction(TType.ENVELOPE_DELETE,f"Deleted envelope: {e.name}", -1*e.balance, datetime.combine(date.today(), datetime.min.time()), u.unallocated_e_id, None, grouping, "", None, 0, e.user_id, False))

            # 3. Mark the envelope as deleted
            c.execute("UPDATE envelopes SET deleted=1 WHERE id=?", (envelope_id,))
            log_write('E DELETE: ' + str(get_envelope(envelope_id)))

            # 4. Set display_order of deleted envelope to NULL
            c.execute("UPDATE envelopes SET display_order=NULL WHERE id=?", (envelope_id,))
        else:
            raise OtherError(f"ERROR: User {u.uuid} tried to delete unallocated envelope with id {envelope_id}")

def restore_envelope(envelope_id):
    """
    Restores an envelope by setting its deleted flag to false
    * Does NOT adjust the envelope balances, since this is done at the transaction level
    """
    e = get_envelope(envelope_id)
    with conn:
        c.execute("SELECT MAX(display_order) FROM envelopes WHERE user_id=?", (e.user_id,))
        max_disp_order = c.fetchone()[0]
        if max_disp_order is not None:
            new_disp_order = max_disp_order + 1
        else:
            new_disp_order = 0
        c.execute("UPDATE envelopes SET deleted=0, display_order=? WHERE id=?",(new_disp_order, envelope_id))
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
        raise EnvelopeNotFoundError(f"Envelope with ID {id} not found!")

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

def edit_envelopes(uuid, envelopes_to_edit, new_envelopes, present_ids):
    """
    Inputs:
    1.  envelopes_to_edit: A list of envelope objects that have different names, budgets, or orders than what is stored in the database
    2.  new_envelopes: A lit of brand new envelope objects to be inserted into the database
    3.  present_ids: A list of all id's present in the envelope editor modal (notably missing any that were deleted by the user)
    """
    u = get_user_by_uuid(uuid) 
    done_something = False
    c.execute("SELECT id FROM envelopes WHERE deleted=0 AND user_id=?",(uuid,))
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
        if not id in present_ids and id != u.unallocated_e_id:
            delete_envelope(id)
            done_something = True
    if done_something:
        return "Envelopes updated!"
    else:
        return "No changes were made"

def envelope_transfer(name, amt, date, to_envelope, from_envelope, note, schedule, user_id, pending):
    """
    Creates a transaction to fill one envelope and another to empty the other
    """
    grouping = gen_grouping_num()
    insert_transaction(Transaction(TType.ENVELOPE_TRANSFER, name, -1*amt, date, to_envelope, None, grouping, note, schedule, False, user_id, pending)) #Fill
    insert_transaction(Transaction(TType.ENVELOPE_TRANSFER, name, amt, date, from_envelope, None, grouping, note, schedule, False, user_id, pending))  #Empty

def envelope_fill(t):
    """
    Takes an ENVELOPE_FILL transaction with an array of envelope ids and amounts and creates sub-transactions to fill the envelopes
    """
    u = get_user_by_uuid(t.user_id)
    if t.type == TType.ENVELOPE_FILL:
        grouping = gen_grouping_num()
        amts = t.amt
        envelopes = t.envelope_id
        for i in range(len(amts)):
            # Empty the unallocated envelope
            insert_transaction(Transaction(TType.ENVELOPE_FILL, t.name, amts[i], t.date, u.unallocated_e_id, None, grouping, t.note, t.schedule, False, t.user_id, t.pending))
            # Fill the other envelopes
            insert_transaction(Transaction(TType.ENVELOPE_FILL, t.name, amts[i] * -1, t.date, envelopes[i], None, grouping, t.note, t.schedule, False, t.user_id, t.pending))
    else:
        raise OtherError(f"ERROR: Transaction type mismatch. Expected TType.ENVELOPE_FILL, got {t.type}")

# endregion ENVELOPE FUNCTIONS

# region ---------------USER FUNCTIONS---------------
def get_user_by_email(email):
    """
    Given an email address, return a User object if the email is in the database, or return none if not
    """
    with conn:
        c.execute("SELECT * FROM users WHERE email=?",(email,))
        u = c.fetchone()
        if u is not None:
            user = User(*u)
            user.confirmed = bool(user.confirmed)
            return user
        else:
            return None
    
def get_user_for_flask(uuid):
    """
    Given a uuid, return a User object if the uuid is in the database, or return None if not
    Note: Must return None, and not throw an exception
    """
    conn = sqlite3.connect(database, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE uuid=?",(uuid,))
    u = c.fetchone()
    c.close()
    if u is not None:
        user = User(*u)
        user.confirmed = bool(user.confirmed)
        return user
    else:
        return None

def get_user_by_uuid(uuid):
    """
    Given a uuid address, return a User object if the uuid is in the database, or return none if not
    """
    c.execute("SELECT * FROM users WHERE uuid=?",(uuid,))
    udata = c.fetchone()
    if udata is not None:
        user = User(*udata)
        user.confirmed = bool(user.confirmed)
        return user
    else:
        raise UserNotFoundError(f"No user exists with uuid {uuid}")

def insert_user(u):
    with conn:
        # 1. Create a new unallocated envelope for the user
        insert_envelope(Envelope(None, "Unallocated", 0, 0, False, u.id, 0))

        # 2. Insert the new user into the database referencing the ID of the newly created unallocated envelope
        c.execute("INSERT INTO users (uuid, email, password_hash, password_salt, first_name, last_name, registered_on, unallocated_e_id) VALUES (?,?,?,?,?,?,?, (SELECT id FROM envelopes WHERE user_id=? LIMIT 1))", (u.id, u.email, u.password_hash, u.password_salt, u.first_name, u.last_name, u.registered_on, u.id))

def confirm_user(u):
    with conn:
        c.execute("UPDATE users SET confirmed=1, confirmed_on=? WHERE uuid=?", (datetime.now(), u.id))

# TODO: Implement soft and hard user deletes (hard deletes delete all user data, soft deletes sets a deleted flag to true)
def delete_user(uuid):
    with conn:
        c.execute("DELETE FROM users WHERE uuid=?", (uuid,))
        
def update_user(u):
    """
    Given a user, update all the fields in the database to match the user object's fields
    """
    with conn:
        c.execute("UPDATE users SET email=?, password_hash=?, password_salt=?, first_name=?, last_name=?, registered_on=?, unallocated_e_id=? WHERE uuid=?", (u.email, u.password_hash, u.password_salt, u.first_name, u.last_name, u.registered_on, u.unallocated_e_id, u.id))


# endregion USER FUNCTIONS

# region ---------------OTHER FUNCTIONS---------------

def get_total(uuid):
    """
    Sums the account balances for display
    """
    c.execute("SELECT SUM(balance) FROM accounts WHERE user_id=?", (uuid,))
    total = c.fetchone()[0]
    if total is not None:
        return total/100
    else:
        return 0

def gen_grouping_num():
    """
    Returns a new and unique grouping number
    """
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
        raise TransactionNotFoundError(f"ERROR: There is no transaction with this id {t_id}")
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

def get_grouped_json(uuid, t_id):
    """
    Given a transaction id, return a json with the transaction data necessary to fill the transaction editor
    This function is called for displaying ENVELOPE_TRANSFER's, ACCOUNT_TRANSFER's, SPLIT_TRANSACTION's, and ENVELOPE_FILL's
    """
    if get_transaction(t_id).user_id != uuid:
        raise UnauthorizedAccessError(f"ERROR: User {uuid} attempted to get grouped transaction data for id={t_id} which belongs to user {get_transaction(t_id).user_id}.")

    ids = get_grouped_ids_from_id(t_id)
    data = {'transactions': [], 'success': True}
    for id in ids:
        t = get_transaction(id)
        data['transactions'].append({
            'id': t.id,
            'amt': t.amt / 100,
            'envelope_id': t.envelope_id,
            'account_id': t.account_id
        })
    return data

def health_check(toasts, interactive=False):
    """
    1. Compares the sum of all account balances to the sum of all envelope balances
    2. Ensures that all deleted envelopes and accounts have a balance of zero
    3. Checks if stored/displayed account balances equal the sum of their non-pending transactions
    4. Checks if stored/displayed envelope balances equal the sum of their non-pending transactions
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
            c.execute("SELECT SUM(amount) from transactions WHERE account_id=? AND pending=0", (a_id,))
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
            c.execute("SELECT SUM(amount) from transactions WHERE envelope_id=? AND pending=0", (e_id,))
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
            toasts.append("HEALTH ERROR!")
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

# endregion OTHER FUNCTIONS

# region ---------------DEBUGGING FUNCTIONS---------------

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
    c.execute("SELECT * FROM accounts ORDER BY display_order ASC, id ASC")
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
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n")

    print('USERS:')
    c.execute("PRAGMA table_info(users)")
    colnames = ''
    for row in c:
        colnames = colnames + row[1] + ', '
    print("(" + colnames[:-2] + ")\n")
    c.execute("SELECT * FROM users ORDER BY user_id ASC")
    for row in c:
        print(row)
    print()

# endregion DEBUGGING FUNCTIONS

def main():
    print_database()

if __name__ == "__main__":
    main()
