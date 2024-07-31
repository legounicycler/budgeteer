"""
TODO: Add description of the file here
"""

#Flask imports
from flask import Blueprint, request, current_app, jsonify, render_template, make_response
from flask_login import login_required, current_user
from flask_mail import Message

#Library imports
from werkzeug.exceptions import HTTPException
import re, os
from werkzeug.utils import secure_filename

#Custom import
from database import *
from exceptions import *
from forms import NewExpenseForm, NewTransferForm, NewIncomeForm
from filters import datetimeformat
from textLogging import log_write
from blueprints.auth import check_confirmed, get_uuid_from_cookie, generate_uuid
import traceback

main_bp = Blueprint('main', __name__)

# Error handler for HTTP exceptions
@main_bp.errorhandler(HTTPException)
def handle_exception(e):
    log_write(f'HTTP ERROR: {e}', "EventLog.txt")
    log_write(f'\n{traceback.format_exc()}', "EventLog.txt")
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # If error happens in an ajax request, return a response with the error message rather than rendering the error_page template
    #    This is because the ajax request will redirect via javascript to the /error route below which renders the template
    if is_ajax:
      response = jsonify({'error_message': e.description})
      response.status_code = e.code
      return response
    return render_template('error_page.html', message=f"Error {e.code}: {e.description}"), e.code

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
        new_income_form = NewIncomeForm()
      ))
      response.delete_cookie('timestamp')
      return response
    except CustomException as e:
      return jsonify({"error": str(e)})

@main_bp.route("/get_home_transactions_page", methods=["POST"])
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

@main_bp.route("/get_envelope_page", methods=["POST"])
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

@main_bp.route("/get_account_page", methods=["POST"])
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

@main_bp.route('/new_expense', methods=['POST'])
@login_required
@check_confirmed
def new_expense(edited=False):
  try:
    form = NewExpenseForm()
    names = form.name.data

    if not form.validate():
      errors = {field.name: field.errors for field in form if field.errors}
      log_write(f"NEW EXPENSE FAIL: Errors - {errors}")
      return jsonify(success=False, errors=errors)

    uuid = get_uuid_from_cookie()
    names = [n.lstrip() for n in names.split(',') if n.lstrip()] #Parse name field separated by commas
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
    return jsonify({'success': True, 'toasts': toasts})
  
  except CustomException as e:
    return jsonify({'success': False, "toasts": f"ERROR: {str(e)}"})

@main_bp.route('/new_transfer', methods=['POST'])
@login_required
@check_confirmed
def new_transfer(edited=False):
  try:
    form = NewTransferForm()
    names = form.name.data

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
  
  except CustomException as e:
    toasts.append(str(e))
    return jsonify({'success': False, 'toasts': toasts})
  

@main_bp.route('/new_income', methods=['POST'])
@login_required
@check_confirmed
def new_income(edited=False):
  try:
    form = NewIncomeForm()
    names = form.name.data

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
  
  except CustomException as e:
    toasts.append(str(e))
    return jsonify({'success': False, 'toasts': toasts})

@main_bp.route('/fill_envelopes', methods=['POST'])
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

@main_bp.route('/edit_delete_envelope', methods=['POST'])
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
@main_bp.route('/edit_delete_account', methods=['POST'])
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

@main_bp.route('/edit_transaction', methods=['POST'])
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

@main_bp.route('/api/load-more', methods=['POST'])
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
  
@main_bp.route('/api/load-static-html', methods=["POST"])
@login_required
@check_confirmed
def load_static_html():
  return jsonify({
    'edit_envelope_row': render_template('edit_envelope_row.html'),
    'edit_account_row': render_template('edit_account_row.html'),
    't_editor_new_env_row': render_template('transaction_editor_new_envelope_row.html')
  })


@main_bp.route('/bug-report', methods=['POST'])
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
        screenshot.save(os.path.join(current_app.config['UPLOAD_FOLDER'], screenshot.filename))
    
    send_bug_report_email_developer(uuid, name, email, desc, bug_report_id, timestamp, screenshot)  # Send bug report email to the developer
    send_bug_report_email_user(name, email, bug_report_id) # Send confirmation email to the user
    
    return jsonify({'toasts': ["Thank you! Your bug report has been submitted!"]})
  except CustomException as e:
    return jsonify({"error": str(e)})

def send_bug_report_email_developer(uuid, name, email, desc, bug_report_id, timestamp, screenshot):
  msg = Message(f'Budgeteer: Bug Report from {email}', sender=current_app.config["MAIL_USERNAME"], recipients=[current_app.config["MAIL_USERNAME"]])
  if screenshot:
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], screenshot.filename)
    with current_app.open_resource(file_path) as fp:
      msg.attach(screenshot.filename, "image/png", fp.read())
    os.remove(file_path)
  msg.html = render_template("emails/bug_report_developer.html", uuid=uuid, name=name, email=email, desc=desc, bug_report_id=bug_report_id, timestamp=timestamp)
  current_app.mail.send(msg)

def send_bug_report_email_user(name, email, bug_report_id):
  msg = Message('Budgeteer: Your Bug Report Has Been Received', sender=current_app.config["MAIL_USERNAME"], recipients=[email])
  msg.html = render_template("emails/bug_report_user.html", name=name, email=email, bug_report_id=bug_report_id)
  current_app.mail.send(msg)

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