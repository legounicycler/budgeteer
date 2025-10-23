import pytest, re
from datetime import datetime
from flask import url_for
from flask_login import current_user

from budgeteer import create_app
from database import Database, User, confirm_user
from blueprints.auth import generate_uuid, insert_user, login_user

@pytest.fixture
def db():
    # Create the tables for the testing configuration
    db = Database(":memory:")
    db.get_conn()
    db.create_tables()
    yield db
    db.close_conn()

@pytest.fixture
def app(db):
    """Create and configure a new app instance for testing."""
    app = create_app('config.TestingConfig')
    yield app

@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()

# Define a fixture for the context of a logged-in user
@pytest.fixture
def logged_in_user_client(client):
    """
    Creates a fixture for a logged-in user in the Flask application context.

    Parameters:
    - app: The Flask application instance.
    - client: The test client for the Flask application.

    Returns:
    - The test client with a logged-in user in the context.
    """
    
    # 1. Insert a new user to the database
    uuid = generate_uuid()
    (new_password_hash, new_password_salt) = User.hash_password("password")
    new_user = User(uuid, "email@example.com", new_password_hash, new_password_salt, "Firstname", "Lastname", datetime.now())
    insert_user(new_user)

    #2. Simulate a user login
    login_user(new_user)

    # 3. Yield the test client with the logged-in user in the context
    yield client

@pytest.fixture
def confirmed_user_client(client, monkeypatch):
    """
    Logged-in + confirmed user test client.
    - monkeypatches blueprints.main.get_uuid_from_cookie to return the test user's uuid
    - sets the timestamp cookie so /home renders the real page (no client-side JS redirect)
    - fetches /home once and attaches the extracted CSRF token as `client.csrf_token`
    """
    # 1. Insert a new user to the database, then confirm them
    uuid = generate_uuid()
    (new_password_hash, new_password_salt) = User.hash_password("password")
    new_user = User(uuid, "email@example.com", new_password_hash, new_password_salt, "Firstname", "Lastname", datetime.now())
    insert_user(new_user)
    confirm_user(new_user)

    # 2. Log the user in
    login_user(new_user)

    # 3. Monkeypatch get_uuid_from_cookie used by main blueprints to return this user's uuid
    monkeypatch.setattr('blueprints.main.get_uuid_from_cookie', lambda: new_user.id)

    # 4. Set timestamp cookie so the server renders the full /home (the real app sets this via JS)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # test_client requires a domain for set_cookie; 'localhost' works
    client.set_cookie('timestamp', ts)

    # 5. Prime the session / extract CSRF token from the home page and attach to client
    resp = client.get(url_for('main.home'))
    html = resp.get_data(as_text=True)
    match = re.search(r'<input[^>]*id=["\']csrf-token["\'][^>]*value=["\']([^"\']+)["\']', html)
    if match:
        client.csrf_token = match.group(1)

    # 6. Yield the prepared client
    yield client

@pytest.fixture
def mail_instance(app):
    return app.extensions['mail']

@pytest.fixture
def mock_get_uuid_from_cookie_main(mocker):
    return mocker.patch('blueprints.main.get_uuid_from_cookie', return_value=current_user.id)

@pytest.fixture
def mock_get_uuid_from_cookie_error_handling(mocker):
    return mocker.patch('blueprints.error_handling.get_uuid_from_cookie', return_value=current_user.id)

def get_login_csrf_token(client):
    """Get the CSRF token from the login page"""
    response = client.get(url_for('auth.login'))
    html = response.get_data(as_text=True)
    match = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="([^"]+)">', html)
    if match:
        csrf_token = match.group(1)
        return csrf_token
    else:
        raise ValueError("CSRF token not found in the login page")
    
def get_home_csrf_token(client):
    """Get the CSRF token from the home page"""
    # 1. Set the expected cookies needed to load the home page
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client.set_cookie('timestamp', ts)

    #2. Get the CSRF token from the home page
    response = client.get(url_for('main.home'))
    html = response.get_data(as_text=True)
    match = re.search(r'<input id="csrf-token" name="csrf_token" type="hidden" value="([^"]+)">', html)
    if match:
        csrf_token = match.group(1)
        return csrf_token
    else:
        raise ValueError("CSRF token not found in the home page")