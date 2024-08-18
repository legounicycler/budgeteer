import pytest, re
from datetime import datetime
from flask import url_for

from budgeteer import create_app
from database import Database, User
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


# @pytest.fixture
# def app_with_context(app):
#     """Create and configure a new app instance for testing."""
#     with app.app_context():
#         yield app


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

def get_csrf_token(client):
    """Get the CSRF token from the login page"""
    response = client.get(url_for('auth.login'))
    html = response.get_data(as_text=True)
    match = re.search(r'<input id="csrf_token" name="csrf_token" type="hidden" value="([^"]+)">', html)
    if match:
        csrf_token = match.group(1)
        return csrf_token
    else:
        raise ValueError("CSRF token not found in the login page")