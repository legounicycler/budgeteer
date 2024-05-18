import pytest

from flask import url_for
from flask_login import current_user

from budgeteer import create_app
from blueprints.auth import *
from database import User
from secret import RECAPTCHA_SITE_KEY

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
        print(current_user)

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
    """Test the login route when the user is already authenticated and confirmed."""
    # Simulate a logged-in and confirmed user
    print(current_user)
    confirm_user(current_user)
    print(current_user)
    
    # Request the login page
    response = logged_in_user_client.get('/login')
    
    # Verify the response redirects to the home page for a user that's already logged in
    assert response.status_code == 302
    assert response.location == "/home"

def test_nonexistent_route(client):
    """Test a POST request to a route that doesn't exist"""
    response = client.post('/nonexistentroute', data={'key': 'value'})
    assert response.status_code == 404

    # Check that the response brings up the error page
    assert b"<h5>You've encountered the following error:</h5>" in response.data