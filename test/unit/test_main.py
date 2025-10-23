from time import time

from flask import url_for
from flask_login import current_user

from test.unit.conftest import get_csrf_token
from blueprints.main import *
from database import Transaction, Account, Envelope, TType, gen_grouping_num
from forms import TransactionSearchForm
from blueprints.auth import confirm_user, generate_uuid, insert_user, login_user
from datetime import datetime
import re

# region ROUTE TESTS

def test_search_transactions_success(logged_in_user_client):
    """
    Test POSTing valid data to the search transactions API.
    The site should return search results.
    """
    # 0. Confirm the user
    confirm_user(current_user)
    
    # Get the CSRF token from the home page
    response = logged_in_user_client.get('/home')
    html = response.get_data(as_text=True)
    match = re.search(r'<input id="csrf-token" type="hidden" value="([^"]+)">', html)
    if match:
        csrf_token = match.group(1)
    else:
        raise ValueError("CSRF token not found in the home page")

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
    response = logged_in_user_client.post(
        '/api/search-transactions',
        data={
            'csrf_token': csrf_token,
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

# def test_search_transactions_invalid_form(logged_in_user_client):
#     """
#     Test POSTing invalid data to the search transactions API.
#     The site should return field errors.
#     """
#     # 0. Confirm the user
#     confirm_user(current_user)

#     # 1. Post invalid data (e.g., invalid date format)
#     response = logged_in_user_client.post(
#         '/api/search-transactions',
#         data={
#             'search_term': '',
#             'search_amt_min': 'invalid',
#             'search_amt_max': '',
#             'search_date_min': 'invalid-date',
#             'search_date_max': '',
#             'timestamp': str(time())
#         }
#     )

#     # 2. Verify the response
#     assert response.status_code == 200
#     json_data = response.get_json()
#     assert 'field_errors' in json_data
#     assert 'search_amt_min' in json_data['field_errors']

# def test_search_transactions_not_logged_in(client):
#     """
#     Test POSTing to the search transactions API without being logged in.
#     The user should be redirected to the login page.
#     """
#     # 1. Post data without login
#     response = client.post(
#         '/api/search-transactions',
#         data={
#             'search_term': '',
#             'search_amt_min': '',
#             'search_amt_max': '',
#             'search_date_min': '',
#             'search_date_max': '',
#             'timestamp': str(time())
#         }
#     )

#     # 2. Verify the response redirects to login
#     assert response.status_code == 302
#     assert '/login' in response.headers['Location']

# def test_search_transactions_unconfirmed(logged_in_user_client):
#     """
#     Test POSTing to the search transactions API as an unconfirmed user.
#     The user should be redirected to the unconfirmed page.
#     """
#     # 1. Post data as unconfirmed user
#     response = logged_in_user_client.post(
#         '/api/search-transactions',
#         data={
#             'search_term': '',
#             'search_amt_min': '',
#             'search_amt_max': '',
#             'search_date_min': '',
#             'search_date_max': '',
#             'timestamp': str(time())
#         }
#     )

#     # 2. Verify the response redirects to unconfirmed
#     assert response.status_code == 302
#     assert '/unconfirmed' in response.headers['Location']


# Test search transactions with invalid transaction type
# test if the data is a random string
# test if the data submitted is an integer that does not correspond to any TType

# endregion ROUTE TESTS