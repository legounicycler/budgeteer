"""
This file contains functions relevant the GUI, the flask app, and getting data from the browser
This file interacts a lot with the javascript/jQuery running on the site
"""

from flask import Flask, render_template, url_for, request, redirect, jsonify, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from itsdangerous import URLSafeSerializer
import uuid

from database import *
from secret import SECRET_KEY
from forms import *
from datetime import datetime, timedelta
import calendar, re, platform

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
serializer = URLSafeSerializer(app.config['SECRET_KEY'])

def generate_uuid():
  return str(uuid.uuid4())

def set_secure_cookie(response, key, value):
  encrypted_value = serializer.dumps(value)
  response.set_cookie(key, encrypted_value, httponly=True, secure=True, max_age=30*24*60*60) #Make age is 30 days
  return response

def retrieve_uuid():
  encrypted_uuid = request.cookies.get('uuid')
  if encrypted_uuid:
    return serializer.loads(encrypted_uuid)    
  else:
    return None

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(uuid):
  return get_user_by_uuid(uuid)

@app.route("/")
@app.route('/login', methods=["POST", "GET"])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('home'))
  else:
    login_form = LoginForm()
    register_form = RegisterForm()
    return render_template('login.html',login_form=login_form, register_form=register_form)
  
@app.route('/api/login', methods=["POST", "GET"])
def api_login():
  if current_user.is_authenticated:
    return jsonify({'login_success': True})
  
  form = LoginForm()
  email = form.email.data
  password = form.password.data
  if email is not None:
    user = get_user_by_email(email)
    if user is not None:
      if user.check_password(password):
        login_user(user, remember=False) # Swap to this eventually: login_user(user, remember=form.remember_me.data)
        response = make_response(jsonify({'login_success': True}))
        return set_secure_cookie(response, 'uuid', user.id) # Set the encrypted uuid cookie on the user's browser
      else:
        return jsonify({'message': 'Incorrect password!', 'login_success': False})
    else:
      return jsonify({'message': 'No user with that email exists!', 'login_success': False})
  else:
    return jsonify({'message': "FORM VALIDATION ERROR (Shouldn't be possible)", 'login_success': False})

@app.route("/register", methods=["POST", "GET"])
def register():
  form = RegisterForm()
  new_email = form.new_email.data
  new_password = form.new_password.data
  new_first_name = form.new_first_name.data
  new_last_name = form.new_last_name.data

  # 1. Check if user with that email already exists
  if get_user_by_email(new_email) is not None:
    return jsonify({'message': 'A user with that email already exists!', 'login_success': False})

  # 2. Check the password validation
  if form.new_password.validate(form) and form.confirm_password.validate(form):
    uuid = generate_uuid()
    (new_password_hash, new_password_salt) = hash_password(new_password)
    new_user = User(uuid, new_email, new_password_hash, new_password_salt, new_first_name, new_last_name)
    insert_user(new_user)
    login_user(new_user, remember=False) # Swap to this eventually: login_user(user, remember=form.remember_me.data)
    response = make_response(jsonify({'login_success': True}))
    return set_secure_cookie(response, 'uuid', new_user.id) # Set the encrypted uuid cookie on the user's browser
  else:
    return jsonify({'message': 'Passwords must match!', 'login_success': False})

@app.route('/logout')
def logout():
  if current_user.is_authenticated:
    logout_user()
  return redirect(url_for('login'))


# TODO: Make this a global filter instead
t_type_dict = {
  0: 'Basic Transaction',
  1: 'Envelope Transfer',
  2: 'Account Transfer',
  3: 'Income',
  4: 'Split Transaction',
  5: 'Envelope Fill',
  6: 'Envelope Delete',
  7: 'Account Delete',
  8: 'Account Adjust'
}

# TODO: Make this a global filter instead
t_type_icon_dict = {
  0: 'local_atm',
  1: 'swap_horiz',
  2: 'swap_vert',
  3: 'vertical_align_bottom',
  4: 'call_split',
  5: 'input',
  6: 'layers_clear',
  7: 'money_off',
  8: 'build'
}

def datetimeformat(value, format='%m/%d/%Y'):
  return value.strftime(format)

def datetimeformatshort(value, format='%b %d\n%Y'):
  return value.strftime(format)

def inputformat(num):
  return '%.2f' % num

def add_months(sourcedate, months):
  """
  Adds an integer amount of months to a given date.
  Returns the new date.
  """
  month = sourcedate.month - 1 + months
  year = sourcedate.year + month // 12
  month = month % 12 + 1
  day = min(sourcedate.day, calendar.monthrange(year,month)[1])
  return date(year, month, day)

def schedule_date_calc(tdate, schedule, timestamp):
  """
  Calculates the upcoming transaction date for a scheduled transaction based on its frequency and the user's timestamp.
  Returns the date of the next transaction.
  """
  date_is_pending = False
  while not date_is_pending:
    if (schedule=="daily"):
      nextdate = tdate + timedelta(days=1)
    elif (schedule=="weekly"):
      nextdate = tdate + timedelta(days=7)
    elif (schedule=="biweekly"):
      nextdate = tdate + timedelta(days=14)
    elif (schedule=="monthly"):
      nextdate = add_months(tdate,1)
    elif (schedule=="endofmonth"):
      lastmonthday = calendar.monthrange(tdate.year, tdate.month)[1]
      if (tdate.day == lastmonthday):
        nextdate = add_months(tdate,1)
      else:
        nextdate = date(tdate.year, tdate.month, lastmonthday)
    elif (schedule=="semianually"):
      nextdate = add_months(tdate,6)
    elif (schedule=="anually"):
      nextdate = add_months(tdate,12)
    else:
      log_write("ERROR: Invalid schedule option!")
      return False #TODO: Throw error here instead
    
    nextdate = datetime.combine(nextdate, datetime.min.time())
    if nextdate > timestamp:
      date_is_pending = True
    else:
      tdate = nextdate

  return nextdate

def is_pending(date, timestamp):
  if date > timestamp:
    return True
  else:
    return False

app.jinja_env.filters['datetimeformat'] = datetimeformat
app.jinja_env.filters['datetimeformatshort'] = datetimeformatshort
app.jinja_env.filters['balanceformat'] = balanceformat
app.jinja_env.filters['inputformat'] = inputformat

@app.route("/home", methods=['GET'])
@login_required
def home():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify("ERROR: No uuid cookie found!")
  
  (transactions_data, offset, limit) = get_home_transactions(uuid,0,50)
  (active_envelopes, envelopes_data, budget_total) = get_envelope_dict(uuid)
  (active_accounts, accounts_data) = get_account_dict(uuid)
  total_funds = get_total(uuid)
  return render_template(
    'layout.html',
    current_page='All transactions',
    t_type_dict=t_type_dict,
    t_type_icon_dict=t_type_icon_dict,
    active_envelopes=active_envelopes,
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
    last_name=current_user.last_name
  )

@app.route("/get_envelope_page", methods=["POST"])
@login_required
def get_envelope_page():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify("ERROR: No uuid cookie found!")
  
  envelope_id = request.get_json()['envelope_id']
  current_page = f'envelope/{envelope_id}'
  (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,0,50)
  (active_envelopes, envelopes_data, budget_total) = get_envelope_dict(uuid)
  (active_accounts, accounts_data) = get_account_dict(uuid)
  page_total = balanceformat(get_envelope(envelope_id).balance/100)
  data = {}
  data['transactions_html'] = render_template('transactions.html', current_page=current_page, t_type_dict=t_type_dict, t_type_icon_dict=t_type_icon_dict, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
  data['page_total'] = page_total
  data['envelope_name'] = get_envelope(envelope_id).name
  return jsonify(data)

@app.route("/get_account_page", methods=["POST"])
@login_required
def get_account_page():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify("ERROR: No uuid cookie found!")
  
  account_id = request.get_json()['account_id']
  current_page = f'account/{account_id}'
  (transactions_data, offset, limit) = get_account_transactions(account_id,0,50)
  (active_envelopes, envelopes_data, budget_total) = get_envelope_dict(uuid)
  (active_accounts, accounts_data) = get_account_dict(uuid)
  page_total = balanceformat(get_account(account_id).balance/100)
  data = {}
  data['transactions_html'] = render_template('transactions.html', current_page=current_page, t_type_dict=t_type_dict, t_type_icon_dict = t_type_icon_dict, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
  data['page_total'] = page_total
  data['account_name'] = get_account(account_id).name
  return jsonify(data)

@app.route('/new_expense', methods=['POST'])
@login_required
def new_expense(edited=False):
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"], 'success': False})
  
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
  success = True

  try: 
    for i in range(len(amounts)):
      amounts[i] = int(round(float(amounts[i]) * 100))
      envelope_ids[i] = int(envelope_ids[i])
  except:
    toasts.append("An error occurred, and your request was not processed!")
    log_write("ERROR: Bad form data!")
    success = False
  else:
    for name in names:
      t = Transaction(BASIC_TRANSACTION, name, amounts, date, envelope_ids, account_id, None, note, None, False, uuid, pending)
      if scheduled and not pending:
        # Create pending scheduled transaction
        nextdate = schedule_date_calc(date, schedule, timestamp)
        scheduled_t = Transaction(BASIC_TRANSACTION, name, amounts, nextdate, envelope_ids, account_id, None, note, schedule, False, uuid, is_pending(nextdate, timestamp))
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
        t.type = SPLIT_TRANSACTION
        new_split_transaction(t)
        if scheduled and not pending:
          scheduled_t.type = SPLIT_TRANSACTION
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
        toasts.append('There was an error!')

  if (health_check() is False):
    toasts.append("HEALTH ERROR!")
  return jsonify({'toasts': toasts, 'success': success})

@app.route('/new_transfer', methods=['POST'])
@login_required
def new_transfer(edited=False):
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"], 'success': False})
  
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
  success = True

  try:
    amount = int(round(float(request.form['amount'])*100))
  except:
    toasts.append("An error occurred, and your request was not processed!")
    log_write("ERROR: Bad form data!")
    success = False
  else:
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
          nextdate = schedule_date_calc(date, schedule, timestamp)
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
          nextdate = schedule_date_calc(date, schedule, timestamp)
          envelope_transfer(name, amount, nextdate, to_envelope, from_envelope, note, schedule, uuid, is_pending(nextdate, timestamp))
          sched_t_submitted = True
        else:
          # Create transfer WITHOUT schedule
          envelope_transfer(name, amount, date, to_envelope, from_envelope, note, None, uuid, pending)
      else:
        log_write(f"ERROR: '{transfer_type}' isn't a valid transfer type, you twit!")

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
        toasts.append('There was an error!')

  if (health_check() is False):
    toasts.append("HEALTH ERROR!")
  return jsonify({'toasts': toasts, 'success': success})

@app.route('/new_income', methods=['POST'])
@login_required
def new_income(edited=False):
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"], 'success': False})
  
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
  success = True

  try:
    amount = int(round(float(request.form['amount'])*100))
  except:
    toasts.append("An error occurred, and your request was not processed!")
    log_write("ERROR: Bad form data!")
    success = False
  else:
    for name in names:
      t = Transaction(INCOME, name, -1 * amount, date, UNALLOCATED, account_id, gen_grouping_num(), note, None, False, uuid, pending)
      if scheduled and not pending:
        insert_transaction(t)
        nextdate = schedule_date_calc(date, schedule, timestamp)
        scheduled_t = Transaction(INCOME, name, -1 * amount, nextdate, 1, account_id, gen_grouping_num(), note, schedule, False, uuid, is_pending(nextdate, timestamp))
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
        toasts.append('There was an error!')

  if (health_check() is False):
    toasts.append("HEALTH ERROR!")
  return jsonify({'toasts': toasts, 'success': success})

@app.route('/fill_envelopes', methods=['POST'])
@login_required
def fill_envelopes(edited=False):
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"], 'success': False})
  
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
  success = True
   
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
    toasts.append("An error occurred, and your request was not processed!")
    log_write("ERROR: Bad form data!")
    success = False
  else:
    if amounts:
      for name in names:
        t = Transaction(ENVELOPE_FILL, name, amounts, date, envelope_ids, None, None, note, None, False, uuid, pending)
        if scheduled and not pending:
          envelope_fill(t)
          nextdate = schedule_date_calc(date, schedule, timestamp)
          scheduled_t = Transaction(ENVELOPE_FILL, name, amounts, nextdate, envelope_ids, None, None, note, schedule, False, uuid, is_pending(nextdate, timestamp))
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
          toasts.append('There was an error!')
    else:
      toasts.append("No envelope fill was created!")

  if (health_check() is False):
    toasts.append("HEALTH ERROR!")
  return jsonify({'toasts': toasts, 'success': success})

@app.route('/edit_delete_envelope', methods=['POST'])
def edit_delete_envelope():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"], 'success': False})
  
  name = request.form['name']
  note = request.form['note']
  date = datetime.strptime(request.form['date'], "%m/%d/%Y")
  envelope_id = request.form['envelope_id']
  # timestamp = date_parse(request.form['timestamp']) #Don't need to check timestamp in this function
  toasts = []
  success = True

  # A copy of the delete_envelope() function from database.py but with the info from the form pasted in
  with conn:
    if (envelope_id != UNALLOCATED): #You can't delete the unallocated envelope
      e = get_envelope(envelope_id)
      grouping = gen_grouping_num()
      # 1. Empty the deleted envelope
      t_envelope = Transaction(ENVELOPE_DELETE, name, e.balance, date, envelope_id, None, grouping, note, None, 0, uuid, False)
      insert_transaction(t_envelope)
      # 2. Fill the unallocated envelope
      t_unallocated = Transaction(ENVELOPE_DELETE, name, -1*e.balance, date, UNALLOCATED, None, grouping, note, None, 0, uuid, False)
      insert_transaction(t_unallocated)
      # 3. Mark the envelope as deleted
      c.execute("UPDATE envelopes SET deleted=1 WHERE id=?", (envelope_id,))
      toasts.append("Transaction updated!")
      log_write('E DELETE: ' + str(get_envelope(envelope_id)))
    else:
      log_write("ERROR: You can't delete the 'Unallocated' envelope you moron")
      toasts.append("Something went wrong, and your transaction was not processed!")
      success = False

    if (health_check() is False):
      toasts.append("HEALTH ERROR!")
    return jsonify({'toasts': toasts, 'success': success})

# TODO: Revisit this. There's probably no need to delete and recreate the transaction. Test to see what happens if you directly
#       update the transaction details in the database
@app.route('/edit_delete_account', methods=['POST'])
def edit_delete_account():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"], 'success': False})
  
  name = request.form['name']
  note = request.form['note']
  date = datetime.strptime(request.form['date'], "%m/%d/%Y")
  account_id = request.form['account_id']
  # timestamp = date_parse(request.form['timestamp']) #Don't need to check timestamp in this function
  toasts = []
  success = True
  
  # A copy of the delete_account() function from database.py but with the info from the form pasted in
  with conn:
    a = get_account(account_id)
    
    # 1. Empty the deleted account
    insert_transaction(Transaction(ACCOUNT_DELETE, name, a.balance, date, UNALLOCATED, a.id, gen_grouping_num(), note, None, 0, uuid, False))

    # 2. Mark the account as deleted
    c.execute("UPDATE accounts SET deleted=1 WHERE id=?", (account_id,))
    toasts.append("Transaction updated!")
    log_write('A DELETE: ' + str(get_account(account_id)))

  if (health_check() is False):
    toasts.append("HEALTH ERROR!")
  return jsonify({'toasts': toasts, 'success': success})

@app.route('/edit_account_adjust', methods=['POST'])
def edit_account_adjust():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"], 'success': False})
  
  name = request.form['name']
  date = datetime.strptime(request.form['date'], "%m/%d/%Y")
  note = request.form['note']
  account_id = int(request.form['account_id'])
  timestamp = date_parse(request.form['timestamp'])
  toasts = []
  success = True

  try:
    balance_diff = int(round(float(request.form['amount'])*100))
  except:
    toasts.append("An error occurred, and your request was not processed!")
    log_write("ERROR: Bad form data!")
    success = False
  else:
    insert_transaction(Transaction(ACCOUNT_ADJUST, name, -1*balance_diff, date, UNALLOCATED, account_id, gen_grouping_num(), note, None, False, uuid, is_pending(date, timestamp)))
    toasts.append("Transaction updated!")

  if (health_check() is False):
    toasts.append("HEALTH ERROR!")
  return jsonify({'toasts': toasts, 'success': success})

@app.route('/edit_transaction', methods=['POST'])
@login_required
def edit_transaction():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify("ERROR: No uuid cookie found!")
  
  id = int(request.form['edit-id'])
  type = int(request.form['type'])
    
  if (type == BASIC_TRANSACTION):
    response = new_expense(True)
  elif (type == ENVELOPE_TRANSFER or type == ACCOUNT_TRANSFER):
    response =  new_transfer(True)
  elif (type == INCOME):
    response = new_income(True)
  elif (type == SPLIT_TRANSACTION):
    response = new_expense(True)
  elif (type == ENVELOPE_FILL):
    response = fill_envelopes(True)
  elif (type == ENVELOPE_DELETE):
    response = edit_delete_envelope()
  elif (type == ACCOUNT_DELETE):
    response = edit_delete_account()
  elif (type == ACCOUNT_ADJUST):
    response =  edit_account_adjust()

  if response.json['success']:
    delete_success = delete_transaction(uuid, id) #Only delete the original transaction if you were successful in creating the replacement edited transaction
    if not delete_success:
      log_write("ERROR: Failed to delete original transaction after editing!")
      response.json['toasts'] = ["An error occurred, and your request was not processed!"]
      response.json['success'] = False
  return response


@app.route('/delete_transaction_page', methods=['POST'])
@login_required
# TODO: Change this to use an <id> in the URL instead of using the hidden form thing (SEE get_json). Also probably rename this to not say "page"
def delete_transaction_page():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify("ERROR: No uuid cookie found!")
  
  id = int(request.form['delete-id'])
  # timestamp = date_parse(request.form['timestamp']) #Don't need to check timestamp in this function
  success = delete_transaction(uuid, id)
  if success:
    return jsonify({'toasts': ['Transaction deleted!']})
  else:
    return jsonify({'toasts': ['An error occurred, and your request was not processed!']})

# TODO: Once the login system is implemented, this whole page will no longer be needed, since all check_pending_request() calls will be in /home or /data-reload
@app.route('/api/check_pending_transactions', methods=['POST'])
@login_required
def check_pending_request():
  timestamp = request.get_json()['timestamp']
  return jsonify({'should_reload': check_pending_transactions(timestamp)})

@app.route('/api/transaction/<id>/group', methods=['GET'])
@login_required
def get_json(id): #TODO: Should this be get_grouped_json??? This doesn't seem to get called anywhere, nor does get_grouped_json()
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({"success": False})
  
  return jsonify(get_grouped_ids_from_id(uuid,id))
  

@app.route('/api/edit-accounts', methods=['POST'])
@login_required
def edit_accounts_page():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"]})
  
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

  original_a_order = get_account_order()
  accounts_to_edit = []
  new_accounts = []
  for i in range(len(present_ids)):
    if (edit_names[i] != original_names[i] or edit_balances[i] != original_balances[i] or edit_a_order[i] != original_a_order[present_ids[i]]):
      a = Account(edit_names[i], int(round(float(edit_balances[i])*100)), False, uuid, edit_a_order[i])
      a.id = present_ids[i]
      accounts_to_edit.append(a)
  for i in range(len(new_names)):
    new_accounts.append(Account(new_names[i], int(round(float(new_balances[i])*100)), False, uuid, new_a_order[i]))

  toasts = []
  toasts.append(edit_accounts(accounts_to_edit, new_accounts, present_ids, timestamp)) #From the account editor form, there is no date field, so use timestamp for date of transaction

  if (health_check() is False):
    toasts.append(" HEALTH ERROR!!!")
  return jsonify({'toasts': toasts})

@app.route('/api/edit-envelopes', methods=['POST'])
@login_required
def edit_envelopes_page():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({'toasts': ["ERROR: No uuid cookie found!"]})
  
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

  original_e_order = get_envelope_order()
  envelopes_to_edit = []
  new_envelopes = []
  for i in range(len(present_ids)):
    if (edit_names[i] != original_names[i] or edit_budgets[i] != original_budgets[i] or edit_e_order[i] != original_e_order[present_ids[i]]): #
      e = Envelope(edit_names[i], int(round(float(envelope_balances[i])*100)), int(round(float(edit_budgets[i])*100)), False, uuid, edit_e_order[i])
      e.id = present_ids[i]
      envelopes_to_edit.append(e)
  for i in range(len(new_names)):
    new_envelopes.append(Envelope(new_names[i], 0, int(round(float(new_budgets[i])*100)), False, uuid, new_e_order[i]))

  toasts = []
  toasts.append(edit_envelopes(envelopes_to_edit, new_envelopes, present_ids))

  if (health_check() is False):
    toasts.append("HEALTH ERROR!")
  return jsonify({'toasts': toasts})

@app.route('/api/data-reload', methods=['POST'])
@login_required
def data_reload():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({"success": False, "toast": 'UUID cookie not found!'})
  
  js_data = request.get_json()
  current_page = js_data['current_page']
  timestamp = js_data['timestamp']
  check_pending = js_data['check_pending']
  reload_transactions = js_data['reload_transactions']
  if check_pending:
    check_pending_transactions(timestamp) #Apply any pending transactions that need to before rendering the template
  if 'account/' in current_page:
    regex = re.compile('account/(\d+)')
    account_id = int(regex.findall(current_page)[0])
    (transactions_data, offset, limit) = get_account_transactions(account_id,0,50)
    page_total = balanceformat(get_account(account_id).balance/100)
  elif 'envelope/' in current_page:
    regex = re.compile('envelope/(\d+)')
    envelope_id = int(regex.findall(current_page)[0])
    (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,0,50)
    page_total = balanceformat(get_envelope(envelope_id).balance/100)
  else:
    current_page = 'All Transactions'
    (transactions_data, offset, limit) = get_home_transactions(uuid,0,50)
    page_total = get_total(uuid)
  (active_envelopes, envelopes_data, budget_total) = get_envelope_dict(uuid)
  (active_accounts, accounts_data) = get_account_dict(uuid)
  data = {}
  if reload_transactions:
    data['transactions_html'] = render_template('transactions.html', current_page=current_page, t_type_dict=t_type_dict, t_type_icon_dict = t_type_icon_dict, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
  data['total'] = get_total(uuid)
  data['unallocated'] = envelopes_data[1].balance
  data['accounts_html'] = render_template('accounts.html', active_accounts=active_accounts, accounts_data=accounts_data)
  data['envelopes_html'] = render_template('envelopes.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data)
  data['account_selector_html'] = render_template('account_selector.html', accounts_data=accounts_data)
  data['envelope_selector_html'] = render_template('envelope_selector.html', envelopes_data=envelopes_data)
  data['envelope_editor_html'] = render_template('envelope_editor.html', envelopes_data=envelopes_data, budget_total=budget_total)
  data['account_editor_html'] = render_template('account_editor.html', accounts_data=accounts_data)
  data['envelope_fill_editor_rows_html'] = render_template('envelope_fill_editor_rows.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data)
  data['page_total'] = page_total
  data['success'] = True
  return jsonify(data)

@app.route('/api/load-more', methods=['POST'])
@login_required
def load_more():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({"success": False, "toast": 'UUID cookie not found!'})
  
  current_offset = request.get_json()['offset']
  current_page = request.get_json()['current_page']
  if 'account/' in current_page:
    regex = re.compile('account/(\d+)')
    account_id = int(regex.findall(current_page)[0])
    (transactions_data, offset, limit) = get_account_transactions(account_id,current_offset,50)
  elif 'envelope/' in current_page:
    regex = re.compile('envelope/(\d+)')
    envelope_id = int(regex.findall(current_page)[0])
    (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,current_offset,50)
  else:
    (transactions_data, offset, limit) = get_home_transactions(uuid,current_offset,50)

  # TODO: these 2 lines shouldn't be necessary here after updating to a join clause
  (active_envelopes, envelopes_data, budget_total) = get_envelope_dict(uuid)
  (active_accounts, accounts_data) = get_account_dict(uuid)
  more_transactions = render_template('more_transactions.html', t_type_dict=t_type_dict, t_type_icon_dict = t_type_icon_dict, transactions_data=transactions_data, accounts_data=accounts_data, envelopes_data=envelopes_data, current_page=current_page)
  return jsonify({'offset': offset, 'limit': limit, 'transactions': more_transactions, 'success': True})

@app.route('/api/multi-delete', methods=['POST'])
@login_required
def multi_delete():
  uuid = retrieve_uuid()
  if uuid is None:
    return jsonify({"success": False, "toast": 'UUID cookie not found!'})
  
  delete_ids = request.form.getlist('delete')
  # timestamp = date_parse(request.form['timestamp']) #Don't need to check timestamp in this function
  for id in delete_ids:
    delete_transaction(uuid, id)
    success = delete_transaction(uuid, id)
  if success:
    toasts = []
    if len(delete_ids) == 1:
      toasts.append("Transaction deleted!")
    else:
      toasts.append(f'{len(delete_ids)} transactions deleted!')
    if (health_check() is False):
      toasts.append("HEALTH ERROR!")
    return jsonify({'toasts': toasts})
  else:
    return jsonify({'toasts': ['An error occurred, and your request was not processed!']})

  

@app.route('/api/load-static-html', methods=["POST"])
def load_static_html():
  return jsonify({
    'edit_envelope_row': render_template('edit_envelope_row.html'),
    'edit_account_row': render_template('edit_account_row.html'),
    't_editor_new_env_row': render_template('transaction_editor_new_envelope_row.html')
  })

#MAKES SURE DEBUG IS TURNED OFF FOR MAIN DEPLOYMENT
if __name__ == '__main__':
  platform = platform.system()
  if platform == 'Windows':
      app.run(debug=True)
  else:
    app.run(debug=False)
  
