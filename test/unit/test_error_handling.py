import io
from conftest import get_csrf_token

def test_bug_report_send_success(confirmed_user_client, mail_instance):
    """
    Test POSTing data to the bug report form with a valid name, email address, description, and screenshot
    The site should return success:true
    """
    with mail_instance.record_messages() as outbox:

        # 1. POST with valid data
        response = confirmed_user_client.post('/bug-report', data={
            'bug_reporter_name': 'Firstname Lastname',
            'bug_reporter_email': 'email@example.com',
            'bug_description': 'This is the bug description!!',
            'screenshot': (io.BytesIO(b'my file contents'), 'test_file.png'),
            'csrf_token': confirmed_user_client.csrf_token
        }, content_type='multipart/form-data')

        # 2. Verify the response
        assert response.status_code == 200
        assert b'{"success":true,"toasts":["Bug report successfully submitted. Thank you for helping to improve Budgeteer!"]}\n' in response.data
        assert len(outbox) == 2
        assert outbox[0].subject == 'Budgeteer: Bug Report from email@example.com'
        assert outbox[1].subject == 'Budgeteer: Your Bug Report Has Been Received'

def test_bug_report_send_non_logged_in_user(client, mail_instance):
    """
    Test POSTing data to the bug report form with a valid name, email address, description, and screenshot
    The site should return success:true
    """
    with mail_instance.record_messages() as outbox:

        # 0. Get CSRF token for non-logged-in user
        csrf_token = get_csrf_token(client)

        # 1. POST with valid data
        response = client.post('/bug-report', data={
                'bug_reporter_name': 'Firstname Lastname',
                'bug_reporter_email': 'email@example.com',
                'bug_description': 'This is the bug description!!',
                'screenshot': (io.BytesIO(b'my file contents'), 'test_file.png'),
                'csrf_token': csrf_token
            },
            content_type='multipart/form-data',
            follow_redirects=False
        )

        # 2. Verify the response
        assert response.status_code == 302 # Redirect to login page
        assert 'login' in response.headers.get('Location', '')
        assert len(outbox) == 0 # No emails should be sent

def test_bug_report_success_no_screenshot(confirmed_user_client, mail_instance):
    """
    Test POSTing data to the bug report form with a valid name, email address, description, and no screenshot
    """
    with mail_instance.record_messages() as outbox:

        # 1. POST with valid data
        response = confirmed_user_client.post('/bug-report', data={
            'bug_reporter_name': 'Firstname Lastname',
            'bug_reporter_email': 'email@example.com',
            'bug_description': 'This is the bug description!!',
            'csrf_token': confirmed_user_client.csrf_token
        }, content_type='multipart/form-data')

        # 2. Verify the response
        assert response.status_code == 200
        assert b'"success":true' in response.data
        assert len(outbox) == 2
        assert outbox[0].subject == 'Budgeteer: Bug Report from email@example.com'
        assert outbox[1].subject == 'Budgeteer: Your Bug Report Has Been Received'

def test_bug_report_send_failure_malformed_textual_data(confirmed_user_client):
    """
    Test cases for bad/empty name, bad/empty email, bad/empty description
    """

    # 1. POST with missing name
    response = confirmed_user_client.post('/bug-report', data={'bug_reporter_email': 'email@example.com', 'bug_description': 'Description...', 'csrf_token': confirmed_user_client.csrf_token}, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'{"errors":{"bug_reporter_name":["This field is required."]},"success":false}' in response.data

    # 2. POST with missing email
    response = confirmed_user_client.post('/bug-report', data={'bug_reporter_name': 'Name', 'bug_description': 'Description...', 'csrf_token': confirmed_user_client.csrf_token}, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'{"errors":{"bug_reporter_email":["This field is required."]},"success":false}' in response.data

    # 3. POST with missing description
    response = confirmed_user_client.post('/bug-report', data={'bug_reporter_name': 'Name', 'bug_reporter_email': 'email@example.com', 'csrf_token': confirmed_user_client.csrf_token}, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'{"errors":{"bug_description":["This field is required."]},"success":false}' in response.data

    # 4. Post with invalid name (too long)
    response = confirmed_user_client.post('/bug-report', data={'bug_reporter_name': "a" * 301, 'bug_reporter_email': 'email@example.com', 'bug_description': 'Description...', 'csrf_token': confirmed_user_client.csrf_token}, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'{"errors":{"bug_reporter_name":["Field must be between 1 and 300 characters long."]},"success":false}' in response.data

    # 5. POST with invalid email
    response = confirmed_user_client.post('/bug-report', data={'bug_reporter_name': 'Name', 'bug_reporter_email': 'notanemail', 'bug_description': 'Description...', 'csrf_token': confirmed_user_client.csrf_token}, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'{"errors":{"bug_reporter_email":["Invalid email address."]},"success":false}' in response.data

    # 6. POST with invalid description (too long)
    response = confirmed_user_client.post('/bug-report', data={'bug_reporter_name': 'Name', 'bug_reporter_email': 'email@example.com', 'bug_description': 'a' * 10001, 'csrf_token': confirmed_user_client.csrf_token}, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b'{"errors":{"bug_description":["Field must be between 1 and 10000 characters long."]},"success":false}' in response.data

def test_bug_report_send_failure_invalid_filetype(confirmed_user_client):
    """
    Test case for when a user submits non-image filetypes
    """

    # 1. POST with invalid file type
    response = confirmed_user_client.post('/bug-report', data={
        'bug_reporter_name': 'Firstname Lastname',
        'bug_reporter_email': 'email@example.com',
        'bug_description': 'This is the bug description!!',
        'screenshot': (io.BytesIO(b'my file contents'), 'test_file.csv'),
        'csrf_token': confirmed_user_client.csrf_token
    }, content_type='multipart/form-data')
    
    # 2. Verify the response
    assert response.status_code == 200
    assert b'{"errors":{"screenshot":["Must be image file"],"screenshot_filepath":["Must be image file"]},"success":false}' in response.data

def test_bug_report_send_failure_invalid_filesize(confirmed_user_client):
    """
    Test case for when a user submits files that are too large
    """

    # 1. POST with invalid file type
    response = confirmed_user_client.post('/bug-report', data={
        'bug_reporter_name': 'Firstname Lastname',
        'bug_reporter_email': 'email@example.com',
        'bug_description': 'This is the bug description!!',
        'screenshot': (io.BytesIO(b'a' * (10 * 1024 * 1024)), 'test_file.png'),
        'csrf_token': confirmed_user_client.csrf_token
    }, content_type='multipart/form-data')
    
    # 2. Verify the response
    assert response.status_code == 200
    assert b'{"errors":{"screenshot_filepath":["File size too large! (10.0Mb). Max size 10.0Mb."]},"success":false}' in response.data