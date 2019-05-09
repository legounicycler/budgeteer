  # FEATURES TO ADD
  #
  # Scheduled transactions
  # Multiple delete function
  # hoverable note function
  # sort transaction lists (multiple ways date, amount, name, etc.)
  # Transaction search
  # Add keyboard-tab select function on materialize select so that it's more user friendly
  # add cash back feature!!!
  # Spending graphs
  # Photo of recipt (maybe until reconciled)
  #
  # envelope average spending /spent last month
  # cover overspending button
  # goals function (target category balance / balance by date)
  # average spent in each envelope
  # one click reconcile button
  # use join clause on get_trasactions() to get account name and envelope name
  #     This might mot actually be more efficient unless I add a feature where
  #     there's a current account balance associated with every transaction
  #
  #
  #
  #
  #
  # THINGS TO DO STILL (ALPHA 1.0)
  #
  # Improve envelope fill/ envelope fill editor
  # Add envelope filler to data reload
  # Make sure envelope filler editor works with deleted envelopes
  # Fix CSS so it's mobile responsive
  # Change ajax in so that the site only loads 50 transactions at a time
  #     PROBLEM: If you load specifically 50 transactions at a time, but the 50th
  #     is a part of a split transaction, you're not getting the complete data needed
  #     to render the page correctly
  # Improve documentation on every page
  #
  #
  # QUESTIONS:
  # Is the layout structure good?
  # How to avoid problem with set number of transactions
  # How would I do scheduled transactions?
  # General login stuff
  #
  # THINGS TO MAYBE DO:
  #
  # Change update_transaction function to actually use SQLite UPDATE function

from flask import Flask, render_template, url_for, request, redirect, jsonify
from database import *
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'da3e7b955be0f7eb264a9093989e0b46'

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

@app.route("/")
@app.route("/home", methods=['GET'])
def home():
    transactions_data = get_transactions()
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total()
    current_view = 'All transactions'
    return render_template('layout.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route("/envelope/<envelope_id>", methods=['GET'], )
def envelope(envelope_id):
    transactions_data = get_envelope_transactions(envelope_id)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total()
    current_view = get_envelope(envelope_id).name
    return render_template('layout.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route("/account/<account_id>", methods=['GET'], )
def account(account_id):
    transactions_data = get_account_transactions(account_id)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total()
    current_view = get_account(account_id).name
    return render_template('layout.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route('/new_expense', methods=['POST'])
def new_expense():
    name = request.form['name']
    amounts = request.form.getlist('amount')
    envelope_ids = request.form.getlist('envelope_id')
    account_id = request.form['account_id']
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    for i in range(len(amounts)):
        amounts[i] = int(float(amounts[i]) * 100)
        envelope_ids[i] = int(envelope_ids[i])
    t = Transaction(BASIC_TRANSACTION, name, amounts, date, envelope_ids, account_id, 0, note)
    if len(envelope_ids) == 1:
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
    amount = int(float(request.form['amount'])*100)
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    if (transfer_type == 2):
        to_account = request.form['to_account']
        from_account = request.form['from_account']
        account_transfer(name, amount, date, to_account, from_account, note)
    elif (transfer_type == 1):
        to_envelope = request.form['to_envelope']
        from_envelope = request.form['from_envelope']
        envelope_transfer(name, amount, date, to_envelope, from_envelope, note)
    else:
        print('What the heck are you even trying to do you twit?')
    return 'Successfully added new transfer!'


@app.route('/new_income', methods=['POST'])
def new_income():
    name = request.form['name']
    amount = int(float(request.form['amount'])*100)
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    account_id = request.form['account_id']
    note = request.form['note']
    t = Transaction(INCOME, name, -1 * amount, date, 1, account_id, 0, note)
    insert_transaction(t)
    return 'Successfully added new income!'

@app.route('/fill_envelopes', methods=['POST'])
def fill_envelopes():
    name = request.form['name']
    amounts = request.form.getlist('fill-amount')
    envelope_ids = request.form.getlist('envelope_id')
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    deletes =[]
    for i in range(len(amounts)):
        amounts[i] = int(float(amounts[i])*100)
        envelope_ids[i] = int(envelope_ids[i])
        if amounts[i] == 0:
            deletes.append(i)
    for index in deletes:
        amounts.pop(index)
        envelope_ids.pop(index)
    t = Transaction(ENVELOPE_FILL, name, amounts, date, envelope_ids, None, 0, note)
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
        old_accounts.append([old_ids[i], old_names[i], int(float(old_balances[i])*100)])
    for i in range(len(new_names)):
        new_accounts.append([new_names[i], int(float(new_balances[i])*100)])
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
        old_envelopes.append([old_ids[i], old_names[i], int(float(old_budgets[i])*100)])
    for i in range(len(new_names)):
        new_envelopes.append([new_names[i], int(float(new_budgets[i])*100)])
    edit_envelopes(old_envelopes, new_envelopes)
    return 'Envelopes successfully updated!'

@app.route('/api/data-reload', methods=['POST'])
def transactions_function():
    # needs to change based on what page you're on
    url = request.get_json()['url']
    if 'account/' in url:
        regex = re.compile('account/(\d+)')
        account_id = int(regex.findall(url)[0])
        transactions_data = get_account_transactions(account_id)
    elif 'envelope/' in url:
        regex = re.compile('envelope/(\d+)')
        envelope_id = int(regex.findall(url)[0])
        transactions_data = get_envelope_transactions(envelope_id)
    else:
        transactions_data = get_transactions()

    print(transactions_data)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    data = {}
    data['total'] = get_total()
    data['unallocated'] = envelopes_data[1].balance
    data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data)
    data['accounts_html'] = render_template('accounts.html', active_accounts=active_accounts, accounts_data=accounts_data)
    data['envelopes_html'] = render_template('envelopes.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data)
    data['account_selector_html'] = render_template('account_selector.html', accounts_data=accounts_data)
    data['envelope_selector_html'] = render_template('envelope_selector.html', envelopes_data=envelopes_data)
    data['envelope_editor_html'] = render_template('envelope_editor.html', envelopes_data=envelopes_data)
    data['account_editor_html'] = render_template('account_editor.html', accounts_data=accounts_data)
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)