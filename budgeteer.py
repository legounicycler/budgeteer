"""
This file contains functions relevant the GUI, the flask app, and getting data from the browser
This file interacts a lot with the javascript/jQuery running on the site
"""

# Flask imports
from flask import Flask, render_template, url_for, request, redirect, jsonify, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message

# Library imports
from itsdangerous import URLSafeTimedSerializer, URLSafeSerializer
import uuid, re, os
from werkzeug.utils import secure_filename
from functools import wraps

# Custom imports
from database import *
from exceptions import *
from forms import *
from textLogging import log_write
from secret import SECRET_KEY, MAIL_PASSWORD, MAIL_USERNAME, SECURITY_PASSWORD_SALT

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
timed_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
serializer = URLSafeSerializer(app.config['SECRET_KEY'])

# Configure Flask-Mail settings
app.config['MAIL_SERVER'] = 'smtp.zoho.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECURITY_PASSWORD_SALT'] = SECURITY_PASSWORD_SALT

mail = Mail(app)

def datetimeformat(value, format='%m/%d/%Y'):
  return value.strftime(format)

def datetimeformatshort(value, format='%b %d\n%Y'):
  return value.strftime(format)

def inputformat(num):
  return '%.2f' % num

app.jinja_env.filters['datetimeformat'] = datetimeformat
app.jinja_env.filters['datetimeformatshort'] = datetimeformatshort
app.jinja_env.filters['balanceformat'] = balanceformat
app.jinja_env.filters['inputformat'] = inputformat

def check_confirmed(func):
  @wraps(func)
  def decorated_function(*args, **kwargs):
      if current_user.confirmed is False:
          return redirect(url_for('unconfirmed'))
      return func(*args, **kwargs)

  return decorated_function

def generate_uuid():
  return str(uuid.uuid4())

def set_secure_cookie(response, key, value):
  encrypted_value = serializer.dumps(value)
  response.set_cookie(key, encrypted_value, httponly=True, secure=True, max_age=30*24*60*60) #Make age is 30 days
  return response

def get_uuid_from_cookie():
  encrypted_uuid = request.cookies.get('uuid')
  if encrypted_uuid:
    return serializer.loads(encrypted_uuid)    
  else:
    raise UserIdCookieNotFoundError()

def generate_token(email):
  return timed_serializer.dumps(email, salt=SECURITY_PASSWORD_SALT)

def confirm_token(token, expiration=3600):
  try:
    email = timed_serializer.loads(token, salt=app.config["SECURITY_PASSWORD_SALT"], max_age=expiration)
    return email
  except Exception as e:
    raise e

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(uuid):
  return get_user_for_flask(uuid)

@app.route("/")
@app.route('/login', methods=["POST", "GET"])
def login():
  if current_user.is_authenticated and current_user.confirmed:
    return redirect(url_for('home'))
  else:
    login_form = LoginForm()
    register_form = RegisterForm()
    return render_template('login.html',login_form=login_form, register_form=register_form)
  
@app.route('/api/login', methods=["POST", "GET"])
def api_login():

  # 1. Fetch the form data
  form = LoginForm()
  email = form.email.data
  password = form.password.data
  
  # 2. Check if there is a user with the submitted email
  if email is not None:
    user = get_user_by_email(email)
    if user is None:
      return jsonify({'message': 'No user with that email exists!', 'login_success': False})
  else:
    return jsonify({'message': 'No email was submitted!', 'login_success': False})


  # # 3. If the user is not confirmed, redirect to the confirm page
  # if user.confirmed is False:
  #   return jsonify({'unconfirmed': True, 'login_success': False})

  # 4. If the user is already authenticated (logged in), return a success message (which will redirect to the home page)
  if current_user.is_authenticated:
    return jsonify({'login_success': True})
  
  # 5. Check the submitted password against the hashed password in the database
  if user.check_password(password):
    login_user(user, remember=False) # TODO: Swap to this eventually: login_user(user, remember=form.remember_me.data) *and ctrl+f for this comment*
    response = make_response(jsonify({'login_success': True}))
    return set_secure_cookie(response, 'uuid', user.id) # Set the encrypted uuid cookie on the user's browser
  else:
    return jsonify({'message': 'Incorrect password!', 'login_success': False})

@app.route("/register", methods=["POST", "GET"])
def register():
  try:
    form = RegisterForm()
    new_email = form.new_email.data
    new_password = form.new_password.data
    new_first_name = form.new_first_name.data
    new_last_name = form.new_last_name.data

    # 1. Check if user with that email already exists
    if get_user_by_email(new_email) is not None:
      return jsonify({'message': 'A user with that email already exists!'})

    # 2. Check the password validation
    if form.new_password.validate(form) and form.confirm_password.validate(form):
      uuid = generate_uuid()
      (new_password_hash, new_password_salt) = hash_password(new_password)
      new_user = User(uuid, new_email, new_password_hash, new_password_salt, new_first_name, new_last_name, datetime.now())
      insert_user(new_user)
    else:
      return jsonify({'message': 'Passwords must match!'})
    
    #3. Generate confirmation token and send email
    token = generate_token(new_email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    msg = Message('Budgeteer: Confirm your email address', sender=MAIL_USERNAME, recipients=[new_email])
    msg.html = render_template('emails/email_confirmation.html', confirm_url=confirm_url)
    mail.send(msg)
    return jsonify({'message': 'A confirmation email has been sent to your email address!'})
  except:
    return jsonify({'message': 'An unknown error occurred during registration!'})

@app.route('/confirm/<token>')
def confirm_email(token):
  try:
    email = confirm_token(token)
  except:
    return render_template("error_page.html", message="The confirmation link is invalid or has expired.")
  
  user = get_user_by_email(email)
  if user is None:
    return render_template("error_page.html", message="Something went wrong with the confirmation process. Please try again.")

  if user.confirmed is False:
    confirm_user(user)
  
  login_user(user)
  response = make_response(redirect(url_for('home')))
  return set_secure_cookie(response, 'uuid', user.id) # Set the encrypted uuid cookie on the user's browser

@app.route('/unconfirmed')
@login_required
def unconfirmed():
  if current_user.confirmed:
    return redirect(url_for('home'))
  return render_template('unconfirmed.html')

@app.route('/logout')
def logout():
  if current_user.is_authenticated:
    logout_user()
  return redirect(url_for('login'))

@app.route("/home", methods=['GET'])
@login_required
@check_confirmed
def home():
  timestamp = request.cookies.get('timestamp')
  if timestamp is None:
    return render_template('get_timestamp.html')
  else:
    try: 
      uuid = get_uuid_from_cookie()
      u = get_user_by_uuid(uuid)
      check_pending_transactions(uuid, timestamp)
      (transactions_data, offset, limit) = get_home_transactions(uuid,0,50)
      (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
      (active_accounts, accounts_data) = get_user_account_dict(uuid)
      unallocated_balance = get_envelope_balance(u.unallocated_e_id)/100
      total_funds = get_total(uuid)
      response = make_response(render_template(
        'layout.html',
        current_page='All transactions',
        active_envelopes=active_envelopes,
        unallocated_balance=unallocated_balance,
        envelopes_data=envelopes_data,
        budget_total=budget_total,
        active_accounts=active_accounts,
        accounts_data=accounts_data,
        transactions_data=transactions_data,
        total_funds=total_funds,
        offset=offset,
        limit=limit,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        unallocated_e_id=u.unallocated_e_id,
        TType=TType
      ))
      response.delete_cookie('timestamp')
      return response
    except CustomException as e:
      return jsonify({"error": str(e)})

@app.route("/get_home_transactions_page", methods=["POST"])
@login_required
@check_confirmed
def get_all_transactions_page():
  try:
    uuid = get_uuid_from_cookie()
    timestamp = request.get_json()['timestamp']
    current_page = 'All Transactions'
    check_pending_transactions(uuid, timestamp)
    (transactions_data, offset, limit) = get_home_transactions(uuid,0,50)
    (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
    (active_accounts, accounts_data) = get_user_account_dict(uuid)
    page_total = balanceformat(get_total(uuid))
    data = {}
    data['page_total'] = page_total
    data['page_title'] = current_page
    data['transactions_html'] = render_template(
      'transactions.html',
      current_page=current_page,
      transactions_data=transactions_data,
      envelopes_data=envelopes_data,
      accounts_data=accounts_data,
      offset=offset, limit=limit,
      TType = TType
    )
    return jsonify(data)
  except CustomException as e:
    return jsonify({"error": "ERROR: Something went wrong and your envelope data could not be loaded!"})

@app.route("/get_envelope_page", methods=["POST"])
@login_required
@check_confirmed
def get_envelope_page():
  try:
    uuid = get_uuid_from_cookie()
    js_data = request.get_json()
    envelope_id = js_data['envelope_id']
    timestamp = js_data['timestamp']
    current_page = f'envelope/{envelope_id}'
    check_pending_transactions(uuid, timestamp)
    (transactions_data, offset, limit) = get_envelope_transactions(uuid,envelope_id,0,50)
    (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
    (active_accounts, accounts_data) = get_user_account_dict(uuid)
    page_total = balanceformat(get_envelope(envelope_id).balance/100)
    data = {}
    data['page_total'] = page_total
    data['envelope_name'] = get_envelope(envelope_id).name
    data['transactions_html'] = render_template(
      'transactions.html',
      current_page=current_page,
      transactions_data=transactions_data,
      envelopes_data=envelopes_data,
      accounts_data=accounts_data,
      offset=offset, limit=limit,
      TType = TType
    )
    return jsonify(data)
  except CustomException as e:
    return jsonify({"error": "ERROR: Something went wrong and your envelope data could not be loaded!"})

@app.route("/get_account_page", methods=["POST"])
@login_required
@check_confirmed
def get_account_page():
  try:
    uuid = get_uuid_from_cookie()
    js_data = request.get_json()
    account_id = js_data['account_id']
    timestamp = js_data['timestamp']
    current_page = f'account/{account_id}'
    check_pending_transactions(uuid, timestamp)
    (transactions_data, offset, limit) = get_account_transactions(uuid,account_id,0,50)
    (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
    (active_accounts, accounts_data) = get_user_account_dict(uuid)
    page_total = balanceformat(get_account(account_id).balance/100)
    data = {}
    data['page_total'] = page_total
    data['account_name'] = get_account(account_id).name
    data['transactions_html'] = render_template(
      'transactions.html',
      current_page=current_page,
      transactions_data=transactions_data,
      envelopes_data=envelopes_data,
      accounts_data=accounts_data,
      offset=offset,
      limit=limit,
      TType = TType)
    return jsonify(data)
  except CustomException as e:
    return jsonify({"error": "ERROR: Something went wrong and your account data could not be loaded!"})

@app.route('/new_expense', methods=['POST'])
@login_required
@check_confirmed
def new_expense(edited=False):
  try:
    uuid = get_uuid_from_cookie()
    names = [n.lstrip() for n in request.form['name'].split(',') if n.lstrip()] #Parse name field separated by commas
    amounts = request.form.getlist('amount')
    envelope_ids = request.form.getlist('envelope_id')
    account_id = request.form['account_id']
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    timestamp = date_parse(request.form['timestamp'])
    note = request.form['note']
    scheduled = len(request.form.getlist('scheduled')) != 0
    schedule = request.form['schedule']
    sched_t_submitted = False
    pending = is_pending(date, timestamp)
    toasts = []

    try: 
      for i in range(len(amounts)):
        amounts[i] = int(round(float(amounts[i]) * 100))
        envelope_ids[i] = int(envelope_ids[i])
    except:
      raise InvalidFormDataError("ERROR: Invalid form data in 'amount' field for new_expense!")
    
    for name in names:
      t = Transaction(TType.BASIC_TRANSACTION, name, amounts, date, envelope_ids, account_id, None, note, None, False, uuid, pending)
      if scheduled and not pending:
        # Create pending scheduled transaction
        nextdate = schedule_date_calc(date, schedule, timestamp, True)
        scheduled_t = Transaction(TType.BASIC_TRANSACTION, name, amounts, nextdate, envelope_ids, account_id, None, note, schedule, False, uuid, is_pending(nextdate, timestamp))
      elif scheduled and pending:
        t.schedule = schedule

      if len(envelope_ids) == 1: # If it is a BASIC_TRANSACTION
        t.grouping = gen_grouping_num()
        t.envelope_id = envelope_ids[0]
        t.amt = amounts[0]
        insert_transaction(t)
        if scheduled and not pending:
          scheduled_t.grouping = gen_grouping_num()
          scheduled_t.envelope_id = envelope_ids[0]
          scheduled_t.amt = amounts[0]
          insert_transaction(scheduled_t)
          sched_t_submitted = True
      else: # If it is a SPLIT_TRANSACTION
        t.type = TType.SPLIT_TRANSACTION
        new_split_transaction(t)
        if scheduled and not pending:
          scheduled_t.type = TType.SPLIT_TRANSACTION
          new_split_transaction(scheduled_t)
          sched_t_submitted = True
    if edited:
      toasts.append("Transaction updated!")
    else:
      if len(names) > 1:
        toasts.append(f'Added {len(names)} new expenses!')
        if sched_t_submitted:
          toasts.append(f'Added {len(names)} new expenses scheduled for {datetimeformat(nextdate)}!')
      elif len(names) == 1:
        toasts.append('Added new expense!')
        if sched_t_submitted:
          toasts.append(f'Added new expense scheduled for {datetimeformat(nextdate)}!')
      else:
        raise OtherError("ERROR: No transaction name was submitted for new_expense!")

    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/new_transfer', methods=['POST'])
@login_required
@check_confirmed
def new_transfer(edited=False):
  try:
    uuid = get_uuid_from_cookie()
    transfer_type = int(request.form['transfer_type'])
    names = [n.lstrip() for n in request.form['name'].split(',') if n.lstrip()] #Parse name field separated by commas
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    timestamp = date_parse(request.form['timestamp'])
    note = request.form['note']
    scheduled = len(request.form.getlist('scheduled')) != 0
    schedule = request.form['schedule']
    sched_t_submitted = False
    pending = is_pending(date, timestamp)
    toasts = []

    try:
      amount = int(round(float(request.form['amount'])*100))
    except:
      raise InvalidFormDataError("ERROR: Invalid form data in 'amount' field for new_transfer!")
    
    for name in names:
      if (transfer_type == 2):
        to_account = request.form['to_account']
        from_account = request.form['from_account']
        if scheduled and pending:
          # Create transfer WITH a schedule
          account_transfer(name, amount, date, to_account, from_account, note, schedule, uuid, pending)
        elif scheduled and not pending:
          # Create transfer WITHOUT schedule, then pending transfer WITH schedule
          account_transfer(name, amount, date, to_account, from_account, note, None, uuid, pending)
          nextdate = schedule_date_calc(date, schedule, timestamp, True)
          account_transfer(name, amount, nextdate, to_account, from_account, note, schedule, uuid, is_pending(nextdate, timestamp))
          sched_t_submitted = True
        else:
          # Create transfer WITHOUT schedule
          account_transfer(name, amount, date, to_account, from_account, note, None, uuid, pending)
      elif (transfer_type == 1):
        to_envelope = request.form['to_envelope']
        from_envelope = request.form['from_envelope']
        if scheduled and pending:
          # Create a transfer WITH a schedule
          envelope_transfer(name, amount, date, to_envelope, from_envelope, note, schedule, uuid, pending)
        elif scheduled and not pending:
          # Create transfer WITHOUT schedule, then pending transfer WITH schedule
          envelope_transfer(name, amount, date, to_envelope, from_envelope, note, None, uuid, pending)
          nextdate = schedule_date_calc(date, schedule, timestamp, True)
          envelope_transfer(name, amount, nextdate, to_envelope, from_envelope, note, schedule, uuid, is_pending(nextdate, timestamp))
          sched_t_submitted = True
        else:
          # Create transfer WITHOUT schedule
          envelope_transfer(name, amount, date, to_envelope, from_envelope, note, None, uuid, pending)
      else:
        raise InvalidFormDataError("ERROR: Bad form data in 'transfer_type' field for new_transfer!")

      if edited:
        toasts.append("Transaction updated!")
      else:
        if len(names) > 1:
          toasts.append(f'Added {len(names)} new transfers!')
          if sched_t_submitted:
            toasts.append(f'Added {len(names)} new transfers scheduled for {datetimeformat(nextdate)}!')
        elif len(names) == 1:
          toasts.append('Added new transfer!')
          if sched_t_submitted:
            toasts.append(f'Added new transfer scheduled for {datetimeformat(nextdate)}!')
        else:
          raise InvalidFormDataError("ERROR: No transaction name was submitted for new_transfer!")

    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/new_income', methods=['POST'])
@login_required
@check_confirmed
def new_income(edited=False):
  try:
    uuid = get_uuid_from_cookie()
    u = get_user_by_uuid(uuid)
    names = [n.lstrip() for n in request.form['name'].split(',') if n.lstrip()] #Parse name field separated by commas
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    timestamp = date_parse(request.form['timestamp'])
    account_id = request.form['account_id']
    note = request.form['note']
    scheduled = len(request.form.getlist('scheduled')) != 0
    schedule = request.form['schedule']
    sched_t_submitted = False
    pending = is_pending(date, timestamp)
    toasts = []

    try:
      amount = int(round(float(request.form['amount'])*100))
    except:
      raise InvalidFormDataError("ERROR: Invalid form data in 'amount' field for new_income!")
    
    for name in names:
      t = Transaction(TType.INCOME, name, -1 * amount, date, u.unallocated_e_id, account_id, gen_grouping_num(), note, None, False, uuid, pending)
      if scheduled and not pending:
        insert_transaction(t)
        nextdate = schedule_date_calc(date, schedule, timestamp, True)
        scheduled_t = Transaction(TType.INCOME, name, -1 * amount, nextdate, u.unallocated_e_id, account_id, gen_grouping_num(), note, schedule, False, uuid, is_pending(nextdate, timestamp))
        insert_transaction(scheduled_t)
        sched_t_submitted = True
      elif scheduled and pending:
        t.schedule = schedule
        insert_transaction(t)
      else:
        insert_transaction(t)

      if edited:
        toasts.append("Transaction updated!")
      else:
        if len(names) > 1:
          toasts.append(f'Added {len(names)} new income!')
          if sched_t_submitted:
            toasts.append(f'Added {len(names)} new incomes scheduled for {datetimeformat(nextdate)}!')
        elif len(names) == 1:
          toasts.append('Added new income!')
          if sched_t_submitted:
            toasts.append(f'Added new income scheduled for {datetimeformat(nextdate)}!')
        else:
          raise InvalidFormDataError("ERROR: No transaction name was submitted for new_income!")

    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/fill_envelopes', methods=['POST'])
@login_required
@check_confirmed
def fill_envelopes(edited=False):
  try:
    uuid = get_uuid_from_cookie()
    names = [n.lstrip() for n in request.form['name'].split(',') if n.lstrip()] #Parse name field separated by commas
    amounts = request.form.getlist('fill-amount')
    envelope_ids = request.form.getlist('envelope_id')
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    timestamp = date_parse(request.form['timestamp'])
    note = request.form['note']
    scheduled = len(request.form.getlist('scheduled')) != 0
    schedule = request.form['schedule']
    sched_t_submitted = False
    pending = is_pending(date, timestamp)
    toasts = []
    
    try:
      deletes = []
      for i in range(len(amounts)):
        if amounts[i] == "":
          deletes.append(i)
        else:
          amounts[i] = int(round(float(amounts[i])*100))
          envelope_ids[i] = int(envelope_ids[i])
      for index in reversed(deletes):
        amounts.pop(index)
        envelope_ids.pop(index)
    except:
      raise InvalidFormDataError("ERROR: Invalid form data in 'amount' field for fill_envelopes!")
    
    if amounts:
      for name in names:
        t = Transaction(TType.ENVELOPE_FILL, name, amounts, date, envelope_ids, None, None, note, None, False, uuid, pending)
        if scheduled and not pending:
          envelope_fill(t)
          nextdate = schedule_date_calc(date, schedule, timestamp, True)
          scheduled_t = Transaction(TType.ENVELOPE_FILL, name, amounts, nextdate, envelope_ids, None, None, note, schedule, False, uuid, is_pending(nextdate, timestamp))
          envelope_fill(scheduled_t)
          sched_t_submitted = True
        elif scheduled and pending:
          t.schedule = schedule
          envelope_fill(t)
        else:
          envelope_fill(t)
          
      if edited:
        toasts.append("Transaction updated!")
      else:
        if len(names) > 1:
          toasts.append(f'Added {len(names)} envelope fills!')
          if sched_t_submitted:
            toasts.append(f'Added {len(names)} new envelope fills scheduled for {datetimeformat(nextdate)}!')
        elif len(names) == 1:
          toasts.append('Envelopes filled!')
          if sched_t_submitted:
            toasts.append(f'Added new envelope fill scheduled for {datetimeformat(nextdate)}!')
        else:
          raise InvalidFormDataError("ERROR: No transaction name was submitted for fill_envelopes!")
    else:
      toasts.append("No envelope fill was created!")

    health_check(toasts)
    return jsonify({'toasts': toasts})

  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/edit_delete_envelope', methods=['POST'])
@login_required
@check_confirmed
def edit_delete_envelope():
  try:
    uuid = get_uuid_from_cookie()
    u = get_user_by_uuid(uuid)
    name = request.form['name']
    note = request.form['note']
    date = datetime.strptime(request.form['date'], "%m/%d/%Y")
    envelope_id = request.form['envelope_id']
    # timestamp = date_parse(request.form['timestamp']) #Don't need to check timestamp in this function
    toasts = []

    # A copy of the delete_envelope() function from database.py but with the info from the form pasted in
    with conn:
      if (envelope_id != u.unallocated_e_id): #You can't delete the unallocated envelope
        e = get_envelope(envelope_id)
        grouping = gen_grouping_num()
        # 1. Empty the deleted envelope
        t_envelope = Transaction(TType.ENVELOPE_DELETE, name, e.balance, date, envelope_id, None, grouping, note, None, 0, uuid, False)
        insert_transaction(t_envelope)
        # 2. Fill the unallocated envelope
        t_unallocated = Transaction(TType.ENVELOPE_DELETE, name, -1*e.balance, date, u.unallocated_e_id, None, grouping, note, None, 0, uuid, False)
        insert_transaction(t_unallocated)
        # 3. Mark the envelope as deleted
        c.execute("UPDATE envelopes SET deleted=1 WHERE id=?", (envelope_id,))
        toasts.append("Transaction updated!")
        log_write('E DELETE: ' + str(get_envelope(envelope_id)))
      else:
        raise InvalidFormDataError("ERROR: You cannot delete the unallocated envelope!")

    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

# TODO: Revisit this. There's probably no need to delete and recreate the transaction. Test to see what happens if you directly
#       update the transaction details in the database
@app.route('/edit_delete_account', methods=['POST'])
@login_required
@check_confirmed
def edit_delete_account():
  try:
    uuid = get_uuid_from_cookie()
    u = get_user_by_uuid(uuid)
    name = request.form['name']
    note = request.form['note']
    date = datetime.strptime(request.form['date'], "%m/%d/%Y")
    account_id = request.form['account_id']
    # timestamp = date_parse(request.form['timestamp']) #Don't need to check timestamp in this function
    toasts = []
    
    # TODO: Look into why this can't be an account delete function in database.py so there is no sqlite here.
    # A copy of the delete_account() function from database.py but with the info from the form pasted in
    with conn:
      a = get_account(account_id)
      
      # 1. Empty the deleted account
      insert_transaction(Transaction(TType.ACCOUNT_DELETE, name, a.balance, date, u.unallocated_e_id, a.id, gen_grouping_num(), note, None, 0, uuid, False))

      # 2. Mark the account as deleted
      c.execute("UPDATE accounts SET deleted=1 WHERE id=?", (account_id,))
      toasts.append("Transaction updated!")
      log_write('A DELETE: ' + str(get_account(account_id)))

    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/edit_account_adjust', methods=['POST'])
@login_required
@check_confirmed
def edit_account_adjust():
  try:
    uuid = get_uuid_from_cookie()
    u = get_user_by_uuid(uuid)
    name = request.form['name']
    date = datetime.strptime(request.form['date'], "%m/%d/%Y")
    note = request.form['note']
    account_id = int(request.form['account_id'])
    timestamp = date_parse(request.form['timestamp'])
    toasts = []

    try:
      balance_diff = int(round(float(request.form['amount'])*100))
    except:
      raise InvalidFormDataError("ERROR: Invalid form data in 'amount' field for edit_account_adjust!")
    
    insert_transaction(Transaction(TType.ACCOUNT_ADJUST, name, -1*balance_diff, date, u.unallocated_e_id, account_id, gen_grouping_num(), note, None, False, uuid, is_pending(date, timestamp)))
    toasts.append("Transaction updated!")

    health_check(toasts)
    return jsonify({'toasts': toasts})

  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/edit_transaction', methods=['POST'])
@login_required
@check_confirmed
def edit_transaction():
  try:
    uuid = get_uuid_from_cookie()
    id = int(request.form['edit-id'])
    type = TType.from_int(int(request.form['type']))
      
    if (type == TType.BASIC_TRANSACTION):
      response = new_expense(True)
    elif (type == TType.ENVELOPE_TRANSFER or type == TType.ACCOUNT_TRANSFER):
      response =  new_transfer(True)
    elif (type == TType.INCOME):
      response = new_income(True)
    elif (type == TType.SPLIT_TRANSACTION):
      response = new_expense(True)
    elif (type == TType.ENVELOPE_FILL):
      response = fill_envelopes(True)
    elif (type == TType.ENVELOPE_DELETE):
      response = edit_delete_envelope()
    elif (type == TType.ACCOUNT_DELETE):
      response = edit_delete_account()
    elif (type == TType.ACCOUNT_ADJUST):
      response =  edit_account_adjust()

    if not response.json.get('error'):
      delete_transaction(uuid, id) #Only delete the original transaction if you were successful in creating the replacement edited transaction
      
    return response
  
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/api/delete_transaction', methods=['POST'])
@login_required
@check_confirmed
def api_delete_transaction():
  try: 
    uuid = get_uuid_from_cookie()
    id = int(request.form['delete-id'])
    # timestamp = date_parse(request.form['timestamp']) #Don't need to check timestamp in this function
    
    delete_transaction(uuid, id)
    return jsonify({'toasts': ["Transaction deleted!"]})
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/api/transaction/<id>/group', methods=['GET'])
@login_required
@check_confirmed
def get_grouped_json_page(id):
  try:
    uuid = get_uuid_from_cookie()
    grouped_json = get_grouped_json(uuid, id)
    return jsonify(grouped_json)
  
  except CustomException as e:
    return jsonify({"error": str(e)})
  

@app.route('/api/edit-accounts', methods=['POST'])
@login_required
@check_confirmed
def edit_accounts_page():
  try:
    uuid = get_uuid_from_cookie()
    edit_balances = request.form.getlist('edit-account-balance')
    original_balances = request.form.getlist('original-account-balance')
    edit_names = request.form.getlist('edit-account-name')
    original_names = request.form.getlist('original-account-name')
    timestamp = date_parse(request.form['timestamp'])
    present_ids = list(map(int, request.form.getlist('account-id'))) # Turn the list of strings into a list of ints
    edit_a_order = list(map(int, request.form.getlist('account-order'))) # Turn the list of strings into a list of ints

    new_balances = request.form.getlist('new-account-balance')
    new_names = request.form.getlist('new-account-name')
    new_a_order = list(map(int, request.form.getlist('new-account-order'))) # Turn the list of strings into a list of ints

    original_a_order = get_user_account_order(uuid)
    accounts_to_edit = []
    new_accounts = []
    for i in range(len(present_ids)):
      if (edit_names[i] != original_names[i] or edit_balances[i] != original_balances[i] or edit_a_order[i] != original_a_order[present_ids[i]]):
        a = Account(present_ids[i], edit_names[i], int(round(float(edit_balances[i])*100)), False, uuid, edit_a_order[i])
        accounts_to_edit.append(a)
    for i in range(len(new_names)):
      new_accounts.append(Account(None, new_names[i], int(round(float(new_balances[i])*100)), False, uuid, new_a_order[i]))

    toasts = []
    toasts.append(edit_accounts(uuid, accounts_to_edit, new_accounts, present_ids, timestamp)) #From the account editor form, there is no date field, so use timestamp for date of transaction

    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/api/edit-envelopes', methods=['POST'])
@login_required
@check_confirmed
def edit_envelopes_page():
  try:
    uuid = get_uuid_from_cookie()
    edit_budgets = request.form.getlist('edit-envelope-budget')
    original_budgets = request.form.getlist('original-envelope-budget')
    envelope_balances = request.form.getlist('envelope-balance')
    edit_names = request.form.getlist('edit-envelope-name')
    original_names = request.form.getlist('original-envelope-name')
    # timestamp = date_parse(request.form['timestamp']) #No timestamp needed for this page
    present_ids = list(map(int, request.form.getlist('envelope-id'))) # Turn the list of strings into a list of ints
    edit_e_order = list(map(int, request.form.getlist('envelope-order'))) # Turn the list of strings into a list of ints

    new_names = request.form.getlist('new-envelope-name')
    new_budgets = request.form.getlist('new-envelope-budget')
    new_e_order = list(map(int, request.form.getlist('new-envelope-order'))) # Turn the list of strings into a list of ints

    original_e_order = get_user_envelope_order(uuid)
    envelopes_to_edit = []
    new_envelopes = []
    for i in range(len(present_ids)):
      if (edit_names[i] != original_names[i] or edit_budgets[i] != original_budgets[i] or edit_e_order[i] != original_e_order[present_ids[i]]): #
        e = Envelope(present_ids[i], edit_names[i], int(round(float(envelope_balances[i])*100)), int(round(float(edit_budgets[i])*100)), False, uuid, edit_e_order[i])
        e.id = present_ids[i]
        envelopes_to_edit.append(e)
    for i in range(len(new_names)):
      new_envelopes.append(Envelope(None, new_names[i], 0, int(round(float(new_budgets[i])*100)), False, uuid, new_e_order[i]))

    toasts = []
    toasts.append(edit_envelopes(uuid, envelopes_to_edit, new_envelopes, present_ids))

    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/api/data-reload', methods=['POST'])
@login_required
@check_confirmed
def data_reload():
  try:
    uuid = get_uuid_from_cookie()
    u = get_user_by_uuid(uuid)
    js_data = request.get_json()
    current_page = js_data['current_page']
    timestamp = js_data['timestamp']
    reload_transactions = js_data['reload_transactions']
    check_pending_transactions(uuid, timestamp) #Apply any pending transactions that need to before rendering the template
    if 'account/' in current_page:
      regex = re.compile('account/(\d+)')
      account_id = int(regex.findall(current_page)[0])
      (transactions_data, offset, limit) = get_account_transactions(uuid,account_id,0,50)
      page_total = balanceformat(get_account(account_id).balance/100)
    elif 'envelope/' in current_page:
      regex = re.compile('envelope/(\d+)')
      envelope_id = int(regex.findall(current_page)[0])
      (transactions_data, offset, limit) = get_envelope_transactions(uuid,envelope_id,0,50)
      page_total = balanceformat(get_envelope(envelope_id).balance/100)
    else:
      current_page = 'All Transactions'
      (transactions_data, offset, limit) = get_home_transactions(uuid,0,50)
      page_total = balanceformat(get_total(uuid))
    (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
    (active_accounts, accounts_data) = get_user_account_dict(uuid)
    data = {}
    data['total'] = get_total(uuid)
    data['unallocated'] = get_envelope_balance(u.unallocated_e_id)/100
    data['accounts_html'] = render_template('accounts.html', active_accounts=active_accounts, accounts_data=accounts_data)
    data['envelopes_html'] = render_template('envelopes.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data, unallocated_e_id=u.unallocated_e_id)
    data['account_selector_html'] = render_template('account_selector.html', accounts_data=accounts_data)
    data['envelope_selector_html'] = render_template('envelope_selector.html', envelopes_data=envelopes_data, unallocated_e_id=u.unallocated_e_id)
    data['envelope_editor_html'] = render_template('envelope_editor.html', envelopes_data=envelopes_data, budget_total=budget_total,  unallocated_e_id=u.unallocated_e_id)
    data['account_editor_html'] = render_template('account_editor.html', accounts_data=accounts_data)
    data['envelope_fill_editor_rows_html'] = render_template('envelope_fill_editor_rows.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data, unallocated_e_id=u.unallocated_e_id)
    data['page_total'] = page_total
    if reload_transactions:
      data['transactions_html'] = render_template(
        'transactions.html',
        current_page=current_page,
        transactions_data=transactions_data,
        envelopes_data=envelopes_data,
        accounts_data=accounts_data,
        offset=offset,
        limit=limit,
        TType=TType
      )
    return jsonify(data)
  except CustomException as e:
    return jsonify({"error": str(e)})

@app.route('/api/load-more', methods=['POST'])
@login_required
@check_confirmed
def load_more():
  try:
    uuid = get_uuid_from_cookie()
    current_offset = request.get_json()['offset']
    current_page = request.get_json()['current_page']
    # TODO: When implementing unit test framework, test what happens if the user somehow manually changes the current_page variable so that it doesn't include a valid account or envelope id
    # TODO: When implementing unit test framework, if the user manually changes the offset variable to something other than a valid integer, the app will crash. Test for this.
    if 'account/' in current_page:
      regex = re.compile('account/(\d+)')
      account_id = int(regex.findall(current_page)[0])
      (transactions_data, offset, limit) = get_account_transactions(uuid,account_id,current_offset,50)
    elif 'envelope/' in current_page:
      regex = re.compile('envelope/(\d+)')
      envelope_id = int(regex.findall(current_page)[0])
      (transactions_data, offset, limit) = get_envelope_transactions(uuid,envelope_id,current_offset,50)
    else:
      (transactions_data, offset, limit) = get_home_transactions(uuid,current_offset,50)

    (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
    (active_accounts, accounts_data) = get_user_account_dict(uuid)
    more_transactions = render_template(
      'more_transactions.html',
      transactions_data=transactions_data,
      accounts_data=accounts_data,
      envelopes_data=envelopes_data,
      current_page=current_page,
      TType = TType
    )
    return jsonify({'offset': offset, 'limit': limit, 'transactions': more_transactions})
  
  except CustomException as e:
      return jsonify({"error": str(e)})

@app.route('/api/multi-delete', methods=['POST'])
@login_required
@check_confirmed
def multi_delete():
  try:
    uuid = get_uuid_from_cookie()
    delete_ids = request.form.getlist('delete')
    # timestamp = date_parse(request.form['timestamp']) #Don't need to check timestamp in this function

    for id in delete_ids:
      delete_transaction(uuid, id)
    
    toasts = []
    if len(delete_ids) == 1:
      toasts.append("Transaction deleted!")
    else:
      toasts.append(f'{len(delete_ids)} transactions deleted!')
    
    health_check(toasts)
    return jsonify({'toasts': toasts})
    
  except CustomException as e:
    return jsonify({"error": str(e)})
  
@app.route('/api/load-static-html', methods=["POST"])
@login_required
@check_confirmed
def load_static_html():
  return jsonify({
    'edit_envelope_row': render_template('edit_envelope_row.html'),
    'edit_account_row': render_template('edit_account_row.html'),
    't_editor_new_env_row': render_template('transaction_editor_new_envelope_row.html')
  })


@app.route('/bug-report', methods=['POST'])
@login_required
@check_confirmed
def bug_report():
  try:
    uuid = get_uuid_from_cookie()
    bug_report_id = generate_uuid()
    name = request.form.get('bug_reporter_name')
    email = request.form.get('bug_reporter_email')
    desc = request.form.get('bug_description')
    timestamp = request.form.get('timestamp')
    screenshot = request.files['screenshot']
    if screenshot.filename == '':
        screenshot = None
    if screenshot:
        allowed_file_extension(screenshot)
        allowed_file_size(screenshot)
        screenshot.filename = secure_filename(screenshot.filename)
        screenshot.save(os.path.join(app.config['UPLOAD_FOLDER'], screenshot.filename))
    else:
        raise InvalidFormDataError("ERROR: Invalid file type for bug report screenshot!")
    
    send_bug_report_email_developer(uuid, name, email, desc, bug_report_id, timestamp, screenshot)  # Send bug report email to the developer
    send_bug_report_email_user(name, email, bug_report_id) # Send confirmation email to the user
    
    return jsonify({'toasts': ["Thank you! Your bug report has been submitted!"]})
  except CustomException as e:
    return jsonify({"error": str(e)})

def send_bug_report_email_developer(uuid, name, email, desc, bug_report_id, timestamp, screenshot):
  msg = Message(f'Budgeteer: Bug Report from {email}', sender=MAIL_USERNAME, recipients=[MAIL_USERNAME])
  if screenshot:
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], screenshot.filename)
    with app.open_resource(file_path) as fp:
      msg.attach(screenshot.filename, "image/png", fp.read())
    os.remove(file_path)
  msg.html = render_template("emails/bug_report_developer.html", uuid=uuid, name=name, email=email, desc=desc, bug_report_id=bug_report_id, timestamp=timestamp)
  mail.send(msg)

def send_bug_report_email_user(name, email, bug_report_id):
  msg = Message('Budgeteer: Your Bug Report Has Been Received', sender=MAIL_USERNAME, recipients=[email])
  msg.html = render_template("emails/bug_report_user.html", name=name, email=email, bug_report_id=bug_report_id)
  mail.send(msg)

def allowed_file_extension(file):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    if '.' in file.filename and file_extension in ALLOWED_EXTENSIONS:
      return True
    else:
      raise InvalidFileTypeError(f"ERROR: Invalid file type .{file_extension} for bug report screenshot!")

def allowed_file_size(file):
    MAX_FILE_SIZE = 1024*1024*10 # 10Mb
    file_data = file.read()
    file_size = len(file_data) # in bytes
    file.seek(0) # Reset the file pointer to the beginning of the file so it can be saved properly
    if file_size >= MAX_FILE_SIZE:
      raise InvalidFileSizeError(f"The file you uploaded is too large! ({round(file_size/(1024*1024), 2)}Mb). Please upload a file smaller than {round(MAX_FILE_SIZE/(1024*1024), 0)}Mb.")

#MAKES SURE DEBUG IS TURNED OFF FOR MAIN DEPLOYMENT
if __name__ == '__main__':
  if app_platform == 'Windows':
      app.run(debug=True)
  else:
    app.run(debug=False)