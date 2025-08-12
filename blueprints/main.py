"""
main.py
This file contains all the main routes for the application once you're past login
Does not include routes for error handling or the bug report form
"""

#Flask imports
from flask import Blueprint, request, jsonify, render_template, make_response
from flask_login import login_required, current_user

#Library imports
import re

#Custom import
from database import *
from exceptions import *
from forms import NewExpenseForm, NewTransferForm, NewIncomeForm, BugReportForm
from filters import datetimeformat
from textLogging import log_write
from blueprints.auth import check_confirmed, get_uuid_from_cookie

main_bp = Blueprint('main', __name__)

@main_bp.route("/home", methods=['GET'])
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
        TType=TType,
        new_expense_form = NewExpenseForm(),
        new_transfer_form = NewTransferForm(),
        new_income_form = NewIncomeForm(),
        bug_report_form = BugReportForm()
      ))
      response.delete_cookie('timestamp')
      return response
    except CustomException as e:
      return jsonify({"error": str(e)})

# Display all transactions on the home dashboard
@main_bp.route("/get_home_transactions_page", methods=["POST"])
@login_required
@check_confirmed
def get_all_transactions_page():
  try:
    uuid = get_uuid_from_cookie()
    js_data = request.get_json()
    timestamp = js_data.get('timestamp')
    return jsonify(_build_home_page(uuid, timestamp))
  except CustomException:
    return jsonify({"error": "ERROR: Something went wrong and your envelope data could not be loaded!"})

# Display transactions from a specific envelope on the home dashboard
@main_bp.route("/get_envelope_page", methods=["POST"])
@login_required
@check_confirmed
def get_envelope_page():
  try:
    uuid = get_uuid_from_cookie()
    js_data = request.get_json()
    envelope_id = js_data['envelope_id']
    timestamp = js_data['timestamp']
    return jsonify(_build_envelope_page(uuid, envelope_id, timestamp))
  except CustomException:
    return jsonify({"error": "ERROR: Something went wrong and your envelope data could not be loaded!"})

# Display transactions from a specific account on the home dashboard
@main_bp.route("/get_account_page", methods=["POST"])
@login_required
@check_confirmed
def get_account_page():
  try:
    uuid = get_uuid_from_cookie()
    js_data = request.get_json()
    account_id = js_data['account_id']
    timestamp = js_data['timestamp']
    return jsonify(_build_account_page(uuid, account_id, timestamp))
  except CustomException:
    return jsonify({"error": "ERROR: Something went wrong and your account data could not be loaded!"})

# Display the transactions from a searrch query on the home dashboard
@main_bp.route('/api/search-transactions', methods=['POST'])
@login_required
@check_confirmed
def search_transactions():
  try:
    uuid = get_uuid_from_cookie()
    # All fields optional
    search_term = request.form.get('search_term', '').strip()
    amt_min_raw = request.form.get('search_amt_min', '').strip()
    amt_max_raw = request.form.get('search_amt_max', '').strip()
    date_min_raw = request.form['search_date_min']
    date_max_raw = request.form['search_date_max']
    e_ids_raw = request.form.getlist('search_envelope_ids') if 'search_envelope_ids' in request.form else []
    a_ids_raw = request.form.getlist('search_account_ids') if 'search_account_ids' in request.form else []
    timestamp = request.form['timestamp']

    amt_min = None
    amt_max = None
    try: 
      if amt_min_raw:
        amt_min = (int(round(float(amt_min_raw) * 100)))
      if amt_max_raw:
        amt_max = (int(round(float(amt_max_raw) * 100)))
    except:
      raise InvalidFormDataError("ERROR: Invalid form data in 'amount' field for search!")

    date_min = None
    date_max = None
    if date_min_raw:
      try:
        date_min = datetime.strptime(date_min_raw, '%m/%d/%Y')
      except ValueError:
        raise InvalidFormDataError("ERROR: Invalid date format for 'Min date'. Expected format: MM/DD/YYYY")

    if date_max_raw:
      try:
        date_max = datetime.strptime(date_max_raw, '%m/%d/%Y')
      except ValueError:
        raise InvalidFormDataError("ERROR: Invalid date format for 'Max date'. Expected format: MM/DD/YYYY")

    # Convert envelope/account id lists front strings to ints (Materialize multi-select sends comma separated via serialize)
    # request.form.getlist will already split repeated keys. If values are like '1,2' handle that too
    def expand(id_list):
      expanded = []
      for item in id_list:
        for part in str(item).split(','):
          part = part.strip()
          if part.isdigit():
            expanded.append(int(part))
      return expanded
    envelope_ids = expand(e_ids_raw)
    account_ids = expand(a_ids_raw)

    print(amt_min)
    print(amt_max)

    check_pending_transactions(uuid, timestamp)
    (transactions_data, offset, limit) = get_search_transactions(uuid,start=0,amount=50,search_term=search_term,amt_min=amt_min,amt_max=amt_max,date_min=date_min,date_max=date_max,envelope_ids=envelope_ids,account_ids=account_ids)
    (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
    (active_accounts, accounts_data) = get_user_account_dict(uuid)
    data = {}
    data['current_page'] = "Search results"
    if not transactions_data:
      data['transactions_html'] = render_template('transactions.html', current_page = 'Search results', transactions_data = [], empty_message = 'No search results found')
    else:
      data['transactions_html'] = render_template('transactions.html',current_page = 'Search results', transactions_data = transactions_data, envelopes_data = envelopes_data, accounts_data = accounts_data, offset = offset, limit=limit,TType = TType)
    return jsonify(data)
  except Exception as e:
    return jsonify({'error': str(e)})

# Display the transactions on the home dashboard from the page you were on before the search
@main_bp.route('/api/reset-search', methods=['POST'])
@login_required
@check_confirmed
def reset_search():
  """Return the transaction list for the previously viewed page before a search.

  Expects JSON: { "previous-page": <string>, "timestamp": <timestamp str> }
  previous_page represents the page the user was on before the search
  previous_page formats supported:
    - None or 'All Transactions' -> home transactions page
    - 'envelope/<id>' -> specific envelope page
    - 'account/<id>' -> specific account page
  """
  try:
    uuid = get_uuid_from_cookie()
    js_data = request.get_json() or {}
    prev = (js_data.get('previous_page') or 'All Transactions').strip()
    timestamp = js_data.get('timestamp')
    if prev.lower() in ['all transactions']:
      return jsonify(_build_home_page(uuid, timestamp))
    
    if prev.startswith('envelope/'):
      try:
        envelope_id = int(prev.split('/',1)[1])
      except ValueError:
        return jsonify({'error': 'Invalid envelope id'})
      return jsonify(_build_envelope_page(uuid, envelope_id, timestamp))
    
    if prev.startswith('account/'):
      try:
        account_id = int(prev.split('/',1)[1])
      except ValueError:
        return jsonify({'error': 'Invalid account id'})
      return jsonify(_build_account_page(uuid, account_id, timestamp))
    return jsonify({'error': 'Invalid previous_page value supplied to reset-search.'})
  
  except CustomException as ce:
    return jsonify({'error': str(ce)})
  except Exception as e:
    return jsonify({'error': f'Unexpected error resetting search: {e}'})

# Display reloaded data on the home dashboard whenever a transaction is added/removed/edited or accounts/envelopes are edited
@main_bp.route('/api/data-reload', methods=['POST'])
@login_required
@check_confirmed
def data_reload():
  try:
    uuid = get_uuid_from_cookie()
    u = get_user_by_uuid(uuid)
    js_data = request.get_json()
    current_page = js_data['current_page']
    timestamp = js_data['timestamp']
    should_reload_transactions_bin = js_data['should_reload_transactions_bin']
    check_pending_transactions(uuid, timestamp) #Apply any pending transactions that need to before rendering the template
    if 'account/' in current_page:
      regex = re.compile(r'account/(\d+)')
      account_id = int(regex.findall(current_page)[0])
      (transactions_data, offset, limit) = get_account_transactions(uuid,account_id,0,50)
      page_total = balanceformat(get_account(account_id).balance/100)
    elif 'envelope/' in current_page:
      regex = re.compile(r'envelope/(\d+)')
      envelope_id = int(regex.findall(current_page)[0])
      (transactions_data, offset, limit) = get_envelope_transactions(uuid,envelope_id,0,50)
      page_total = balanceformat(get_envelope(envelope_id).balance/100)
    elif 'Search' in current_page:
      (transactions_data, offset, limit) = get_search_transactions(uuid, js_data['search_term'], 0, 50) # TODO: Edit this function
      page_total = None
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
    data['account_select_options_html'] = render_template('account_select_options.html', accounts_data=accounts_data)
    data['account_select_options_special_html'] = render_template('account_select_options.html', accounts_data=accounts_data, special=True)
    data['envelope_select_options_html'] = render_template('envelope_select_options.html', envelopes_data=envelopes_data, unallocated_e_id=u.unallocated_e_id)
    data['envelope_select_options_special_html'] = render_template('envelope_select_options.html', envelopes_data=envelopes_data, unallocated_e_id=u.unallocated_e_id, special=True)
    data['envelope_editor_html'] = render_template('envelope_editor.html', envelopes_data=envelopes_data, budget_total=budget_total,  unallocated_e_id=u.unallocated_e_id)
    data['account_editor_html'] = render_template('account_editor.html', accounts_data=accounts_data)
    data['envelope_fill_editor_rows_html'] = render_template('envelope_fill_editor_rows.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data, unallocated_e_id=u.unallocated_e_id)
    data['page_total'] = page_total
    if should_reload_transactions_bin:
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

# Loads more transactions for display into the transaction list on the home dashboard
@main_bp.route('/api/load-more', methods=['POST'])
@login_required
@check_confirmed
def load_more():
  try:
    uuid = get_uuid_from_cookie()
    js_data = request.get_json()
    current_offset = js_data['offset']
    current_page = js_data['current_page']
    # TODO: When implementing unit test framework, test what happens if the user somehow manually changes the current_page variable so that it doesn't include a valid account or envelope id
    # TODO: When implementing unit test framework, if the user manually changes the offset variable to something other than a valid integer, the app will crash. Test for this.
    if 'account/' in current_page:
      regex = re.compile(r'account/(\d+)')
      account_id = int(regex.findall(current_page)[0])
      (transactions_data, offset, limit) = get_account_transactions(uuid,account_id,current_offset,50)
    elif 'envelope/' in current_page:
      regex = re.compile(r'envelope/(\d+)')
      envelope_id = int(regex.findall(current_page)[0])
      (transactions_data, offset, limit) = get_envelope_transactions(uuid,envelope_id,current_offset,50)
    elif 'Search' in current_page:
      (transactions_data, offset, limit) = get_search_transactions(uuid, js_data['search_term'], current_offset, 50) # TODO: edit this function
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


# ---------------- Helper builders (not routes) ----------------
def _build_home_page(uuid, timestamp):
  check_pending_transactions(uuid, timestamp)
  (transactions_data, offset, limit) = get_home_transactions(uuid,0,50)
  (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
  (active_accounts, accounts_data) = get_user_account_dict(uuid)
  page_total = balanceformat(get_total(uuid))
  return {
    'page_total': page_total,
    'current_page': 'All Transactions',
    'transactions_html': render_template(
      'transactions.html',
      current_page='All Transactions',
      transactions_data=transactions_data,
      envelopes_data=envelopes_data,
      accounts_data=accounts_data,
      offset=offset,
      limit=limit,
      TType=TType
    )
  }

def _build_envelope_page(uuid, envelope_id, timestamp):
  check_pending_transactions(uuid, timestamp)
  (transactions_data, offset, limit) = get_envelope_transactions(uuid,envelope_id,0,50)
  (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
  (active_accounts, accounts_data) = get_user_account_dict(uuid)
  page_total = balanceformat(get_envelope(envelope_id).balance/100)
  name = get_envelope(envelope_id).name
  return {
    'page_total': page_total,
    'current_page': name,
    'transactions_html': render_template(
      'transactions.html',
      current_page=f'envelope/{envelope_id}',
      transactions_data=transactions_data,
      envelopes_data=envelopes_data,
      accounts_data=accounts_data,
      offset=offset,
      limit=limit,
      TType=TType
    )
  }

def _build_account_page(uuid, account_id, timestamp):
  check_pending_transactions(uuid, timestamp)
  (transactions_data, offset, limit) = get_account_transactions(uuid,account_id,0,50)
  (active_envelopes, envelopes_data, budget_total) = get_user_envelope_dict(uuid)
  (active_accounts, accounts_data) = get_user_account_dict(uuid)
  page_total = balanceformat(get_account(account_id).balance/100)
  name = get_account(account_id).name
  return {
    'page_total': page_total,
    'current_page': name,
    'transactions_html': render_template(
      'transactions.html',
      current_page=f'account/{account_id}',
      transactions_data=transactions_data,
      envelopes_data=envelopes_data,
      accounts_data=accounts_data,
      offset=offset,
      limit=limit,
      TType=TType
    )
  }

# Route to create a new BASIC_TRANSACTION
@main_bp.route('/new_expense', methods=['POST'])
@login_required
@check_confirmed
def new_expense(edited=False):
  try:
    form = NewExpenseForm()
    names = form.name.data
    if names is None:
      raise InvalidFormDataError("ERROR: No transaction name was submitted for new expense!")

    if not form.validate():
      errors = {field.name: field.errors for field in form if field.errors}
      log_write(f"NEW EXPENSE FAIL: Errors - {errors}")
      return jsonify(success=False, errors=errors)

    uuid = get_uuid_from_cookie()
    names = [n.lstrip() for n in names.split(',') if n.lstrip()] #Parse name field separated by commas
    str_amounts = request.form.getlist('amount')
    str_envelope_ids = request.form.getlist('envelope_id')
    account_id = request.form['account_id']
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    timestamp = date_parse(request.form['timestamp'])
    note = request.form['note']
    scheduled = len(request.form.getlist('scheduled')) != 0
    schedule = request.form['schedule']
    sched_t_submitted = False
    pending = is_pending(date, timestamp)
    toasts = []

    # Convert the amounts and envelope_ids from strings to integers
    amounts = []
    envelope_ids = []
    try: 
      for i in range(len(str_amounts)):
        amounts.append(int(round(float(str_amounts[i]) * 100)))
        envelope_ids.append(int(str_envelope_ids[i]))
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
    return jsonify({'success': True, 'toasts': toasts})
  except Exception as e:
    toasts.append(f"ERROR: {str(e)}")
    return jsonify({'success': False, 'toasts': toasts})

# Route to create a new ACCOUNT_TRANSFER or ENVELOPE_TRANSFER
@main_bp.route('/new_transfer', methods=['POST'])
@login_required
@check_confirmed
def new_transfer(edited=False):
  try:
    form = NewTransferForm()
    names = form.name.data
    if names is None:
      raise InvalidFormDataError("ERROR: No transaction name was submitted for new transfer!")

    if not form.validate():
      errors = {field.name: field.errors for field in form if field.errors}
      log_write(f"NEW TRANSFER FAIL: Errors - {errors}")
      return jsonify(success=False, errors=errors)

    uuid = get_uuid_from_cookie()
    transfer_type = int(request.form['transfer_type'])
    names = [n.lstrip() for n in names.split(',') if n.lstrip()] #Parse name field separated by commas
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
    return jsonify({'success': True, 'toasts': toasts})
  
  except Exception as e:
    toasts.append(f"ERROR: {str(e)}")
    return jsonify({'success': False, 'toasts': toasts})

# Route to create a new INCOME
@main_bp.route('/new_income', methods=['POST'])
@login_required
@check_confirmed
def new_income(edited=False):
  try:
    form = NewIncomeForm()
    names = form.name.data
    if names is None:
      raise InvalidFormDataError("ERROR: No transaction name was submitted for new income!")

    if not form.validate():
      errors = {field.name: field.errors for field in form if field.errors}
      log_write(f"NEW INCOME FAIL: Errors - {errors}")
      return jsonify(success=False, errors=errors)

    uuid = get_uuid_from_cookie()
    u = get_user_by_uuid(uuid)
    names = [n.lstrip() for n in names.split(',') if n.lstrip()] #Parse name field separated by commas
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
    return jsonify({'success': True,'toasts': toasts})
  
  except Exception as e:
    toasts.append(f"ERROR: {str(e)}")
    return jsonify({'success': False, 'toasts': toasts})

# Route to create a new ENVELOPE_FILL 
@main_bp.route('/new_envelope_fill', methods=['POST'])
@login_required
@check_confirmed
def new_envelope_fill(edited=False):
  try:
    uuid = get_uuid_from_cookie()
    names = [n.lstrip() for n in request.form['name'].split(',') if n.lstrip()] #Parse name field separated by commas
    str_amounts = request.form.getlist('fill-amount')
    str_envelope_ids = request.form.getlist('envelope_id')
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    timestamp = date_parse(request.form['timestamp'])
    note = request.form['note']
    scheduled = len(request.form.getlist('scheduled')) != 0
    schedule = request.form['schedule']
    sched_t_submitted = False
    pending = is_pending(date, timestamp)
    toasts = []
    
    # Convert the amounts and envelope_ids from strings to integers
    amounts = []
    envelope_ids = []
    try:
      # If the user didn't input a number for a particular envelope, don't add it from the list that will be used to create the envelope_fill transaction
      for i in range(len(str_amounts)):
        if str_amounts[i] == "":
          continue
        else:
          amounts.append(int(round(float(str_amounts[i])*100)))
          envelope_ids.append(int(str_envelope_ids[i]))
    except Exception as e:
      log_write(f"INTERNAL ERROR: {e}")
      raise InvalidFormDataError("ERROR: Invalid form data in 'amount' field for new_envelope_fill!")
    
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
          raise InvalidFormDataError("ERROR: No transaction name was submitted for new_envelope_fill!")
    else:
      toasts.append("No envelope fill was created!")

    health_check(toasts)
    return jsonify({'toasts': toasts})

  except CustomException as e:
    return jsonify({"error": str(e)})

# Routes to the various transaction editing functions (called from )
@main_bp.route('/edit_transaction', methods=['POST'])
@login_required
@check_confirmed
def edit_transaction():
  try:

    # Retrieve the common info among all transactions (id and the type) from the form
    uuid = get_uuid_from_cookie()
    id = int(request.form['edit-id'])
    type = TType.from_int(int(request.form['type']))
      
    # Create a new transaction in the database based on the info you just edited
    if (type == TType.BASIC_TRANSACTION):
      response = new_expense(True)
    elif (type == TType.ENVELOPE_TRANSFER or type == TType.ACCOUNT_TRANSFER):
      response =  new_transfer(True)
    elif (type == TType.INCOME):
      response = new_income(True)
    elif (type == TType.SPLIT_TRANSACTION):
      response = new_expense(True)
    elif (type == TType.ENVELOPE_FILL):
      response = new_envelope_fill(True)
    elif (type == TType.ENVELOPE_DELETE):
      response = edit_envelope_delete()
    elif (type == TType.ACCOUNT_DELETE):
      response = edit_account_delete()
    elif (type == TType.ACCOUNT_ADJUST):
      response =  edit_account_adjust()

    # Delete the original transaction in the database if a new one was created successfully
    response_json = response.get_json()
    if response_json is not None and not response_json.get('error'):
      # If the transaction was an ENVELOPE_DELETE or ACCOUNT_DELETE, only the name/note was edited, so no need to delete the original transaction
      if (type != TType.ENVELOPE_DELETE and type != TType.ACCOUNT_DELETE): 
        delete_transaction(uuid, id)
      
    return response
  
  except CustomException as e:
    return jsonify({"error": str(e)})

# Route to edit ENVELOPE_DELETE transactions
@main_bp.route('/edit_envelope_delete', methods=['POST'])
@login_required
@check_confirmed
def edit_envelope_delete():
  try:
    uuid = get_uuid_from_cookie()
    new_name = request.form['name']
    new_note = request.form['note']
    t_id = int(request.form['edit-id'])
    toasts = []
    edit_envelope_delete_transaction(uuid, t_id, new_name, new_note)
    toasts.append("Transaction details updated!")
    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

# Route to edit ACCOUNT_DELETE transactions
@main_bp.route('/edit_account_delete', methods=['POST'])
@login_required
@check_confirmed
def edit_account_delete():
  try:
    uuid = get_uuid_from_cookie()
    new_name = request.form['name']
    new_note = request.form['note']
    t_id = int(request.form['edit-id'])
    toasts = []
    edit_account_delete_transaction(uuid, t_id, new_name, new_note)
    toasts.append("Transaction details updated!")
    health_check(toasts)
    return jsonify({'toasts': toasts})
  
  except CustomException as e:
    return jsonify({"error": str(e)})

# Route to edit ACCOUNT_ADJUST transactions
@main_bp.route('/edit_account_adjust', methods=['POST'])
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

# Edit the balances, names, and orders of existing accounts, and creates/deletes accounts (called from the account editor form)
@main_bp.route('/api/edit-accounts', methods=['POST'])
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

# Edit the balances, budgets, names, and orders of existing envelopes, and creates/deletes envelopes (called from the envelope editor form)
@main_bp.route('/api/edit-envelopes', methods=['POST'])
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

# Route to delete a transaction (called from the delete button in the transaction editor)
@main_bp.route('/api/delete_transaction', methods=['POST'])
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

# Route to delete multiple transactions at once (called from the multidelete form encapsulating the transactions bin)
@main_bp.route('/api/multi-delete', methods=['POST'])
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

# Get all the info from a grouped transaction when opening the transaction editor modal
@main_bp.route('/api/transaction/<id>/group', methods=['GET'])
@login_required
@check_confirmed
def get_grouped_json_page(id):
  try:
    uuid = get_uuid_from_cookie()
    grouped_json = get_grouped_json(uuid, id)
    return jsonify(grouped_json)
  
  except CustomException as e:
    return jsonify({"error": str(e)})

# Loads the static HTML templates into the page memory (used for adding envelope/account rows to editors and more envelopes to transaction builder/editor)
@main_bp.route('/api/load-static-html', methods=["POST"])
@login_required
@check_confirmed
def load_static_html():
  return jsonify({
    'edit_envelope_row': render_template('edit_envelope_row.html'),
    'edit_account_row': render_template('edit_account_row.html'),
    't_editor_new_env_row': render_template('transaction_editor_new_envelope_row.html')
  })