import os, sys, pytest
project_directory = os.path.abspath('../..')
sys.path.append(project_directory)
from database import *
import sqlite3


# region ---------------TRANSACTION FUNCTIONS TESTS---------------

def test_insert_transaction():
    # Test a valid transaction insertion
    t = Transaction(TType.BASIC_TRANSACTION, "Test Transaction", 100, datetime.now(), 1, 1, "Grouping", "Note", False, "status", "user_id", False)
    
    # Create an in-memory database with the same structure as the main database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, type TEXT, name TEXT, amount REAL, date TEXT, envelope_id INTEGER, account_id INTEGER, grouping TEXT, note TEXT, reconciled INTEGER, status TEXT, user_id TEXT, deleted INTEGER)")
    
    # Insert the transaction into the in-memory database
    insert_transaction(t, conn)
    
    # Read the in-memory database to check if the inserted transaction is present
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (t.id,))
    result = cursor.fetchone()
    
    # Assert that the transaction was inserted successfully
    assert result is not None, "Inserted transaction not found in the database"
    
    # Clean up the inserted transaction
    delete_transaction("user_id", t.id, conn)

def test_apply_transaction():
    # Test case for apply_transaction function
    pass

def test_unapply_transaction():
    # Test case for unapply_transaction function
    pass

def test_get_transaction():
    # Test case for get_transaction function
    pass

def test_get_home_transactions():
    # Test case for get_home_transactions function
    pass

def test_get_envelope_transactions():
    # Test case for get_envelope_transactions function
    pass

def test_get_account_transactions():
    # Test case for get_account_transactions function
    pass

def test_delete_transaction():
    # Test case for delete_transaction function
    pass

def test_new_split_transaction():
    # Test case for new_split_transaction function
    pass

def test_check_pending_transactions():
    # Test case for check_pending_transactions function
    pass

def test_generate_scheduled_transaction():
    # Test case for generate_scheduled_transaction function
    pass

# endregion TRANSACTION FUNCTIONS TESTS

# region ---------------ACCOUNT FUNCTIONS TESTS---------------

def test_insert_account():
    # Test case for insert_account function
    pass

def test_get_account():
    # Test case for get_account function
    pass

def test_get_user_account_dict():
    # Test case for get_user_account_dict function
    pass

def test_get_user_account_order():
    # Test case for get_user_account_order function
    pass

def test_delete_account():
    # Test case for delete_account function
    pass

def test_restore_account():
    # Test case for restore_account function
    pass

def test_get_account_balance():
    # Test case for get_account_balance function
    pass

def test_update_account_balance():
    # Test case for update_account_balance function
    pass

def test_edit_account():
    # Test case for edit_account function
    pass

def test_edit_accounts():
    # Test case for edit_accounts function
    pass

def test_account_transfer():
    # Test case for account_transfer function
    pass

def test_adjust_account_balance():
    # Test case for adjust_account_balance function
    pass

# endregion ACCOUNT FUNCTIONS TESTS

# region ---------------ENVELOPE FUNCTIONS TESTS---------------

def test_insert_envelope():
    # Test case for insert_envelope function
    pass

def test_get_envelope():
    # Test case for get_envelope function
    pass

def test_get_user_envelope_dict():
    # Test case for get_user_envelope_dict function
    pass

def test_get_user_envelope_order():
    # Test case for get_user_envelope_order function
    pass

def test_delete_envelope():
    # Test case for delete_envelope function
    pass

def test_restore_envelope():
    # Test case for restore_envelope function
    pass

def test_get_envelope_balance():
    # Test case for get_envelope_balance function
    pass

def test_update_envelope_balance():
    # Test case for update_envelope_balance function
    pass

def test_edit_envelope():
    # Test case for edit_envelope function
    pass

def test_edit_envelopes():
    # Test case for edit_envelopes function
    pass

def test_envelope_transfer():
    # Test case for envelope_transfer function
    pass

def test_envelope_fill():
    # Test case for envelope_fill function
    pass

# endregion ENVELOPE FUNCTIONS TESTS

# region ---------------USER FUNCTIONS TESTS---------------

def test_get_user_by_email():
    # Test case for get_user_by_email function
    pass

def test_get_user_for_flask():
    # Test case for get_user_for_flask function
    pass

def test_get_user_by_uuid():
    # Test case for get_user_by_uuid function
    pass

def test_insert_user():
    # Test case for insert_user function
    pass

def test_confirm_user():
    # Test case for confirm_user function
    pass

def test_delete_user():
    # Test case for delete_user function
    pass

def test_update_user():
    # Test case for update_user function
    pass

# endregion USER FUNCTIONS TESTS

# region ---------------OTHER FUNCTIONS TESTS---------------

def test_get_total():
    # Test case for get_total function
    pass

def test_gen_grouping_num():
    # Test case for gen_grouping_num function
    pass

def test_get_grouping_from_id():
    # Test case for get_grouping_from_id function
    pass

def test_get_ids_from_grouping():
    # Test case for get_ids_from_grouping function
    pass

def test_get_grouped_ids_from_id():
    # Test case for get_grouped_ids_from_id function
    pass

def test_get_grouped_json():
    # Test case for get_grouped_json function
    pass

def test_health_check():
    # Test case for health_check function
    pass

# endregion OTHER FUNCTIONS TESTS

# region ---------------DEBUGGING FUNCTIONS TESTS---------------

def test_print_database():
    # Test case for print_database function
    pass

# endregion DEBUGGING FUNCTIONS TESTS
