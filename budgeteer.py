  # FEATURES TO ADD
  #
  # Scheduled transactions (chrontab?)
  # Ajax for accounts/envelopes views
  # Quick fill for envelopes based on budget
  # Accounts/login
  # hoverable note function
  # sort transaction lists (multiple ways date, amount, name, etc.)
  # Transaction search
  # loading spinners
  # Placeholder transactions (for deleted/edited accounts/envelopes)
  # import transactions from bank
  # Spending graphs/budgeting tracking
  # Add keyboard-tab select function on materialize select so that it's more user friendly
  # Add cash back feature
  # Split envelope transfer?
  # Photo of recipt (maybe until reconciled)
  #
  # Link to other transactions in descriptions??
  # envelope average spending /spent last month
  # cover overspending button
  # goals function (target category balance / balance by date)
  # average spent in each envelope
  # one click reconcile button
  # use join clause on get_trasactions() to get account name and envelope name
  #     This might mot actually be more efficient unless I add a feature where
  #     there's a current account balance associated with every transaction
  #
  # BUG FIXES:
  # Helper text overflow on medium screen envelope editor
  # Context menu not available on non-mobile transactions right click
  #
  # THINGS TO MAYBE DO:
  #
  # Update get_transactions to use join clause for account_name and deleted info
  # fix template structure for transactions and envelope/selectors

from flask import Flask, render_template, url_for, request, redirect, jsonify
from database import *
from datetime import datetime
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
    return render_template('layout.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view, offset=offset, limit=limit)

@app.route("/envelope/<envelope_id>", methods=['GET'], )
def envelope(envelope_id):
    (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,0,50)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total(USER_ID)
    current_view = get_envelope(envelope_id).name
    return render_template('layout.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view, offset=offset, limit=limit)

@app.route("/account/<account_id>", methods=['GET'], )
def account(account_id):
    (transactions_data, offset, limit) = get_account_transactions(account_id,0,50)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total(USER_ID)
    current_view = get_account(account_id).name
    return render_template('layout.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view, offset=offset, limit=limit)

@app.route('/new_expense', methods=['POST'])
def new_expense():
    name = request.form['name']
    amounts = request.form.getlist('amount')
    envelope_ids = request.form.getlist('envelope_id')
    account_id = request.form['account_id']
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    scheduled = request.form.getlist('scheduled')
    schedule = request.form['schedule']
    if len(scheduled) == 0:
      schedule = None
    for i in range(len(amounts)):
        amounts[i] = int(round(float(amounts[i]) * 100))
        envelope_ids[i] = int(envelope_ids[i])
    t = Transaction(BASIC_TRANSACTION, name, amounts, date, envelope_ids, account_id, None, note, schedule, False, USER_ID)
    if len(envelope_ids) == 1:
        t.grouping = gen_grouping_num()
        t.envelope_id = envelope_ids[0]
        t.amt = amounts[0]
        insert_transaction(t)
    else:
        t.type = SPLIT_TRANSACTION
        new_split_transaction(t)
    return 'Successfully added new expense!'

@app.route('/new_transfer', methods=['POST'])
def new_transfer():
    transfer_type = int(request.form['transfer_type'])
    name = request.form['name']
    amount = int(round(float(request.form['amount'])*100))
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    scheduled = request.form.getlist('scheduled')
    schedule = request.form['schedule']
    if len(scheduled) == 0:
      schedule = None
    if (transfer_type == 2):
        to_account = request.form['to_account']
        from_account = request.form['from_account']
        account_transfer(name, amount, date, to_account, from_account, note, schedule, USER_ID)
    elif (transfer_type == 1):
        to_envelope = request.form['to_envelope']
        from_envelope = request.form['from_envelope']
        envelope_transfer(name, amount, date, to_envelope, from_envelope, note, schedule, USER_ID)
    else:
        print('What the heck are you even trying to do you twit?')
    return 'Successfully added new transfer!'


@app.route('/new_income', methods=['POST'])
def new_income():
    name = request.form['name']
    amount = int(round(float(request.form['amount'])*100))
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    account_id = request.form['account_id']
    note = request.form['note']
    scheduled = request.form.getlist('scheduled')
    schedule = request.form['schedule']
    if len(scheduled) == 0:
      schedule = None
    t = Transaction(INCOME, name, -1 * amount, date, 1, account_id, gen_grouping_num(), note, schedule, False, USER_ID)
    insert_transaction(t)
    return 'Successfully added new income!'

@app.route('/fill_envelopes', methods=['POST'])
def fill_envelopes():
    name = request.form['name']
    amounts = request.form.getlist('fill-amount')
    print(amounts)
    envelope_ids = request.form.getlist('envelope_id')
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    scheduled = request.form.getlist('scheduled')
    schedule = request.form['schedule']
    if len(scheduled) == 0:
      schedule = None
    deletes =[]
    for i in range(len(amounts)):
        amounts[i] = int(round(float(amounts[i])*100))
        envelope_ids[i] = int(envelope_ids[i])
        if amounts[i] == 0:
            deletes.append(i)
    for index in reversed(deletes):
        amounts.pop(index)
        envelope_ids.pop(index)
    t = Transaction(ENVELOPE_FILL, name, amounts, date, envelope_ids, None, None, note, schedule, False, USER_ID)
    envelope_fill(t)
    return 'Envelopes successfully filled!'

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
    id = int(request.form['edit-id'])
    type = int(request.form['type'])
    delete_transaction(id)
    if (type == BASIC_TRANSACTION):
        new_expense()
    elif (type == ENVELOPE_TRANSFER or type == ACCOUNT_TRANSFER):
        new_transfer()
    elif (type == INCOME):
        new_income()
    elif (type == SPLIT_TRANSACTION):
        new_expense()
    elif (type == ENVELOPE_FILL):
        fill_envelopes()
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
    elif 'envelope/' in url:
        regex = re.compile('envelope/(\d+)')
        envelope_id = int(regex.findall(url)[0])
        (transactions_data, offset, limit) = get_envelope_transactions(envelope_id,0,50)
    else:
        (transactions_data, offset, limit) = get_transactions(0,50)
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