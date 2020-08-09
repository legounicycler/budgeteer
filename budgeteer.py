  # FEATURES TO ADD
  #
  # DEVELOP UNIT TESTS FOR WHEN PUSHING UPDATES
  #
  # -----USER EXPERIENCE ENHANCEMENTS-----
  # Disable autocomplete (autocomplete="off") on mobile
  # clear multi transaction selection with escape key or some other tap on mobile?
  # Draggable order for transactions with same date
  # Add keyboard-tab select function on materialize select so that it's more user friendly
  # "Submit and new" button for faster transaction creations
  # Quick fill for envelopes based on budget
  # Overlay scrollbar (simplebar?)
  # shift select on multiselect checkboxes
  # autofill envelope/account on transaction creation if you're on that envelope/account page
  #
  # -----ACTUAL FEATURES-----
  # Account balance next to transaction amount
  # Reorderable envelopes
  # Icons on envelopes
  # Hoverable note function
  # Placeholder transactions (for deleted/edited accounts/envelopes)
  # Import transactions from bank
  # Specific number of instances for scheduled transactions
  # Transaction search/sort (multiple ways date, amount, name, etc.)
  # Accounts/login functions
  # Spending graphs/budgeting tracking
  # Report a bug feature for users (probably using formspree)
  # Cash back feature
  # Photo of recipt (maybe until reconciled)
  # Total envelope budget (on envelope editor) (monthly or biweekly??)
  #
  #
  # -----BUG LIST-----
  # Scheduled transactions don't create new scheduled transactions! (nightly.py?)
  # Future transaction on the next day doesn't show up as gray. (Time was 9:51 on July 27, 2020, transaction was set for July 28)
  # Strange scrolling glitch with long selects by changing the container of
  #     the select from body to something under the nav bar? (CAN'T REPRODUCE??)
  # Arrow keys don't work in selects
  # Clicking another input field after an unselected select requires 2 clicks
  #
  # -----THINGS TO MAYBE DO-----
  # Split envelope transfer?
  # inline math
  # some kind of venmo feature?
  # abort ajax request (loading spinner page would have an 'x')
  # Update get_transactions to use join clause for account_name and deleted info
  # fix template structure for transactions and envelope/selectors
  # customization of date option
  # replace the jquery weird find structures with .closest()
  # Link to other transactions in descriptions??
  # quick edit on date for reconciling?
  # envelope average spending /spent last month
  # Saving goals (how much to put in an envelope each week to reach
  # a goal balance by a ceratin date)
  # cover overspending button
  # average spent in each envelope
  # one click reconcile button
  # Show both accounts/envelopes on transaction list for transfers (with an arrow)
  # use join clause on get_trasactions() to get account name and envelope name
  #     This might mot actually be more efficient unless I add a feature where
  #     there's a current account balance associated with every transaction
  # Scheduled transactions documentation
  # redo css structure to get rid of !important tags

from flask import Flask, render_template, url_for, request, redirect, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import *
from datetime import datetime
from datetime import timedelta
import calendar
import re
import platform

app = Flask(__name__)
app.config['SECRET_KEY'] = 'totallysecretkey'

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):

  def __init__(self,email,password_hash,first_name,last_name):
    self.password_hash = password_hash
    self.email = email
    self.id = self.email
    self.first_name = first_name
    self.last_name = last_name

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def __repr__(self):
    return '<User {}>'.format(self.email)

@app.route("/create_account", methods=["POST", "GET"])
def create_account():
  new_email = request.form['new_email']
  new_password = request.form['new_password']
  new_new_password = request.form['new_new_password']
  new_first_name = request.form['new_first_name']
  new_last_name = request.form['new_last_name']
  data = {}
  if new_password == new_new_password:
    # If new_email is not unique, display error message
    u = User(new_email, generate_password_hash(new_password), new_first_name, new_last_name)
    insert_user(u)
    data['message'] = None
    data['login'] = True
    login_user(u, remember=False)
  else:
    data['message'] = 'INVALID'
    data['login'] = False
  return jsonify(data)


@login_manager.user_loader
def load_user(email):
  return get_user(email)

@app.route("/")
@app.route('/login', methods=["POST", "GET"])
def login():
  data = {}
  if current_user.is_authenticated:
    print("User already authenticated")
    return redirect(url_for('home'))
  try:
    email = request.form['email']
    password = request.form['password']
  except:
    return redirect(url_for('login_page'))
  user = load_user(email)
  user.password = password
  print(user.password)
  if user is None:
    data['message'] = 'USER DOES NOT EXIST'
    data['login'] = False
    return jsonify(data)
  elif not user.check_password(password):
    data['message'] = 'INCORRECT PASSWORD'
    data['login'] = False
    return jsonify(data)
  else:
    login_user(user, remember=False) # Swap to this eventually: login_user(user, remember=form.remember_me.data)
    data['message'] = None
    data['login'] = True
    return jsonify(data)


@app.route('/login-page', methods=["POST", "GET"])
def login_page():
  return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
  if current_user.is_authenticated:
    logout_user()
  return redirect(url_for('login'))


USER_ID = 1

t_type_dict = {
  0: 'Basic Transaction',
  1: 'Envelope Transfer',
  2: 'Account Transfer',
  3: 'Income',
  4: 'Split Transaction',
  5: 'Envelope Fill'
}

t_type_dict2 = {
  0: 'local_atm',
  1: 'swap_horiz',
  2: 'swap_vert',
  3: 'vertical_align_bottom',
  4: 'call_split',
  5: 'input'
}

def datetimeformat(value, format='%m/%d/%Y'):
  return value.strftime(format)

def datetimeformatshort(value, format='%b %d\n%Y'):
  return value.strftime(format)

def add_months(sourcedate, months):
  month = sourcedate.month - 1 + months
  year = sourcedate.year + month // 12
  month = month % 12 + 1
  day = min(sourcedate.day, calendar.monthrange(year,month)[1])
  return date(year, month, day)

def schedule_date_calc(tdate, schedule):
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
  nextdate = datetime.combine(nextdate, datetime.min.time())
  return nextdate

app.jinja_env.filters['datetimeformat'] = datetimeformat
app.jinja_env.filters['datetimeformatshort'] = datetimeformatshort

@app.route("/home", methods=['GET'])
@login_required
def home():
  (transactions_data, offset, limit) = get_transactions(0,50)
  (active_envelopes, envelopes_data) = get_envelope_dict()
  (active_accounts, accounts_data) = get_account_dict()
  total_funds = get_total(USER_ID)
  current_view = 'All transactions'
  current_total = total_funds
  return render_template('layout.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view, current_total=current_total, offset=offset, limit=limit, email=current_user.email, first_name=current_user.first_name, last_name=current_user.last_name)

@app.route("/get_envelope_page", methods=["POST"])
@login_required
def get_envelope_page():
  envelope_id = request.get_json()['envelope_id']
  (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,0,50)
  (active_envelopes, envelopes_data) = get_envelope_dict()
  (active_accounts, accounts_data) = get_account_dict()
  page_total = stringify(get_envelope(envelope_id).balance)
  data = {}
  data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
  data['page_total'] = page_total
  data['envelope_name'] = get_envelope(envelope_id).name
  return jsonify(data)

@app.route("/get_account_page", methods=["POST"])
@login_required
def get_account_page():
  account_id = request.get_json()['account_id']
  (transactions_data, offset, limit) = get_account_transactions(account_id,0,20)
  (active_envelopes, envelopes_data) = get_envelope_dict()
  (active_accounts, accounts_data) = get_account_dict()
  page_total = stringify(get_account(account_id).balance)
  data = {}
  data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
  data['page_total'] = page_total
  data['account_name'] = get_account(account_id).name
  return jsonify(data)

@app.route('/new_expense', methods=['POST'])
@login_required
def new_expense(edited=False):
  # edited=True if this is called from edit_transaction
  name = request.form['name']
  amounts = request.form.getlist('amount')
  envelope_ids = request.form.getlist('envelope_id')
  account_id = request.form['account_id']
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  note = request.form['note']
  scheduled = request.form.getlist('scheduled')
  scheduled = len(scheduled) != 0
  schedule = request.form['schedule']
  scheduled_transaction_submitted = False
  for i in range(len(amounts)):
    amounts[i] = int(round(float(amounts[i]) * 100))
    envelope_ids[i] = int(envelope_ids[i])
  t = Transaction(BASIC_TRANSACTION, name, amounts, date, envelope_ids, account_id, None, note, None, False, USER_ID, None)
  # Only insert a NEW scheduled transaction if it's not an edited transaction
  if scheduled and edited:
    t.schedule = schedule
  if scheduled and not edited:
    # Create placeholder scheduled transaction
    nextdate = schedule_date_calc(date,schedule)
    scheduled_t = Transaction(BASIC_TRANSACTION, name, amounts, nextdate, envelope_ids, account_id, None, note, schedule, False, USER_ID, None)

  # If it is a single transaction
  if len(envelope_ids) == 1:
    t.grouping = gen_grouping_num()
    t.envelope_id = envelope_ids[0]
    t.amt = amounts[0]
    # insert new transaction without schedule
    insert_transaction(t)
    if scheduled and not edited:
      # update placeholder scheduled transaction
      scheduled_t.grouping = gen_grouping_num()
      scheduled_t.envelope_id = envelope_ids[0]
      scheduled_t.amt = amounts[0]
      # insert new transaction with schedule
      insert_transaction(scheduled_t)
      scheduled_transaction_submitted = True
  else:
    t.type = SPLIT_TRANSACTION
    new_split_transaction(t)
    if scheduled and not edited:
      # insert new split transaction with schedule
      scheduled_t.type = SPLIT_TRANSACTION
      new_split_transaction(scheduled_t)
      scheduled_transaction_submitted = True
  return jsonify({'message': 'Successfully added new expense!', 'scheduled_transaction_submitted': scheduled_transaction_submitted})

@app.route('/new_transfer', methods=['POST'])
@login_required
def new_transfer(edited=False):
  # edited=True if this is called from edit_transaction
  transfer_type = int(request.form['transfer_type'])
  name = request.form['name']
  amount = int(round(float(request.form['amount'])*100))
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  note = request.form['note']
  scheduled = request.form.getlist('scheduled')
  scheduled = len(scheduled) != 0
  schedule = request.form['schedule']
  scheduled_transaction_submitted = False
  if (transfer_type == 2):
    to_account = request.form['to_account']
    from_account = request.form['from_account']
    # Only insert a new scheduled transaction if it's not edited
    if scheduled and edited:
      # Update schedule of edited transaction, but don't make new scheduled transaction
      account_transfer(name, amount, date, to_account, from_account, note, schedule, USER_ID)
    elif scheduled and not edited:
      # Add in the new transaction, then add in the scheduled transaction
      account_transfer(name, amount, date, to_account, from_account, note, None, USER_ID)
      nextdate = schedule_date_calc(date,schedule)
      account_transfer(name, amount, nextdate, to_account, from_account, note, schedule, USER_ID)
      scheduled_transaction_submitted = True
    else:
      # Add in a normal non-scheduled transaction
      account_transfer(name, amount, date, to_account, from_account, note, None, USER_ID)
  elif (transfer_type == 1):
    to_envelope = request.form['to_envelope']
    from_envelope = request.form['from_envelope']
    # Only insert a new scheduled transaction if it's not edited
    if scheduled and edited:
      # Update schedule of edited transaction, but don't make new scheduled transaction
      envelope_transfer(name, amount, date, to_envelope, from_envelope, note, schedule, USER_ID)
    elif scheduled and not edited:
      # Add in the new transaction, then add in the scheduled transaction
      envelope_transfer(name, amount, date, to_envelope, from_envelope, note, None, USER_ID)
      nextdate = schedule_date_calc(date,schedule)
      envelope_transfer(name, amount, nextdate, to_envelope, from_envelope, note, schedule, USER_ID)
      scheduled_transaction_submitted = True
    else:
      # If there's no schedule, add in the normal non-scheduled transaction
      envelope_transfer(name, amount, date, to_envelope, from_envelope, note, None, USER_ID)
  else:
    print('What the heck are you even trying to do you twit?')
  return jsonify({'message': 'Successfully added new transfer!', 'scheduled_transaction_submitted': scheduled_transaction_submitted})


@app.route('/new_income', methods=['POST'])
@login_required
def new_income(edited=False):
  name = request.form['name']
  amount = int(round(float(request.form['amount'])*100))
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  account_id = request.form['account_id']
  note = request.form['note']
  scheduled = request.form.getlist('scheduled')
  scheduled = len(scheduled) != 0
  schedule = request.form['schedule']
  scheduled_transaction_submitted = False
  t = Transaction(INCOME, name, -1 * amount, date, 1, account_id, gen_grouping_num(), note, None, False, USER_ID, None)

  # Only insert NEW scheduled transaction if it's not edited
  if scheduled and edited:
    t.schedule = schedule
    # Insert transaction with edited schedule
    insert_transaction(t)
  elif scheduled and not edited:
    # Insert transaction with no schedule
    insert_transaction(t)
    # Insert scheduled transaction
    nextdate = schedule_date_calc(date,schedule)
    scheduled_t = Transaction(INCOME, name, -1 * amount, nextdate, 1, account_id, gen_grouping_num(), note, schedule, False, USER_ID, None)
    insert_transaction(scheduled_t)
    scheduled_transaction_submitted = True
  else:
    # If there's no schedule, add in the normal non-scheduled transaction
    insert_transaction(t)
  return jsonify({'message': 'Successfully added new income!', 'scheduled_transaction_submitted': scheduled_transaction_submitted})

@app.route('/fill_envelopes', methods=['POST'])
@login_required
def fill_envelopes(edited=False):
  name = request.form['name']
  amounts = request.form.getlist('fill-amount')
  envelope_ids = request.form.getlist('envelope_id')
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  note = request.form['note']
  scheduled = request.form.getlist('scheduled')
  scheduled = len(scheduled) != 0
  schedule = request.form['schedule']
  scheduled_transaction_submitted = False
  deletes =[]
  for i in range(len(amounts)):
    amounts[i] = int(round(float(amounts[i])*100))
    envelope_ids[i] = int(envelope_ids[i])
    if amounts[i] == 0:
      deletes.append(i)
  for index in reversed(deletes):
    amounts.pop(index)
    envelope_ids.pop(index)
  t = Transaction(ENVELOPE_FILL, name, amounts, date, envelope_ids, None, None, note, None, False, USER_ID, None)
  # Only insert NEW scheduled transaction if it's not edited
  if scheduled and edited:
    t.schedule = schedule
    # Insert transaction with edited schedule
    envelope_fill(t)
  elif scheduled and not edited:
    # Insert transaction with no schedule
    envelope_fill(t)
    # Insert scheduled transaction
    nextdate = schedule_date_calc(date,schedule)
    scheduled_t = Transaction(ENVELOPE_FILL, name, amounts, nextdate, envelope_ids, None, None, note, schedule, False, USER_ID, None)
    envelope_fill(scheduled_t)
    scheduled_transaction_submitted = True
  else:
    # If there's no schedule, add in the normal non-scheduled transaction
    envelope_fill(t)
  return jsonify({'message': 'Envelopes successfully filled!', 'scheduled_transaction_submitted': scheduled_transaction_submitted})

@app.route('/edit_transaction', methods=['POST'])
@login_required
def edit_transaction():
  scheduled_transaction_submitted = False
  id = int(request.form['edit-id'])
  type = int(request.form['type'])
  delete_transaction(id)
  if (type == BASIC_TRANSACTION):
    new_expense(True)
  elif (type == ENVELOPE_TRANSFER or type == ACCOUNT_TRANSFER):
    new_transfer(True)
  elif (type == INCOME):
    new_income(True)
  elif (type == SPLIT_TRANSACTION):
    new_expense(True)
  elif (type == ENVELOPE_FILL):
    fill_envelopes(True)
  return jsonify({'message': 'Transaction successfully edited!', 'scheduled_transaction_submitted': scheduled_transaction_submitted})

@app.route('/delete_transaction_page', methods=['POST'])
@login_required
# Change this to use an <id> in the URL instead of using the hidden form thing
def delete_transaction_page():
  id = int(request.form['delete-id'])
  delete_transaction(id)
  return 'Transaction successfully deleted!'

@app.route('/api/transaction/<id>/group', methods=['GET'])
@login_required
def get_json(id):
  return jsonify(get_grouped_json(id))

@app.route('/api/edit-accounts', methods=['POST'])
@login_required
def edit_accounts_page():
  old_balances = request.form.getlist('edit-account-balance')
  old_names = request.form.getlist('edit-account-name')
  old_ids = request.form.getlist('account-id')
  new_balances = request.form.getlist('new-account-balance')
  new_names = request.form.getlist('new-account-name')
  old_accounts = []
  new_accounts = []
  for i in range(len(old_ids)):
    old_accounts.append([old_ids[i], old_names[i], int(round(float(old_balances[i])*100))])
  for i in range(len(new_names)):
    new_accounts.append([new_names[i], int(round(float(new_balances[i])*100)), USER_ID])
  edit_accounts(old_accounts, new_accounts)
  return 'Accounts successfully updated!'


@app.route('/api/edit-envelopes', methods=['POST'])
@login_required
def edit_envelopes_page():
  old_budgets = request.form.getlist('edit-envelope-budget')
  old_names = request.form.getlist('edit-envelope-name')
  old_ids = request.form.getlist('envelope-id')
  new_budgets = request.form.getlist('new-envelope-budget')
  new_names = request.form.getlist('new-envelope-name')
  old_envelopes = []
  new_envelopes = []
  for i in range(len(old_ids)):
    old_envelopes.append([old_ids[i], old_names[i], int(round(float(old_budgets[i])*100))])
  for i in range(len(new_names)):
    new_envelopes.append([new_names[i], int(round(float(new_budgets[i])*100)), USER_ID])
  edit_envelopes(old_envelopes, new_envelopes)
  return 'Envelopes successfully updated!'

@app.route('/api/data-reload', methods=['POST'])
@login_required
def transactions_function():
  current_page = request.get_json()['current_page']
  if 'account/' in current_page:
    regex = re.compile('account/(\d+)')
    account_id = int(regex.findall(current_page)[0])
    (transactions_data, offset, limit) = get_account_transactions(account_id,0,50)
    page_total = stringify(get_account(account_id).balance)
  elif 'envelope/' in current_page:
    regex = re.compile('envelope/(\d+)')
    envelope_id = int(regex.findall(current_page)[0])
    (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,0,50)
    page_total = stringify(get_envelope(envelope_id).balance)
  else:
    (transactions_data, offset, limit) = get_transactions(0,50)
    page_total = get_total(USER_ID)
  (active_envelopes, envelopes_data) = get_envelope_dict()
  (active_accounts, accounts_data) = get_account_dict()
  data = {}
  data['total'] = get_total(USER_ID)
  data['unallocated'] = envelopes_data[1].balance
  data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
  data['accounts_html'] = render_template('accounts.html', active_accounts=active_accounts, accounts_data=accounts_data)
  data['envelopes_html'] = render_template('envelopes.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data)
  data['account_selector_html'] = render_template('account_selector.html', accounts_data=accounts_data)
  data['envelope_selector_html'] = render_template('envelope_selector.html', envelopes_data=envelopes_data)
  data['envelope_editor_html'] = render_template('envelope_editor.html', envelopes_data=envelopes_data)
  data['account_editor_html'] = render_template('account_editor.html', accounts_data=accounts_data)
  data['envelope_fill_editor_rows_html'] = render_template('envelope_fill_editor_rows.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data)
  data['page_total'] = page_total
  return jsonify(data)

@app.route('/api/load-more', methods=['POST'])
@login_required
def load_more():
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
    (transactions_data, offset, limit) = get_transactions(current_offset,50)

  # these 2 lines shouldn't be necessary here after updating to a join clause
  (active_envelopes, envelopes_data) = get_envelope_dict()
  (active_accounts, accounts_data) = get_account_dict()
  more_transactions = render_template('more_transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, accounts_data=accounts_data, envelopes_data=envelopes_data)
  return jsonify({'offset': offset, 'limit': limit, 'transactions': more_transactions})

@app.route('/api/multi-delete', methods=['POST'])
@login_required
def multi_delete():
  delete_ids = request.form.getlist('delete')
  for id in delete_ids:
    delete_transaction(id)
  return 'Transactions successfully deleted!'


#MAKE SURE DEBUG IS TURNED OFF FOR MAIN DEPLOYMENT
if __name__ == '__main__':
  platform = platform.system()
  if platform == 'Windows':
      debug_bool = True
  else:
    debug_bool = False
  app.run(debug=debug_bool)