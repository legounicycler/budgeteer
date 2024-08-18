import pytest
from test.unit.conftest import get_csrf_token
from flask_login import current_user
from blueprints.auth import confirm_user


def test_bug_report_send_success(logged_in_user_client):
    """
    Test POSTing data to the bug report form with a valid name, email address, description, and screenshot
    The site should return success:true
    """

    # 0. Get the CSRF token
    csrf_token = get_csrf_token(logged_in_user_client)
    confirm_user(current_user)

    # 1. POST with valid data
    response = logged_in_user_client.post('/bug-report', data={'bug_reporter_name': 'Firstname Lastname', 'bug_reporter_email': 'email@example.com', 'bug_description': 'This is the bug description!!', 'screenshot': 'screenshot', 'csrf_token': csrf_token})

    # 2. Verify the response
    print(response.data)
    assert response.status_code == 200
    assert b'"success":true' in response.data
