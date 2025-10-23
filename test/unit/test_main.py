from time import time

from flask import url_for
from flask_login import current_user

from blueprints.main import *
from database import Transaction, Account, Envelope, TType, gen_grouping_num
from forms import TransactionSearchForm
from blueprints.auth import generate_uuid, insert_user, login_user
from datetime import datetime
import re

# region ROUTE TESTS

def test_search_transactions_success(confirmed_user_client):
    """
    Test POSTing valid data to the search transactions API.
    The site should return search results.
    """

    # 1. Insert test data: account, envelope, transaction
    account = Account(None, "Test Account", 10000, False, current_user.id, 1)
    insert_account(account, datetime.now())
    _, accounts_dict = get_user_account_dict(current_user.id)
    account_id = list(accounts_dict.keys())[0]

    envelope = Envelope(None, "Test Envelope", 0, 5000, False, current_user.id, 1)
    insert_envelope(envelope)
    _, envelopes_dict, _ = get_user_envelope_dict(current_user.id)
    envelope_id = list(envelopes_dict.keys())[0]

    transaction = Transaction(TType.BASIC_TRANSACTION, "Test Transaction", 1000, datetime.now(), envelope_id, account_id, gen_grouping_num(), "", None, False, current_user.id, False)
    insert_transaction(transaction)

    # 2. Post data to the search API
    response = confirmed_user_client.post(
        '/api/search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '',
            'search_amt_max': '',
            'search_date_min': '',
            'search_date_max': '',
            'timestamp': str(time())
        }
    )

    # 3. Verify the response
    print(response.data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'current_page' in json_data
    assert json_data['current_page'] == 'Search results'

def test_search_transactions_invalid_form(confirmed_user_client):
    """
    Test POSTing invalid data to the search transactions API.
    The site should return field errors.
    """

    # 1. Post invalid data (e.g., invalid date format)
    response = confirmed_user_client.post(
        '/api/search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': 'invalid',
            'search_amt_max': '',
            'search_date_min': 'invalid-date',
            'search_date_max': '',
            'timestamp': str(time())
        }
    )

    # 2. Verify the response
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'field_errors' in json_data
    assert 'search_amt_min' in json_data['field_errors']

def test_search_applies_pending_transactions_requires_data_reload(confirmed_user_client):
    """
    Demonstrate that when check_pending_transactions applies a pending transaction during a search
    the database balances are updated but the /api/search-transactions response does NOT include
    the accounts/envelopes HTML (i.e. the page-side data that would reflect the new balances).
    """

    # 1. Insert test account + envelope
    account = Account(None, "Pending Account", 0, False, current_user.id, 1)
    insert_account(account, datetime.now())
    _, accounts_dict = get_user_account_dict(current_user.id)
    account_id = list(accounts_dict.keys())[0]

    envelope = Envelope(None, "Pending Envelope", 0, 0, False, current_user.id, 1)
    insert_envelope(envelope)
    _, envelopes_dict, _ = get_user_envelope_dict(current_user.id)
    envelope_id = list(envelopes_dict.keys())[0]

    # 2. Insert a pending INCOME transaction dated in the past so check_pending_transactions will apply it
    past_date = datetime.now() - timedelta(days=1)
    pending_income = Transaction(TType.INCOME, "Pending Income", -1000, past_date, None, account_id, gen_grouping_num(), "", None, False, current_user.id, True)
    insert_transaction(pending_income)

    # Sanity: balance before applying should be unchanged
    before_bal = get_account_balance(account_id)
    assert before_bal == 0

    # 3. Call the search endpoint with a timestamp >= the pending transaction date so it gets applied
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resp = confirmed_user_client.post(
        '/api/search-transactions',
        data={
            'csrf_token': confirmed_user_client.csrf_token,
            'search_term': '',
            'search_amt_min': '',
            'search_amt_max': '',   
            'search_date_min': '',
            'search_date_max': '',
            'timestamp': ts
        }
    )

    assert resp.status_code == 200
    json_data = resp.get_json()

    # 4. DB should reflect the applied transaction (balance updated)
    after_bal = get_account_balance(account_id)
    assert after_bal == 1000  # pending INCOME of -1000 should have increased stored balance by 1000

    # 5. But the search response does NOT include the side-panel HTML needed to show the updated balances.
    #    This demonstrates the missing reload: client must separately call /api/data-reload to refresh accounts/envelopes HTML.
    assert 'accounts_html' not in json_data
    assert 'envelopes_html' not in json_data
    assert 'page_total' not in json_data


# Test search transactions with invalid transaction type
# test if the data is a random string
# test if the data submitted is an integer that does not correspond to any TType

# endregion ROUTE TESTS