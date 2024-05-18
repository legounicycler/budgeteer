import pytest, re

from flask import url_for
from flask_login import current_user
from unittest.mock import patch

from budgeteer import create_app
from blueprints.auth import *
from database import User
from secret import RECAPTCHA_SITE_KEY

def get_csrf_token(client):
    response = client.get(url_for('auth.login'))
    html = response.get_data(as_text=True)
    match = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="([^"]+)">', html)
    if match:
        csrf_token = match.group(1)
        return csrf_token
    else:
        raise ValueError("CSRF token not found in the login page")

# Mock the reCAPTCHA validation to always return True
def mock_verify_recaptcha(response):
    return {'score': 0.9}

@pytest.fixture
def app():
    """Create and configure a new instance of the Flask application for testing."""
    app = create_app('config.TestingConfig')
    return app

@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()

# Define a fixture for the context of a logged-in user
@pytest.fixture
def logged_in_user_client(app, client):
    """
    Creates a fixture for a logged-in user in the Flask application context.

    Parameters:
    - app: The Flask application instance.
    - client: The test client for the Flask application.

    Returns:
    - The test client with a logged-in user in the context.
    """
    with app.app_context():
        # 1. Create a user that is verified
        uuid = generate_uuid()
        (new_password_hash, new_password_salt) = User.hash_password("password")
        new_user = User(uuid, "email@example.com", new_password_hash, new_password_salt, "Firstname", "Lastname", datetime.now())
        insert_user(new_user)

        #2. Simulate a user login
        login_user(new_user)

        # 3. Return the test client with the logged-in user in the context
        return client

def test_login_get(client):
    """Test loading the login route."""
    response = client.get('/login')
    assert response.status_code == 200

    # Check that the response contains the expected forms
    assert b'<form id="login-form"' in response.data
    assert b'<form id="register-form"' in response.data
    assert b'<form id="forgot-password-form"' in response.data

    # Check that the reCAPTCHA site key is included
    assert RECAPTCHA_SITE_KEY.encode() in response.data

def test_login_authenticated_user(logged_in_user_client):
    """
    Test the login route when the user is already authenticated and confirmed.
    The user should be redirected to the home page
    """
    # Simulate a logged-in and confirmed user
    confirm_user(current_user)
    
    # Request the login page
    response = logged_in_user_client.get('/login')
    
    # Verify the response redirects to the home page for a user that's already logged in
    assert response.status_code == 302
    assert response.location == "/home"

@patch('blueprints.auth.verify_recaptcha', mock_verify_recaptcha)
def test_login_nonexistent_user(client):
    """
    Test the login route when the user doesn't exist.
    The user should be redirected to the login page
    """
    csrf_token = get_csrf_token(client)
    response = client.post(
        '/api/login',
        data={
            'email': 'idontexist@example.com',
            'password': 'password',
            'csrf_token': csrf_token,
            'g-recaptcha-response': 'dummy-response'
            },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'No user with that email exists!' in response.data

# def test_login_unauthenticated_user(logged_in_user_client):
#     """
#     Test the login route when the user is not authenticated or confirmed.
#     The user should ... be directed to the confirm page? Receive a toast? I don't remember
#     """
#     csrf_token = get_csrf_token(logged_in_user_client)
#     response = logged_in_user_client.post('/api/login', data={'email': 'email@example.com', 'password': 'password', 'csrf_token': csrf_token})

#     assert response.status_code == 200
#     assert response.location == "/confirm"
    

def test_nonexistent_route(client):
    """Test a POST request to a route that doesn't exist"""
    response = client.post('/nonexistentroute', data={'key': 'value'})
    assert response.status_code == 404

    # Check that the response brings up the error page
    assert b"<h5>You've encountered the following error:</h5>" in response.data