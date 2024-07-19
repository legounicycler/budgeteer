import pytest, re

from flask import url_for
from flask_login import current_user

from blueprints.auth import *
from database import User
from secret import RECAPTCHA_SITE_KEY

# region HELPERS

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

# Mock the reCAPTCHA validation to always return True
def mock_verify_recaptcha(response):
    return {'score': 0.9}

def remove_key(d, key):
    r = dict(d)
    del r[key]
    return r

def modify_dict(d, key, value):
    r = dict(d)
    r[key] = value
    return r

# endregion HELPERS

# region FIXTURES

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
def mail_instance(app):
    return app.mail

@pytest.fixture
def mock_verify_recaptcha(mocker):
    return mocker.patch('blueprints.auth.verify_recaptcha', return_value=True)

# endregion FIXTURES

# region ROUTE TESTS

def test_email_send(mail_instance):
    with mail_instance.record_messages() as outbox:
        msg = Message(subject="Test email", recipients=['email@example.com'], body="Test email body")
        mail_instance.send(msg)
        assert len(outbox) == 1
        assert outbox[0].subject == 'Test email'
        assert outbox[0].body == 'Test email body'
        assert outbox[0].recipients == ["email@example.com"]

def test_post_to_nonexistent_route(client):
    """
    Test a POST request to a route that doesn't exist.
    You should go to a 404 error page.
    """
    # 1. Send a POST request to a route that doesn't exist
    response = client.post('/nonexistentroute', data={'key': 'value'})

    # 2. Verify the response
    assert response.status_code == 404

    # 3. Verify that the response brings up the 404 error page
    assert b"<h5>You've encountered the following error:</h5>" in response.data

def test_home_get_not_logged_in(client):
    """
    Test loading the home route WITHOUT being authenticated (logged in)
    You should be redirected to the login page.
    """
    # 1. Request the home page
    response = client.get('/home')

    # 2. Verify the response
    assert response.status_code == 302
    assert response.location == "/login?next=%2Fhome"

def test_login_get(client):
    """
    Test loading the login route without being authenticated (logged in) i.e. a random site visitor
    The login page should display.
    """

    # 1. Request the login page
    response = client.get('/login')

    # 2. Verify the response
    assert response.status_code == 200

    # 3. Verify that the response contains the expected forms
    assert b'<form id="login-form"' in response.data
    assert b'<form id="register-form"' in response.data
    assert b'<form id="forgot-password-form"' in response.data

    # 4. Check that the reCAPTCHA site key is included
    assert RECAPTCHA_SITE_KEY.encode() in response.data

def test_login_get_authenticated_and_confirmed_user(logged_in_user_client):
    """
    Test the login route when the user is already authenticated (logged in) AND confirmed.
    The user should be redirected to the home page
    """
    # 0. Manually confirm the user
    confirm_user(current_user)
    
    # 1. Request the login page
    response = logged_in_user_client.get('/login')
    
    # 2. Verify the response redirects to the home page for a user that's already logged in
    assert response.status_code == 302
    assert response.location == "/home"

def test_login_get_authenticated_and_unconfirmed_user(logged_in_user_client):
    """
    Test the login route when the user is authenticated (logged in) but has not confirmed their email address.
    The user should remain on the login page
    """
    # 1. Request the login page
    response = logged_in_user_client.get('/login')
    
    # 2. Verify the response redirects to the email confirmation page for a user that's already logged in
    assert response.status_code == 200

    # 3. Verify that the response contains the expected forms from the login page
    assert b'<form id="login-form"' in response.data
    assert b'<form id="register-form"' in response.data
    assert b'<form id="forgot-password-form"' in response.data

# --Login API tests--

def test_api_login_nonexistent_user(client, mock_verify_recaptcha):
    """
    Test POSTing data to the login form for a user that doesn't exist.
    The user should be redirected to the login page
    """
    # 0. Get the CSRF token from the hidden input on the login page
    csrf_token = get_csrf_token(client)

    # 1. Post data to the login form with an email for a user that doesn't exist
    response = client.post(
        '/api/login',
        data={
            'email': 'idontexist@example.com',
            'password': 'password',
            'csrf_token': csrf_token,
            'g-recaptcha-response': 'dummy-response'
            }
    )

    # 2. Verify the response
    assert response.status_code == 200
    assert b'No user with that email exists!' in response.data

def test_api_login_unconfirmed_user(logged_in_user_client, mock_verify_recaptcha):
    """
    Test POSTing data to the login form for a user that DOES exist but hasn't yet confirmed their email.
    The user should ... be directed to the confirm page? Receive a toast? I don't remember
    """
    # 0. Get the CSRF token from the hidden input on the login page
    csrf_token = get_csrf_token(logged_in_user_client)

    # 1. Post data to the login form with an email for a user that doesn't exist
    response = logged_in_user_client.post(
        '/api/login',
        data={
            'email': 'email@example.com',
            'password': 'password',
            'csrf_token': csrf_token,
            'g-recaptcha-response': 'dummy-response'
            }
    )

    # 2. Verify the response redirects to the confirm page
    assert response.status_code == 200
    assert b'"confirmed":false' in response.data

def test_api_login_confirmed_user(logged_in_user_client, mock_verify_recaptcha):
    """
    Test POSTing data to the login form for a user that DOES exists and HAS confirmed their email.
    The user should be redirected to the home page.
    """

    # 0. Get the CSRF token from the hidden input on the login page
    csrf_token = get_csrf_token(logged_in_user_client)

    # 1. Manually confirm the user
    confirm_user(current_user)

    # 2. Post data to the login form with an email for a user that doesn't exist
    response = logged_in_user_client.post(
        '/api/login',
        data={
            'email': current_user.email,
            'password': 'password',
            'csrf_token': csrf_token,
            'g-recaptcha-response': 'dummy-response'
            }
    )

    # 3. Verify the response redirects to the home page (i.e. login_success=true)
    assert response.status_code == 200
    assert b'"login_success":true' in response.data

def test_api_login_malformed_data(client, mock_verify_recaptcha):
    # 0. Get the CSRF token from the hidden input on the login page
    csrf_token = get_csrf_token(client)

    # 1. Post data to the login form with a malformed email address
    response = client.post('/api/login', data={'email': "email@example", 'password': 'password', 'csrf_token': csrf_token,'g-recaptcha-response': 'dummy-response'})
    assert response.status_code == 200
    assert b'"errors":{"email":["Invalid email address."]},"login_success":false' in response.data

    # 2. Post data to the login form with no email
    response = client.post('/api/login', data={'password': 'password', 'csrf_token': csrf_token,'g-recaptcha-response': 'dummy-response'})
    assert response.status_code == 200
    assert b'"errors":{"email":["This field is required."]}' in response.data

    # 3. Post data to the login form with no password
    response = client.post('/api/login', data={'email': 'email@example.com', 'csrf_token': csrf_token,'g-recaptcha-response': 'dummy-response'})
    assert response.status_code == 200
    assert b'"errors":{"password":["This field is required."]}' in response.data

    # 4. Post data to the login form with a malformed password (too long)
    response = client.post('/api/login', data={'email': 'email@example.com', 'password': 'asdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdf', 'csrf_token': csrf_token,'g-recaptcha-response': 'dummy-response'})
    assert response.status_code == 200
    assert b'{"errors":{"password":["Password must be between 8 and 32 characters long"]}' in response.data

    # 5. Post data to the login form with a malformed password (too short)
    response = client.post('/api/login', data={'email': 'email@example.com', 'password': 'abc', 'csrf_token': csrf_token,'g-recaptcha-response': 'dummy-response'})
    assert response.status_code == 200
    assert b'{"errors":{"password":["Password must be between 8 and 32 characters long"]}' in response.data

def test_api_login_incorrect_password(client, mock_verify_recaptcha):
    # 0. Get the CSRF token from the hidden input on the login page
    csrf_token = get_csrf_token(client)

    # 1. Insert a new user to the database
    uuid = generate_uuid()
    (new_password_hash, new_password_salt) = User.hash_password("password")
    new_user = User(uuid, "email@example.com", new_password_hash, new_password_salt, "Firstname", "Lastname", datetime.now())
    insert_user(new_user)

    # 1. Post data to the login form with an email for a user that doesn't exist
    response = client.post(
        '/api/login',
        data={
            'email': new_user.email,
            'password': 'incorrectpassword',
            'csrf_token': csrf_token,
            'g-recaptcha-response': 'dummy-response'
            }
    )

    # 2. Verify the response redirects to the home page
    assert response.status_code == 200
    assert b'{"login_success":false,"message":"Incorrect password!"}' in response.data

def test_api_login_bad_recaptcha(client):
    # 0. Get the CSRF token from the hidden input on the login page
    csrf_token = get_csrf_token(client)

    # 1. Post data to the login form with an email for a user that doesn't exist
    response = client.post(
        '/api/login',
        data={
            'email': 'email@example.com',
            'password': 'password',
            'csrf_token': csrf_token,
            'g-recaptcha-response': 'bad-response'
            }
    )

    # 2. Verify the response redirects to the home page
    assert response.status_code == 200
    assert b'{"login_success":false,"message":"Error: An unknown error occurred!"}' in response.data

# --Create account form tests--

def test_create_account_form_success(client, mail_instance, mock_verify_recaptcha):
    with mail_instance.record_messages() as outbox:
    
        # 0. Get the CSRF token from the hidden input on the login page 
        csrf_token = get_csrf_token(client)

        # 1. Post data to the login form with an email for a user that doesn't exist
        response = client.post(
            '/register',
            data={
                'new_first_name': 'firstname',
                'new_last_name': 'lastname',
                'new_email': 'email@example.com',
                'new_password': 'password',
                'confirm_password': 'password',
                'csrf_token': csrf_token,
                'g-recaptcha-response': 'dummy-response'
                }
        )

        # 2. Verify the response
        assert response.status_code == 200
        assert b'{"message":"A confirmation email has been sent to your email address!","register_success":true}' in response.data
        
        # 3. Verify the email was sent properly
        assert len(outbox) == 1
        assert outbox[0].subject == 'Budgeteer: Confirm your email address'
        assert outbox[0].recipients == ["email@example.com"]

def test_create_account_email_already_exists(client, mock_verify_recaptcha):
    # 0. Get the CSRF token from the hidden input on the login page
    csrf_token = get_csrf_token(client)

    # 1. Post data to the login form with an email for a user that doesn't exist yet
    response = client.post(
        '/register',
        data={
            'new_first_name': 'firstname',
            'new_last_name': 'lastname',
            'new_email': 'email@example.com',
            'new_password': 'password',
            'confirm_password': 'password',
            'csrf_token': csrf_token,
            'g-recaptcha-response': 'dummy-response'
            }
    )

    # 2. Post data to the login form with an email for a user that already is registered with the same email
    response = client.post(
        '/register',
        data={
            'new_first_name': 'firstname',
            'new_last_name': 'lastname',
            'new_email': 'email@example.com',
            'new_password': 'password',
            'confirm_password': 'password',
            'csrf_token': csrf_token,
            'g-recaptcha-response': 'dummy-response'
            }
    )

    # 2. Verify the response redirects to the home page
    assert response.status_code == 200
    assert b'{"message":"A user with that email already exists!","register_success":false}' in response.data

def test_create_account_malformed_data(client, mock_verify_recaptcha):
    # 0. Get the CSRF token from the hidden input on the login page
    csrf_token = get_csrf_token(client)

    post_data = {
        'new_first_name': 'firstname',
        'new_last_name': 'lastname',
        'new_email': 'email@example.com',
        'new_password': 'password',
        'confirm_password': 'password',
        'csrf_token': csrf_token,
        'g-recaptcha-response': 'dummy-response'
    }

    # 1. Post data with missing firstname
    response = client.post('/register', data = remove_key(post_data, 'new_first_name'))
    assert response.status_code == 200
    assert b'"errors":{"new_first_name":["This field is required."]},"login_success":false' in response.data

    #2. Post data with missing lastname
    response = client.post('/register', data = remove_key(post_data, 'new_last_name'))
    assert response.status_code == 200
    assert b'"errors":{"new_last_name":["This field is required."]},"login_success":false' in response.data

    #3. Post data with missing email
    response = client.post('/register', data = remove_key(post_data, 'new_email'))
    assert response.status_code == 200
    assert b'"errors":{"new_email":["This field is required."]},"login_success":false' in response.data

    #4. Post data with missing new_password
    response = client.post('/register', data = remove_key(post_data, 'new_password'))
    assert response.status_code == 200
    assert b'"errors":{"confirm_password":["Passwords must match"],"new_password":["This field is required."]},"login_success":false' in response.data

    #5. Post data with missing confirm_password
    response = client.post('/register', data = remove_key(post_data, 'confirm_password'))
    assert response.status_code == 200
    assert b'"errors":{"confirm_password":["This field is required."],"new_password":["Passwords must match"]},"login_success":false' in response.data

    #6. Post data with too long firstname
    response = client.post('/register', data = modify_dict(post_data, "new_first_name", "a" * 51))
    assert response.status_code == 200
    assert b'"errors":{"new_first_name":["Field must be between 2 and 50 characters long."]},"login_success":false' in response.data

    #7. Post data with too short firstname
    response = client.post('/register', data = modify_dict(post_data, "new_first_name", "a"))
    assert response.status_code == 200
    assert b'"errors":{"new_first_name":["Field must be between 2 and 50 characters long."]},"login_success":false' in response.data

    #8. Post data with too long lastname
    response = client.post('/register', data = modify_dict(post_data, "new_last_name", "a" * 51))
    assert response.status_code == 200
    assert b'"errors":{"new_last_name":["Field must be between 2 and 50 characters long."]},"login_success":false' in response.data

    #9. Post data with too short lastname
    response = client.post('/register', data = modify_dict(post_data, "new_last_name", "a"))
    assert response.status_code == 200
    assert b'"errors":{"new_last_name":["Field must be between 2 and 50 characters long."]},"login_success":false' in response.data

    #10. Post data with malformed email
    response = client.post('/register', data = modify_dict(post_data, "new_email", "email@example"))
    assert response.status_code == 200
    assert b'"errors":{"new_email":["Invalid email address."]},"login_success":false' in response.data

    #11. Post data with too short new_password
    response = client.post('/register', data = modify_dict(post_data, "new_password", "a"))
    assert response.status_code == 200
    assert b'{"errors":{"confirm_password":["Passwords must match"],"new_password":["Passwords must match","Password must be between 8 and 32 characters long"]},"login_success":false' in response.data

    #12. Post data with too long new_password
    response = client.post('/register', data = modify_dict(post_data, "new_password", "a" * 33))
    assert response.status_code == 200
    assert b'{"errors":{"confirm_password":["Passwords must match"],"new_password":["Passwords must match","Password must be between 8 and 32 characters long"]},"login_success":false' in response.data

    #13. Post data with too short confirm_password
    response = client.post('/register', data = modify_dict(post_data, "confirm_password", "a"))
    assert response.status_code == 200
    assert b'{"errors":{"confirm_password":["Passwords must match","Password must be between 8 and 32 characters long"],"new_password":["Passwords must match"]},"login_success":false' in response.data

    #14. Post data with too long confirm_password
    response = client.post('/register', data = modify_dict(post_data, "confirm_password", "a" * 33))
    assert response.status_code == 200
    assert b'{"errors":{"confirm_password":["Passwords must match","Password must be between 8 and 32 characters long"],"new_password":["Passwords must match"]},"login_success":false' in response.data

    #15. Post data with mismatched passwords
    response = client.post('/register', data = modify_dict(post_data, "confirm_password", "mismatched_password"))
    assert response.status_code == 200
    assert b'{"errors":{"confirm_password":["Passwords must match"],"new_password":["Passwords must match"]},"login_success":false,"message":"Register form validation failed!"}' in response.data

# --Confirm email route--
def test_confirm_email_no_token_in_url(client):
  response = client.get('/confirm/')
  assert response.status_code == 404

def test_confirm_email_invalid_token(client):
  response = client.get('/confirm/invalid_token')
  assert response.status_code == 200
  assert b'The confirmation link is invalid or has expired.' in response.data

def test_confirm_email_valid_token_but_user_not_found(client):
  response = client.get('/confirm/' + generate_token('email@example.com'))
  assert response.status_code == 200
  assert b'Something went wrong with the confirmation process. Please try again.' in response.data

def test_confirm_email_valid_token_user_already_confirmed(logged_in_user_client):
  confirm_user(current_user)
  response = logged_in_user_client.get('/confirm/' + generate_token('email@example.com'))
  assert response.status_code == 302
  assert response.headers['Location'] == url_for('main.home')

def test_confirm_email_valid_token_unconfirmed_user(logged_in_user_client):
  response = logged_in_user_client.get('/confirm/' + generate_token('email@example.com'))
  assert response.status_code == 302
  assert response.headers['Location'] == url_for('main.home')

# --Unocnfirmed route--
# Something

# --Resend confirmation route--
# Something

# --Forgot password form--
# Too short email, too long email, malformed email format, no email

# --reset password route--
# Something

# --logout route--
# Something

# TRY POSTING TO /LOGOUT ROUTE to determine if every route needs explicit methods

# 

# endregion ROUTE TESTS

# region HELPER FUNCTION TESTS



# endregion HELPER FUNCTION TESTS