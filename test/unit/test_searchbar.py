from time import time

from flask_login import current_user

from blueprints.main import *
from database import Transaction, Account, Envelope, TType, gen_grouping_num
from datetime import datetime, timedelta

# region INVALID SEARCH DATA TESTS
# Invalid data
  # Amount too big
  # Amount not a number
  # amount min > amount max
  # Date invalid format
  # Date min > date max
  # Non-existent envelope ID
  # Non-existent account ID
  # Non-existent transaction type
  # Empty data?

def test_search_transactions_amount_too_big(confirmed_user_client):
    # Amount far too large should be rejected as invalid input
    response = confirmed_user_client.post(
        '/api/load-search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '100000000000000000000.00',  # unrealistic huge value
            'search_amt_max': '',
            'search_date_min': '',
            'search_date_max': '',
            'timestamp': str(time())
        }
    )
    assert response.status_code == 200

    json_data = response.get_json()
    assert 'field_errors' in json_data
    assert 'search_amt_min' in json_data['field_errors']
    assert any("Number too large" in msg for msg in json_data['field_errors']['search_amt_min'])

def test_search_transactions_amount_not_number(confirmed_user_client):
    response = confirmed_user_client.post(
        '/api/load-search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': 'not-a-number',
            'search_amt_max': '',
            'search_date_min': '',
            'search_date_max': '',
            'timestamp': str(time())
        }
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'field_errors' in json_data
    assert 'search_amt_min' in json_data['field_errors']
    assert any("Invalid number format" in msg for msg in json_data['field_errors']['search_amt_min'])

def test_search_transactions_amount_min_greater_than_max(confirmed_user_client):
    response = confirmed_user_client.post(
        '/api/load-search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '1000',
            'search_amt_max': '10',
            'search_date_min': '',
            'search_date_max': '',
            'timestamp': str(time())
        }
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'field_errors' in json_data

    # Both min and max fields should be display an error message
    assert 'search_amt_min' in json_data['field_errors']
    assert 'search_amt_max' in json_data['field_errors']
    assert any("min amt > max amt" in msg for msg in json_data['field_errors']['search_amt_min'])
    assert any("min amt > max amt" in msg for msg in json_data['field_errors']['search_amt_max'])

def test_search_transactions_date_min_greater_than_max(confirmed_user_client):
    response = confirmed_user_client.post(
        '/api/load-search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '',
            'search_amt_max': '',
            'search_date_min': '01/02/2025',
            'search_date_max': '01/01/2025',
            'timestamp': str(time())
        }
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'field_errors' in json_data
    # Both min and max fields should be display an error message
    assert 'search_date_min' in json_data['field_errors']
    assert 'search_date_max' in json_data['field_errors']
    assert any("min date > max date" in msg for msg in json_data['field_errors']['search_date_min'])
    assert any("min date > max date" in msg for msg in json_data['field_errors']['search_date_max'])

def test_search_transactions_nonexistent_envelope_or_account(confirmed_user_client):
    # Use non-existent IDs; API should return 200 and a valid JSON response.
    # TODO: Should this return a field error, or should it just return empty search results?
    response = confirmed_user_client.post(
        '/api/load-search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '',
            'search_amt_max': '',
            'search_date_min': '',
            'search_date_max': '',
            'search_envelope_ids': '999999', # non-existent envelope ID
            'search_account_ids': '999999', # non-existent account ID
            'timestamp': str(time())
        }
    )
    assert response.status_code == 200
    json_data = response.get_json()

    # Should return transactions bin with the empty message
    assert 'transactions_html' in json_data
    assert "No search results found" in json_data['transactions_html']

# endregion INVALID SEARCH DATA TESTS


# region PROPER SEARCH FILTERING TESTS
# Proper filtering
  # By amount min/max
  # By date min/max
  # By envelope ID(s)
  # By account ID(s)
  # By transaction type(s)
  # By search term in title/notes
  # By user ID(s)
  # Combination of everything
  # Search that applies pending transactions

def test_search_transactions_filter_by_amount(confirmed_user_client):
    # 1. Insert account & envelope
    insert_account(Account(None, "My Account", 0, False, current_user.id, 1), datetime.now())
    _, accounts_dict = get_user_account_dict(current_user.id)
    account_id = list(accounts_dict.keys())[0]

    insert_envelope(Envelope(None, "My Envelope", 0, 0, False, current_user.id, 1))
    _, envelopes_dict, _ = get_user_envelope_dict(current_user.id)
    envelope_id = list(envelopes_dict.keys())[0]

    # Insert two transactions: 1000 and 2000
    insert_transaction(Transaction(TType.BASIC_TRANSACTION, "Low transaction name", 1000, datetime.now(), envelope_id, account_id, gen_grouping_num(), "", None, False, current_user.id, False))
    insert_transaction(Transaction(TType.BASIC_TRANSACTION, "Middle transaction name", 2000, datetime.now(), envelope_id, account_id, gen_grouping_num(), "", None, False, current_user.id, False))
    insert_transaction(Transaction(TType.BASIC_TRANSACTION, "High transaction name", 3000, datetime.now(), envelope_id, account_id, gen_grouping_num(), "", None, False, current_user.id, False))

    response = confirmed_user_client.post(
        '/api/load-search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '15.00',
            'search_amt_max': '',
            'search_date_min': '',
            'search_date_max': '',
            'timestamp': str(time())
        }
    )
    assert response.status_code == 200
    json_data = response.get_json()
    
    # Only the transactions with amounts greater than 1500 should be fetched
    assert 'transactions_html' in json_data
    assert "Middle transaction name" in json_data['transactions_html']
    assert "High transaction name" in json_data['transactions_html']
    assert "Low transaction name" not in json_data['transactions_html']

    response = confirmed_user_client.post(
        '/api/load-search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '',
            'search_amt_max': '25.00',
            'search_date_min': '',
            'search_date_max': '',
            'timestamp': str(time())
        }
    )
    assert response.status_code == 200
    json_data = response.get_json()
    
    # Only the transactions with amounts less than 2500 should be fetched
    assert 'transactions_html' in json_data
    assert "Low transaction name" in json_data['transactions_html']
    assert "Middle transaction name" in json_data['transactions_html']
    assert "High transaction name" not in json_data['transactions_html']

def test_search_transactions_filter_by_date(confirmed_user_client):
    # 1. Insert account & envelope
    insert_account(Account(None, "DateFilter Account", 0, False, current_user.id, 1), datetime.now())
    _, accounts_dict = get_user_account_dict(current_user.id)
    account_id = list(accounts_dict.keys())[0]

    insert_envelope(Envelope(None, "DateFilter Envelope", 0, 0, False, current_user.id, 1))
    _, envelopes_dict, _ = get_user_envelope_dict(current_user.id)
    envelope_id = list(envelopes_dict.keys())[0]

    # 2. Insert two transactions: one yesterday, one today
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()
    insert_transaction(Transaction(TType.BASIC_TRANSACTION, "Transaction Date Yesterday", 500, yesterday, envelope_id, account_id, gen_grouping_num(), "", None, False, current_user.id, False))
    insert_transaction(Transaction(TType.BASIC_TRANSACTION, "Transaction Date Today", 500, today, envelope_id, account_id, gen_grouping_num(), "", None, False, current_user.id, False))

    response = confirmed_user_client.post(
        '/api/load-search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '',
            'search_amt_max': '',
            'search_date_min': today.strftime("%m/%d/%Y"),
            'search_date_max': '',
            'timestamp': str(time())
        }
    )
    assert response.status_code == 200
    json_data = response.get_json()

    # Only the transaction with the date today should be found
    assert 'transactions_html' in json_data
    assert "Transaction Date Today" in json_data['transactions_html']
    assert "Transaction Date Yesterday" not in json_data['transactions_html']

def test_search_that_applies_pending_transactions(confirmed_user_client):
    """
    Demonstrate that when check_pending_transactions applies a pending transaction during a search
    the database balances are updated and the page response includes the updated envelope/account HTML
    """

    # 1. Insert test account & envelope
    insert_account(Account(None, "My Account", 0, False, current_user.id, 1), datetime.now())
    _, accounts_dict = get_user_account_dict(current_user.id)
    account_id = list(accounts_dict.keys())[0]

    insert_envelope(Envelope(None, "My Envelope", 0, 0, False, current_user.id, 1))

    # 2. Insert a pending INCOME transaction dated in the past so check_pending_transactions will apply it
    past_date = datetime.now() - timedelta(days=1)
    pending_income = Transaction(TType.INCOME, "Pending Income", -1000, past_date, current_user.unallocated_e_id, account_id, gen_grouping_num(), "", None, False, current_user.id, True)
    insert_transaction(pending_income)

    # Sanity: balance before applying should be unchanged
    before_bal = get_account_balance(account_id)
    assert before_bal == 0

    # 3. Call the search endpoint with a timestamp >= the pending transaction date so it gets applied
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = confirmed_user_client.post(
      '/api/load-search-transactions',
      data={
        'csrf_token': confirmed_user_client.csrf_token,
        'search_term': 'income',
        'search_amt_min': '',
        'search_amt_max': '',   
        'search_date_min': '',
        'search_date_max': '',
        'timestamp': ts
      }
    )

    assert response.status_code == 200 # Verify the response returns with 200 OK
    json_data = response.get_json()

    # 4. DB should reflect the applied transaction (balance updated)
    after_bal = get_account_balance(account_id)
    assert after_bal == 1000  # pending INCOME of -1000 should have increased stored balance by 1000

    # 5. But the search response does NOT include the side-panel HTML needed to show the updated balances.
    #    This demonstrates the missing reload: client must separately call /api/data-reload to refresh accounts/envelopes HTML.
    assert 'accounts_html' in json_data
    assert 'envelopes_html' in json_data
    assert 'total' in json_data

# endregion PROPER SEARCH FILTERING TESTS


# region LOAD MORE TESTS
# Load more results (pagination)
  # By envelope ID
  # By amount range


# endregion LOAD MORE TESTS