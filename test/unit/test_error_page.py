import pytest, io
from test.unit.conftest import get_csrf_token
from flask_login import current_user
from blueprints.auth import confirm_user

@pytest.fixture
def mock_get_uuid_from_cookie(mocker):
    return mocker.patch('blueprints.main.get_uuid_from_cookie', return_value=current_user.id)

# TODO: Move this to conftest since it's also used in auth.py
@pytest.fixture
def mail_instance(app):
    return app.mail

def test_bug_report_send_success(logged_in_user_client, mock_get_uuid_from_cookie, mail_instance):
    """
    Test POSTing data to the bug report form with a valid name, email address, description, and screenshot
    The site should return success:true
    """
    with mail_instance.record_messages() as outbox:
        # 0. Get the CSRF token
        csrf_token = get_csrf_token(logged_in_user_client)
        confirm_user(current_user)

        # 1. POST with valid data
        response = logged_in_user_client.post('/bug-report', data={
            'bug_reporter_name': 'Firstname Lastname',
            'bug_reporter_email': 'email@example.com',
            'bug_description': 'This is the bug description!!',
            'screenshot': (io.BytesIO(b'my file contents'), 'test_file.png'),
            'csrf_token': csrf_token
        }, content_type='multipart/form-data')

        # 2. Verify the response
        assert response.status_code == 200
        assert b'"success":true' in response.data
        assert len(outbox) == 2
        assert outbox[0].subject == 'Budgeteer: Bug Report from email@example.com'
        assert outbox[1].subject == 'Budgeteer: Your Bug Report Has Been Received'
