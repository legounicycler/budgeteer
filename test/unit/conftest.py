import pytest
from budgeteer import create_app
from database import Database

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