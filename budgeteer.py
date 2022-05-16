"""
This file contains functions relevant the GUI, the flask app, and getting data from the browser
This file interacts a lot with the javascript/jQuery running on the site
"""

from flask import Flask, render_template, url_for, request, redirect, jsonify
from database import *
from datetime import datetime
from datetime import timedelta
import calendar
import re
import platform

app = Flask(__name__)
app.config['SECRET_KEY'] = 'da3e7b955be0f7eb264a9093989e0b46'

USER_ID = 1

t_type_dict = {
  0: 'Basic Transaction',
  1: 'Envelope Transfer',
  2: 'Account Transfer',
  3: 'Income',
  4: 'Split Transaction',
  5: 'Envelope Fill',
  6: 'Envelope Delete',
  7: 'Account Delete'
}

t_type_icon_dict = {
  0: 'local_atm',
  1: 'swap_horiz',
  2: 'swap_vert',
  3: 'vertical_align_bottom',
  4: 'call_split',
  5: 'input',
  6: 'layers_clear',
  7: 'money_off'
}

def datetimeformat(value, format='%m/%d/%Y'):
  return value.strftime(format)

def datetimeformatshort(value, format='%b %d\n%Y'):
  return value.strftime(format)

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

def schedule_date_calc(tdate, schedule):
  """
  Calculates the upcoming transaction date for a scheduled transaction based on its frequency.
  Returns the date of the next transaction.
  """
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

@app.route("/")
@app.route("/home", methods=['GET'])
def home():
  (transactions_data, offset, limit) = get_transactions(0,50)
  (active_envelopes, envelopes_data) = get_envelope_dict()
  (active_accounts, accounts_data) = get_account_dict()
  total_funds = get_total(USER_ID)
  current_view = 'All transactions'
  current_total = total_funds
  return render_template('layout.html', t_type_dict=t_type_dict, t_type_icon_dict=t_type_icon_dict, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view, current_total=current_total, offset=offset, limit=limit)

@app.route("/get_envelope_page", methods=["POST"], )
def get_envelope_page():
  envelope_id = request.get_json()['envelope_id']
  (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,0,50)
  (active_envelopes, envelopes_data) = get_envelope_dict()
  (active_accounts, accounts_data) = get_account_dict()
  page_total = stringify(get_envelope(envelope_id).balance)
  data = {}
  data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_icon_dict=t_type_icon_dict, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
  data['page_total'] = page_total
  data['envelope_name'] = get_envelope(envelope_id).name
  return jsonify(data)

@app.route("/get_account_page", methods=["POST"], )
def get_account_page():
  account_id = request.get_json()['account_id']
  (transactions_data, offset, limit) = get_account_transactions(account_id,0,20)
  (active_envelopes, envelopes_data) = get_envelope_dict()
  (active_accounts, accounts_data) = get_account_dict()
  page_total = stringify(get_account(account_id).balance)
  data = {}
  data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_icon_dict = t_type_icon_dict, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
  data['page_total'] = page_total
  data['account_name'] = get_account(account_id).name
  return jsonify(data)

@app.route('/new_expense', methods=['POST'])
def new_expense(edited=False):
  # edited=True if this is called from edit_transaction
  name = request.form['name']
  #Parse the name field to separate names by commas
  names = name.split(',')
  names = [n.lstrip() for n in names if n.lstrip()]
  amounts = request.form.getlist('amount')
  envelope_ids = request.form.getlist('envelope_id')
  account_id = request.form['account_id']
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  note = request.form['note']
  scheduled = request.form.getlist('scheduled')
  scheduled = len(scheduled) != 0
  schedule = request.form['schedule']
  sched_t_submitted = False
  for i in range(len(amounts)):
    amounts[i] = int(round(float(amounts[i]) * 100))
    envelope_ids[i] = int(envelope_ids[i])
  for name in names:
    t = Transaction(BASIC_TRANSACTION, name, amounts, date, envelope_ids, account_id, None, note, None, False, USER_ID)
    # Only insert a NEW scheduled transaction if it's not an edited transaction
    if scheduled and edited:
      t.schedule = schedule
    if scheduled and not edited:
      # Create placeholder scheduled transaction
      nextdate = schedule_date_calc(date,schedule)
      scheduled_t = Transaction(BASIC_TRANSACTION, name, amounts, nextdate, envelope_ids, account_id, None, note, schedule, False, USER_ID)

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
        sched_t_submitted = True
    else:
      t.type = SPLIT_TRANSACTION
      new_split_transaction(t)
      if scheduled and not edited:
        # insert new split transaction with schedule
        scheduled_t.type = SPLIT_TRANSACTION
        new_split_transaction(scheduled_t)
        sched_t_submitted = True

  if len(names) > 1:
    message = f'Successfully added {len(names)} new expenses!'
    sched_message = f'Successfully added {len(names)} new scheduled expenses!'
  elif len(names) == 0:
    message = 'No new expenses were added! (shouldn\'t be possible)'
  elif len(names) == 1:
    message = 'Successfully added new expense!'
    sched_message = 'Successfully added new scheduled expense!'
  else:
    message = 'There was an error!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return jsonify({'message': message, 'sched_message': sched_message, 'sched_t_submitted': sched_t_submitted})

@app.route('/new_transfer', methods=['POST'])
def new_transfer(edited=False):
  # edited=True if this is called from edit_transaction
  transfer_type = int(request.form['transfer_type'])
  name = request.form['name']
  #Parse the name field to separate names by commas
  names = name.split(',')
  names = [n.lstrip() for n in names if n.lstrip()]
  amount = int(round(float(request.form['amount'])*100))
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  note = request.form['note']
  scheduled = request.form.getlist('scheduled')
  scheduled = len(scheduled) != 0
  schedule = request.form['schedule']
  sched_t_submitted = False
  for name in names:
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
        sched_t_submitted = True
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
        sched_t_submitted = True
      else:
        # If there's no schedule, add in the normal non-scheduled transaction
        envelope_transfer(name, amount, date, to_envelope, from_envelope, note, None, USER_ID)
    else:
      print('What the heck are you even trying to do you twit?')


  if len(names) > 1:
    message = f'Successfully added {len(names)} new transfers!'
    sched_message = f'Successfully added {len(names)} new scheduled transfers!'
  elif len(names) == 0:
    message = 'No new transfers were added! (shouldn\'t be possible)'
  elif len(names) == 1:
    message = 'Successfully added new transfer!'
    sched_message = 'Successfully added new scheduled transfer!'
  else:
    message = 'There was an error!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return jsonify({'message': message, 'sched_message': sched_message, 'sched_t_submitted': sched_t_submitted})


@app.route('/new_income', methods=['POST'])
def new_income(edited=False):
  name = request.form['name']
  #Parse the name field to separate names by commas
  names = name.split(',')
  names = [n.lstrip() for n in names if n.lstrip()]
  amount = int(round(float(request.form['amount'])*100))
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  account_id = request.form['account_id']
  note = request.form['note']
  scheduled = request.form.getlist('scheduled')
  scheduled = len(scheduled) != 0
  schedule = request.form['schedule']
  sched_t_submitted = False
  for name in names:
    t = Transaction(INCOME, name, -1 * amount, date, 1, account_id, gen_grouping_num(), note, None, False, USER_ID)

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
      scheduled_t = Transaction(INCOME, name, -1 * amount, nextdate, 1, account_id, gen_grouping_num(), note, schedule, False, USER_ID)
      insert_transaction(scheduled_t)
      sched_t_submitted = True
    else:
      # If there's no schedule, add in the normal non-scheduled transaction
      insert_transaction(t)

  if len(names) > 1:
    message = f'Successfully added {len(names)} new income!'
    sched_message = f'Successfully added {len(names)} new scheduled incomes!'
  elif len(names) == 0:
    message = 'No new incomes were added! (shouldn\'t be possible)'
  elif len(names) == 1:
    message = 'Successfully added new income!'
    sched_message = 'Successfully added new scheduled income!'
  else:
    message = 'There was an error!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return jsonify({'message': message, 'sched_message': sched_message, 'sched_t_submitted': sched_t_submitted})

@app.route('/fill_envelopes', methods=['POST'])
def fill_envelopes(edited=False):
  name = request.form['name']
  #Parse the name field to separate names by commas
  names = name.split(',')
  names = [n.lstrip() for n in names if n.lstrip()]
  amounts = request.form.getlist('fill-amount')
  envelope_ids = request.form.getlist('envelope_id')
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  note = request.form['note']
  scheduled = request.form.getlist('scheduled')
  scheduled = len(scheduled) != 0
  schedule = request.form['schedule']
  sched_t_submitted = False
  for name in names:
    deletes =[]
    for i in range(len(amounts)):
      amounts[i] = int(round(float(amounts[i])*100))
      envelope_ids[i] = int(envelope_ids[i])
      if amounts[i] == 0:
        deletes.append(i)
    for index in reversed(deletes):
      amounts.pop(index)
      envelope_ids.pop(index)
    t = Transaction(ENVELOPE_FILL, name, amounts, date, envelope_ids, None, None, note, None, False, USER_ID)
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
      scheduled_t = Transaction(ENVELOPE_FILL, name, amounts, nextdate, envelope_ids, None, None, note, schedule, False, USER_ID)
      envelope_fill(scheduled_t)
      sched_t_submitted = True
    else:
      # If there's no schedule, add in the normal non-scheduled transaction
      envelope_fill(t)

  if len(names) > 1:
    message = f'Successfully added {len(names)} envelope fills!'
    sched_message = f'Successfully added {len(names)} new scheduled envelope fills!'
  elif len(names) == 0:
    message = 'No envelope fill was added! (shouldn\'t be possible)'
  elif len(names) == 1:
    message = 'Envelopes successfully filled!'
    sched_message = 'Successfully added new scheduled envelope fill!'
  else:
    message = 'There was an error!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return jsonify({'message': message, 'sched_message': sched_message, 'sched_t_submitted': sched_t_submitted})

@app.route('/edit_delete_envelope', methods=['POST'])
def edit_delete_envelope(envelope_id):
  # edited=True if this is called from edit_transaction
  name = request.form['name']
  date = datetime.strptime(request.form['date'], '%m/%d/%Y')
  note = request.form['note']

  # A copy of the delete_envelope() function from database.py but with the info from the form pasted in
  with conn:
    if (envelope_id != UNALLOCATED): #You can't delete the unallocated envelope
      e = get_envelope(envelope_id)
      grouping = gen_grouping_num()
      # 1. Empty the deleted envelope
      t_envelope = Transaction(ENVELOPE_DELETE, name, e.balance, date, envelope_id, None, grouping, note, None, 0, USER_ID)
      insert_transaction(t_envelope)
      print()
      # 2. Fill the unallocated envelope
      t_unallocated = Transaction(ENVELOPE_DELETE, name, -1*e.balance, date, envelope_id, None, grouping, note, None, 0, USER_ID)
      insert_transaction(t_unallocated)
      # 3. Mark the envelope as deleted
      c.execute("UPDATE envelopes SET deleted=1 WHERE id=?", (envelope_id,))
    else:
        print("You can't delete the 'Unallocated' envelope you moron")
  
  message = 'Updated envelope deletion!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return jsonify({'message': message})

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
  sched_t_submitted = False #This has to be here or else the javascript side breaks
  id = int(request.form['edit-id'])
  type = int(request.form['type'])
  if (type == ENVELOPE_DELETE):
    e_id = get_transaction(id).envelope_id
  elif (type == ACCOUNT_DELETE):
    a_id = get_transaction(id).account_id
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
  elif (type == ENVELOPE_DELETE):
    edit_delete_envelope(e_id)
  elif (type == ACCOUNT_DELETE):
    edit_delete_account(a_id)

  message = 'Transaction successfully edited!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return jsonify({'message': message, 'sched_t_submitted': sched_t_submitted})

@app.route('/delete_transaction_page', methods=['POST'])
# TODO: Change this to use an <id> in the URL instead of using the hidden form thing (SEE gget_json)
def delete_transaction_page():
  id = int(request.form['delete-id'])
  delete_transaction(id)
  return 'Transaction successfully deleted!'

@app.route('/api/transaction/<id>/group', methods=['GET'])
def get_json(id):
  return jsonify(get_grouped_json(id))

@app.route('/api/edit-accounts', methods=['POST'])
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

  message = 'Accounts successfully updated!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return message


@app.route('/api/edit-envelopes', methods=['POST'])
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

  message = 'Envelopes successfully updated!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return message

@app.route('/api/data-reload', methods=['POST'])
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
  data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_icon_dict = t_type_icon_dict, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
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
  more_transactions = render_template('more_transactions.html', t_type_dict=t_type_dict, t_type_icon_dict = t_type_icon_dict, transactions_data=transactions_data, accounts_data=accounts_data, envelopes_data=envelopes_data)
  return jsonify({'offset': offset, 'limit': limit, 'transactions': more_transactions})

@app.route('/api/multi-delete', methods=['POST'])
def multi_delete():
  delete_ids = request.form.getlist('delete')
  for id in delete_ids:
    delete_transaction(id)

  message = 'Transactions successfully deleted!'
  if (health_check() is False):
    message = message + " HEALTH ERROR!!!"
  return message


#MAKE SURE DEBUG IS TURNED OFF FOR MAIN DEPLOYMENT
if __name__ == '__main__':
  platform = platform.system()
  if platform == 'Windows':
      debug_bool = True
  else:
    debug_bool = False
  app.run(debug=debug_bool)
