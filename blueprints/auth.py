#Flask imports
from flask import Blueprint, render_template, redirect, url_for, jsonify, make_response, flash, request, current_app
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, login_manager
from flask_mail import Message

#Library imports
import uuid, requests
from datetime import datetime
from functools import wraps

#Custom imports
from database import User, get_user_by_email, get_user_for_flask, insert_user, update_user, confirm_user
from exceptions import *
from forms import LoginForm, RegisterForm, ForgotPasswordForm
from secret import RECAPTCHA_SITE_KEY, RECAPTCHA_SECRET_KEY, RECAPTCHA_VERIFY_URL
from textLogging import log_write

auth_bp = Blueprint('auth', __name__)

login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(uuid):
  return get_user_for_flask(uuid)

# region -----Flask Routes-----

# Render the login page
@auth_bp.route("/")
@auth_bp.route('/login', methods=["GET"])
def login():
  try:
    if current_user.is_authenticated and current_user.confirmed:
      return redirect(url_for('main.home'))
    else:
      return render_template('login.html',login_form=LoginForm(), register_form=RegisterForm(), forgot_form=ForgotPasswordForm(), reCAPTCHA_site_key=RECAPTCHA_SITE_KEY)
  except Exception as e:
    log_write(f"INTERNAL ERROR: {e}")

# Attempt to log in the user based on the submitted form data from the login.html page (/login route)
@auth_bp.route('/api/login', methods=["POST"])
def api_login():
  try:
    # 1. Fetch the form data
    form = LoginForm()
    email = form.email.data
    password = form.password.data

    # 2. Check the form validity
    if not form.validate():
      errors = {field.name: field.errors for field in form if field.errors}
      log_write(f"LOGIN FAIL: Errors - {errors}", "LoginAttemptsLog.txt")
      return jsonify(message="Login form validation failed!", login_success=False, errors=errors)

    # 3. Check the recaptchaToken
    recaptchaToken = request.form.get('recaptchaToken')
    verify_recaptcha(recaptchaToken)
    
    # 4. Check if there is a user with the submitted email
    user = get_user_by_email(email)
    if user is None:
      return jsonify({'message': 'No user with that email exists!', 'login_success': False})

    # 5. If the user is already authenticated (logged in), check if their email is confirmed and either log them in or send them to the uncomfirmed email page
    if user == current_user and current_user.is_authenticated:
      if user.confirmed:
        log_write(f"LOGIN SUCCESS: For user {user.id}", "LoginAttemptsLog.txt")
        return jsonify({'login_success': True})
      else:
        log_write(f"UNCONFIRMED LOGIN: For user {user.id}", "LoginAttemptsLog.txt")
        return jsonify({'login_success': False, "confirmed": False})
    
    # 6. Check the submitted password against the hashed password in the database
    if user.check_password(password):
      login_user(user, remember=False) # TODO: Swap to this eventually: login_user(user, remember=form.remember_me.data) *and ctrl+f for this comment*
      response = make_response(jsonify({'login_success': True}))
      log_write(f"LOGIN SUCCESS: For user {user.id}", "LoginAttemptsLog.txt")
      return set_secure_cookie(response, 'uuid', user.id) # Set the encrypted uuid cookie on the user's browser
    else:
      log_write(f"LOGIN FAIL: Incorrect password attempt ({password}) for user {user.id}", "LoginAttemptsLog.txt")
      return jsonify({'message': 'Incorrect password!', 'login_success': False})
  except Exception as e:
    log_write(f"LOGIN FAIL: {e}", "LoginAttemptsLog.txt")
    return jsonify({'message': 'Error: An unknown error occurred!', 'login_success': False})

@auth_bp.route("/register", methods=["POST"])
def register():
  try:
    # 1. Fetch the form data
    form = RegisterForm()
    new_email = form.new_email.data
    new_password = form.new_password.data
    new_first_name = form.new_first_name.data
    new_last_name = form.new_last_name.data

    # 2. Check the form validity
    if not form.validate():
      errors = {field.name: field.errors for field in form if field.errors}
      log_write(f"REGISTER FAIL: Errors - {errors}", "LoginAttemptsLog.txt")
      return jsonify(message="Register form validation failed!", login_success=False, errors=errors)

    # 3. Check the recaptcha
    recaptchaToken = request.form.get('recaptchaToken')
    verify_recaptcha(recaptchaToken)

    # 4. Check if user with that email already exists
    if get_user_by_email(new_email) is not None:
      return jsonify({'message': 'A user with that email already exists!', 'register_success': False})

    # 5. If all steps before are successful, generate and insert a new user
    uuid = generate_uuid()
    (new_password_hash, new_password_salt) = User.hash_password(new_password)
    new_user = User(uuid, new_email, new_password_hash, new_password_salt, new_first_name, new_last_name, datetime.now())
    insert_user(new_user)
    log_write(f"REGISTER SUCCESS: New user with id {uuid} inserted", "LoginAttemptsLog.txt")
    
    # 6. Generate confirmation token and send email
    token = generate_token(new_email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    msg = Message('Budgeteer: Confirm your email address', sender=current_app.config['MAIL_USERNAME'], recipients=[new_email])
    msg.html = render_template('emails/email_confirmation.html', confirm_url=confirm_url)
    current_app.mail.send(msg)
    log_write(f"REGISTER EMAIL SENT: For user {uuid} to email {new_email}", "LoginAttemptsLog.txt")
    return jsonify({'message': 'A confirmation email has been sent to your email address!', 'register_success': True})
  except Exception as e:
    log_write(f"REGISTER ERROR: {e}", "LoginAttemptsLog.txt")
    return jsonify({'message': 'An unknown error occurred during registration!', 'register_success': False})

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
  try:
    email = confirm_token(token)
  except:
    log_write(f"CONFIRM FAIL: Confirmation link invalid or expired for token {token}", "LoginAttemptsLog.txt")
    return render_template("error_page.html", message="The confirmation link is invalid or has expired.")
  
  try:
    user = get_user_by_email(email)
    if user is None:
      log_write(f"CONFIRM FAIL: No user found with email {email}", "LoginAttemptsLog.txt")
      return render_template("error_page.html", message="Something went wrong with the confirmation process. Please try again.")

    if user.confirmed is False:
      confirm_user(user)
      log_write(f"CONFIRM SUCCESS: User {user.id} has been confirmed", "LoginAttemptsLog.txt")
    
    login_user(user)
    flash('Your account has been successfully confirmed!', 'success')
    response = make_response(redirect(url_for('main.home')))
    return set_secure_cookie(response, 'uuid', user.id) # Set the encrypted uuid cookie on the user's browser
  except Exception as e:
    log_write(f"CONFIRM FAIL: {e}", "LoginAttemptsLog.txt")

@auth_bp.route('/unconfirmed')
@login_required
def unconfirmed():
  try:
    if current_user.confirmed:
      return redirect(url_for('main.home'))
    return render_template('unconfirmed.html')
  except Exception as e:
    log_write(f"UNCOMFIRMED FAIL: {e}", "LoginAttemptsLog.txt")

@auth_bp.route('/resend-confirmation')
@login_required
def resend_confirmation():
  try:
    token = generate_token(current_user.email)
    if current_user.confirmed:
      return redirect(url_for('main.home'))
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    msg = Message('Budgeteer: Confirm your email address', sender=current_app.config['MAIL_USERNAME'], recipients=[current_user.email])
    msg.html = render_template('emails/email_confirmation.html', confirm_url=confirm_url)
    current_app.mail.send(msg)
    log_write(f"EMAIL CONFIRM RESEND: Email confirmation email resent to {current_user.email} for user {current_user.id}", "LoginAttemptsLog.txt")
    flash('A new confirmation email has been sent to your email address.', 'success')
    return redirect(url_for('auth.login'))
  except Exception as e:
    log_write(f"RESEND CONFIRMATION FAIL: {e}", "LoginAttemptsLog.txt")

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
  try:
    # 1. Fetch the form data
    form = ForgotPasswordForm()
    email = form.email.data

    # 2. Check the form validity
    if not form.validate():
      errors = {field.name: field.errors for field in form if field.errors}
      log_write(f"PWD RESET FAIL: Errors - {errors}", "LoginAttemptsLog.txt")
      return jsonify(message="Password reset form validation failed!", login_success=False, errors=errors) #TODO: Probably make this error message better when unit tests come around

    # 3. Verify the recaptcha
    recaptchaToken = request.form.get('recaptchaToken')
    verify_recaptcha(recaptchaToken)

    # 4. Verify the user exists
    user = get_user_by_email(email)
    if user is None:
      log_write(f"FORGOT PWD FAIL: No user with email {email}", "LoginAttemptsLog.txt")
      return jsonify({'message': 'No user found with that email!', 'success': False})

    # 5. If all else works, send a password reset email
    token = generate_token(email)
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message('Budgeteer: Reset Your Password', sender=current_app.config["MAIL_USERNAME"], recipients=[email])
    msg.html = render_template('emails/password_reset.html', reset_url=reset_url)
    current_app.mail.send(msg)
    log_write(f"FORGOT PWD SUCCESS: Forgot password email for user {user.id} sent to {email}", "LoginAttemptsLog.txt")
    return jsonify({'message': 'Password reset email has been sent!', 'success': True})
  except Exception as e:
    log_write(f"FORGOT PWD ERROR: {e}", "LoginAttemptsLog.txt")
    return jsonify({'message': 'An unknown error occurred while processing your request!', 'success': False})

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
  try:
    try:
      email = confirm_token(token)
    except:
      log_write(f"PWD RESET FAIL: Link invalid or expired for token {token}", "LoginAttemptsLog.txt")
      return render_template("error_page.html", message="The reset password link is invalid or has expired.")

    user = get_user_by_email(email)
    if user is None:
      log_write(f"PWD RESET FAIL: No user with email {email}", "LoginAttemptsLog.txt")
      return render_template("error_page.html", message="Something went wrong with the password reset process. Please try again.")

    if request.method == 'POST':
      new_password = request.form.get('new_password')
      confirm_password = request.form.get('confirm_password')

      if new_password != confirm_password:
        flash('Passwords must match!', 'error')
        return redirect(url_for('auth.reset_password', token=token))

      new_password_hash, new_password_salt = User.hash_password(new_password)
      user.password_hash = new_password_hash
      user.password_salt = new_password_salt
      update_user(user)

      log_write(f"PWD RESET SUCCESS: Password reset for user {user.id}", "LoginAttemptsLog.txt")
      flash('Your password has been successfully reset!', 'success')
      return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)
  except Exception as e:
    log_write(f"RESET PASSWORD FAIL: {e}", "LoginAttemptsLog.txt")

@auth_bp.route('/logout')
def logout():
  try:
    if current_user.is_authenticated:
      uuid = current_user.id # Save this value so it can be logged after the current_user variable is changed when logging out
      logout_user()
      log_write(f"LOGOUT: User {uuid}", "LoginAttemptsLog.txt")
    return redirect(url_for('auth.login'))
  except Exception as e:
    log_write(f"LOGOUT FAIL: {e}", "LoginAttemptsLog.txt")

# endregion -----Flask Routes-----

# region -----Helper functions-----

def check_confirmed(func):
  @wraps(func)
  def decorated_function(*args, **kwargs):
      if current_user.confirmed is False:
          return redirect(url_for('auth.unconfirmed'))
      return func(*args, **kwargs)

  return decorated_function

def generate_uuid():
  return str(uuid.uuid4())

def set_secure_cookie(response, key, value):
  encrypted_value = current_app.serializer.dumps(value)
  response.set_cookie(key, encrypted_value, httponly=True, secure=True, max_age=30*24*60*60) #Make age is 30 days
  return response

def get_uuid_from_cookie():
  encrypted_uuid = request.cookies.get('uuid')
  if encrypted_uuid:
    return current_app.serializer.loads(encrypted_uuid)    
  else:
    raise UserIdCookieNotFoundError()

def generate_token(email):
  return current_app.timed_serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])

def confirm_token(token, expiration=3600):
  try:
    email = current_app.timed_serializer.loads(token, salt=current_app.config["SECURITY_PASSWORD_SALT"], max_age=expiration)
    return email
  except Exception as e:
    raise e

def verify_recaptcha(recaptchaToken):
  verify_response = requests.post(url=RECAPTCHA_VERIFY_URL, data={'secret': RECAPTCHA_SECRET_KEY, 'response': recaptchaToken}).json()
  if verify_response['success'] == False or verify_response['score'] < 0.5:
    raise RecaptchaFailError(verify_response)


# endregion -----Helper functions-----