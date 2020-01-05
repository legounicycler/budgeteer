  # FEATURES TO ADD
  #
  # toast for scheduled transaction created
  # overlay scrollbar (simplebar?)
  # specific number of instances for scheduled transactions
  # "submit and new" button for faster transaction creations
  # don't show suggested values for numeric fields
  # error throwing instead of server crashing
  # Autoselect first form field on new envelope/account editor
  # Quick fill for envelopes based on budget
  # Add keyboard-tab select function on materialize select so that it's more user friendly
  # hoverable note function
  # sort transaction lists (multiple ways date, amount, name, etc.)
  # Transaction search
    # Accounts/login functions
  # report a bug feature for users (probably using formspree)
  # Placeholder transactions (for deleted/edited accounts/envelopes)
  # import transactions from bank
  # Spending graphs/budgeting tracking
  # allow empty values for numeric fields and have them fill as 0 (maybe with inline math)
  # Add cash back feature
  # Photo of recipt (maybe until reconciled)
  # Total envelope budget (on envelope editor) (monthly or biweekly??)
  #
  # BUG LIST:
  # Scheduling transactions with their next date in the past
    # doesn't create a future transaction at all
  #
  # THINGS TO MAYBE DO:
  #
  # Split envelope transfer?
  # abort ajax request (loading spinner page would have an 'x')
  # Update get_transactions to use join clause for account_name and deleted info
  # fix template structure for transactions and envelope/selectors
  # customization of date option
  # shift select on multiselect checkboxes
  # replace the jquery weird find structures with "for" attributes and IDS?
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

from flask import Flask, render_template, url_for, request, redirect, jsonify
from database import *
from datetime import datetime
from datetime import timedelta
import calendar
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'da3e7b955be0f7eb264a9093989e0b46'

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

@app.route("/")
@app.route("/home", methods=['GET'])
def home():
    (transactions_data, offset, limit) = get_transactions(0,50)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total(USER_ID)
    current_view = 'All transactions'
    current_total = total_funds
    return render_template('layout.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view, current_total=current_total, offset=offset, limit=limit)

@app.route("/get_envelope_page", methods=["POST"], )
def get_envelope_page():
    print(request.get_json())
    envelope_id = request.get_json()['envelope_id']
    print(envelope_id)
    (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,0,50)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    page_total = stringify(get_envelope(envelope_id).balance)
    data = {}
    data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
    data['page_total'] = page_total
    data['envelope_name'] = get_envelope(envelope_id).name
    return jsonify(data)

@app.route("/get_account_page", methods=["POST"], )
def get_account_page():
    print(request.get_json())
    account_id = request.get_json()['account_id']
    print(account_id)
    (transactions_data, offset, limit) = get_account_transactions(account_id,0,50)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    page_total = stringify(get_account(account_id).balance)
    data = {}
    data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, offset=offset, limit=limit)
    data['page_total'] = page_total
    data['account_name'] = get_account(account_id).name
    return jsonify(data)

@app.route('/new_expense', methods=['POST'])
def new_expense(edited=False):
    name = request.form['name']
    amounts = request.form.getlist('amount')
    envelope_ids = request.form.getlist('envelope_id')
    account_id = request.form['account_id']
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    scheduled = request.form.getlist('scheduled')
    scheduled = len(scheduled) != 0
    schedule = request.form['schedule']
    for i in range(len(amounts)):
        amounts[i] = int(round(float(amounts[i]) * 100))
        envelope_ids[i] = int(envelope_ids[i])
    t = Transaction(BASIC_TRANSACTION, name, amounts, date, envelope_ids, account_id, None, note, None, False, USER_ID)
    # Only insert a new scheduled transaction if it's not an edited transaction
    if scheduled and edited:
        t.schedule = schedule
    if scheduled and not edited:
        nextdate = schedule_date_calc(date,schedule)
        scheduled_t = Transaction(BASIC_TRANSACTION, name, amounts, nextdate, envelope_ids, account_id, None, note, schedule, False, USER_ID)
    if len(envelope_ids) == 1:
        t.grouping = gen_grouping_num()
        t.envelope_id = envelope_ids[0]
        t.amt = amounts[0]
        print("inserting new transaction without schedule")
        insert_transaction(t)
        if scheduled and not edited:
            scheduled_t.grouping = gen_grouping_num()
            scheduled_t.envelope_id = envelope_ids[0]
            scheduled_t.amt = amounts[0]
            print("inserting new transaction with schedule")
            insert_transaction(scheduled_t)
    else:
        t.type = SPLIT_TRANSACTION
        new_split_transaction(t)
        if scheduled and not edited:
            print("inserting new split transaction with schedule")
            scheduled_t.type = SPLIT_TRANSACTION
            new_split_transaction(scheduled_t)
    return 'Successfully added new expense!'

@app.route('/new_transfer', methods=['POST'])
def new_transfer(edited=False):
    transfer_type = int(request.form['transfer_type'])
    name = request.form['name']
    amount = int(round(float(request.form['amount'])*100))
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    scheduled = request.form.getlist('scheduled')
    scheduled = len(scheduled) != 0
    schedule = request.form['schedule']
    if (transfer_type == 2):
        to_account = request.form['to_account']
        from_account = request.form['from_account']
        if edited:
            account_transfer(name, amount, date, to_account, from_account, note, schedule, USER_ID)
        else:
            account_transfer(name, amount, date, to_account, from_account, note, None, USER_ID)
        if scheduled and not edited:
            nextdate = schedule_date_calc(date,schedule)
            account_transfer(name, amount, nextdate, to_account, from_account, note, schedule, USER_ID)
    elif (transfer_type == 1):
        to_envelope = request.form['to_envelope']
        from_envelope = request.form['from_envelope']
        if edited:
            envelope_transfer(name, amount, date, to_envelope, from_envelope, note, schedule, USER_ID)
        else:
            envelope_transfer(name, amount, date, to_envelope, from_envelope, note, None, USER_ID)
        if scheduled and not edited:
            nextdate = schedule_date_calc(date,schedule)
            envelope_transfer(name, amount, nextdate, to_envelope, from_envelope, note, schedule, USER_ID)
    else:
        print('What the heck are you even trying to do you twit?')
    return 'Successfully added new transfer!'


@app.route('/new_income', methods=['POST'])
def new_income(edited=False):
    name = request.form['name']
    amount = int(round(float(request.form['amount'])*100))
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    account_id = request.form['account_id']
    note = request.form['note']
    scheduled = request.form.getlist('scheduled')
    scheduled = len(scheduled) != 0
    schedule = request.form['schedule']
    t = Transaction(INCOME, name, -1 * amount, date, 1, account_id, gen_grouping_num(), note, None, False, USER_ID)
    if edited:
        t.schedule = schedule
    insert_transaction(t)
    if scheduled and not edited:
        nextdate = schedule_date_calc(date,schedule)
        scheduled_t = Transaction(INCOME, name, -1 * amount, nextdate, 1, account_id, gen_grouping_num(), note, schedule, False, USER_ID)
        insert_transaction(scheduled_t)
    return 'Successfully added new income!'

@app.route('/fill_envelopes', methods=['POST'])
def fill_envelopes(edited=False):
    name = request.form['name']
    amounts = request.form.getlist('fill-amount')
    envelope_ids = request.form.getlist('envelope_id')
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    scheduled = request.form.getlist('scheduled')
    scheduled = len(scheduled) != 0
    schedule = request.form['schedule']
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
    if edited:
        t.schedule = schedule
    envelope_fill(t)
    if scheduled and not edited:
        nextdate = schedule_date_calc(date,schedule)
        scheduled_t = Transaction(ENVELOPE_FILL, name, amounts, nextdate, envelope_ids, None, None, note, schedule, False, USER_ID)
        envelope_fill(scheduled_t)
    return 'Envelopes successfully filled!'

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
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
    return 'Transaction successfully edited!'

@app.route('/delete_transaction_page', methods=['POST'])
# Change this to use an <id> in the URL instead of using the hidden form thing
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
    return 'Accounts successfully updated!'


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
    return 'Envelopes successfully updated!'

@app.route('/api/data-reload', methods=['POST'])
def transactions_function():
    url = request.get_json()['url']
    if 'account/' in url:
        regex = re.compile('account/(\d+)')
        account_id = int(regex.findall(url)[0])
        (transactions_data, offset, limit) = get_account_transactions(account_id,0,50)
        page_total = stringify(get_account(account_id).balance)
    elif 'envelope/' in url:
        regex = re.compile('envelope/(\d+)')
        envelope_id = int(regex.findall(url)[0])
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
def load_more():
    current_offset = request.get_json()['offset']
    url = request.get_json()['url']
    if 'account/' in url:
        regex = re.compile('account/(\d+)')
        account_id = int(regex.findall(url)[0])
        (transactions_data, offset, limit) = get_account_transactions(account_id,current_offset,50)
    elif 'envelope/' in url:
        regex = re.compile('envelope/(\d+)')
        envelope_id = int(regex.findall(url)[0])
        (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,current_offset,50)
    else:
        (transactions_data, offset, limit) = get_transactions(current_offset,50)

    # these 2 lines shouldn't be necessary here after updating to a join clause
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    more_transactions = render_template('more_transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, accounts_data=accounts_data, envelopes_data=envelopes_data)
    return jsonify({'offset': offset, 'limit': limit, 'transactions': more_transactions})

@app.route('/api/multi-delete', methods=['POST'])
def multi_delete():
  delete_ids = request.form.getlist('delete')
  for id in delete_ids:
    delete_transaction(id)
  return 'Transactions successfully deleted!'

if __name__ == '__main__':
    app.run(debug=True)