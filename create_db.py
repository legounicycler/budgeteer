from database import *
import platform
import sys, os

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/opc/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

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
        e_reconcile_bal INTEGER NOT NULL DEFAULT 0,
        pending BOOLEAN NOT NULL DEFAULT 0
        )
    """)

c.execute("""
    CREATE TABLE accounts (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        balance INTEGER NOT NULL DEFAULT 0,
        deleted BOOLEAN NOT NULL DEFAULT 0,
        user_id INTEGER NOT NULL,
        display_order INTEGER
        )
    """)

c.execute("""
    CREATE TABLE envelopes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        balance INTEGER NOT NULL DEFAULT 0,
        budget INTEGER NOT NULL DEFAULT 0,
        deleted BOOLEAN NOT NULL DEFAULT 0,
        user_id INTEGER NOT NULL,
        display_order INTEGER
        )
    """)

c.execute("""
    CREATE TABLE users (
        uuid TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        unallocated_e_id INTEGER NOT NULL,
        registered_on TEXT NOT NULL,
        confirmed BOOLEAN NOT NULL DEFAULT 0,
        confirmed_on TEXT,
        FOREIGN KEY (unallocated_e_id) REFERENCES envelopes(id)
        )
    """)

c.close()

print("New database has been created!")
log_write('\n\n\nNEW DATABASE HAS BEEN CREATED \n\n\n')