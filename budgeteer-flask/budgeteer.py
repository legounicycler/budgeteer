  # Features to add
  # Photo of recipt (maybe until reconciled)
  # envelope average spending /spent last month
  # cover overspending button
  # goals function (target category balance / balance by date)
  # average spent in each envelope
  # sort transaction lists (multiple ways date, amount, name, etc.)
  # one click reconcile button
  # add cash back feature!!!
  #
  #
  #
  #
  #
  # THINGS TO DO STILL
  #
  # add delete warnings for account/envelope editors
  # only need with conn: when you're modifying data, not when you're selecting
  # use join clause on get_all_trasactions() to get account name and envelope name
  # add envelope fill function
  # get rid of unallocated envelope in envelope select menus
  # Change ajax in so that the site only loads 50 transactions at a time
  # Clean up some of the dirty logic and make sure conn.close isn't super important
  # Fix CSS styling so things scroll correctly
  # replace ajax account-editor and envelope-editor with a decent flask solution
  #     Similarly, get rid of hidden inputs on transaction editor for the transaction id and type
  # Get rid of the active and no-active stuff in js/css and repalce with materialize updateTextField
  # make sure the balance/amount is int (amount*100) and not float
  #
  # THINGS TO MAYBE DO:
  #
  # Change update_transaction function to actually use SQLite UPDATE function
  # check one last time if it's possible to include blocks inside of include statments jinja2
  # Maybe add neutral class back in with grayed out color for $0.00???

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
        4: 'Split Transaction'
    }

t_type_dict2 = {
    0: 'local_atm',
    1: 'swap_horiz',
    2: 'swap_vert',
    3: 'vertical_align_bottom',
    4: 'call_split'
}

@app.route("/")
@app.route("/home", methods=['GET'])
def home():
    transactions_data = get_all_transactions()
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total()
    current_view = 'All transactions'
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route("/envelope/<envelope_id>", methods=['GET'], )
def envelope(envelope_id):
    transactions_data = get_envelope_transactions(envelope_id)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total()
    current_view = get_envelope(envelope_id).name
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route("/account/<account_id>", methods=['GET'], )
def account(account_id):
    transactions_data = get_account_transactions(account_id)
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    total_funds = get_total()
    current_view = get_account(account_id).name
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route('/new_expense', methods=['POST'])
def new_expense():
    name = request.form['name']
    amounts = request.form.getlist('amount')
    envelope_ids = request.form.getlist('envelope_id')
    account_id = request.form['account_id']
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    note = request.form['note']
    for i in range(len(amounts)):
        amounts[i] = float(amounts[i])
        envelope_ids[i] = int(envelope_ids[i])
    t = Transaction(BASIC_TRANSACTION, name, amounts, date, envelope_ids, account_id, 0, note)
    if len(envelope_ids) == 1:
        t.envelope_id = envelope_ids[0]
        t.amt = amounts[0]
        insert_transaction(t)
    else:
        new_split_transaction(t)
    return 'Successfully added new expense'

@app.route('/new_transfer', methods=['POST'])
def new_transfer():
    transfer_type = int(request.form['transfer_type'])
    name = request.form['name']
    amount = float(request.form['amount'])
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
    return 'Successfully added new transfer'


@app.route('/new_income', methods=['POST'])
def new_income():
    name = request.form['name']
    amount = float(request.form['amount'])
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    account_id = request.form['account_id']
    note = request.form['note']
    t = Transaction(INCOME, name, -1 * amount, date, 1, account_id, 0, note)
    insert_transaction(t)
    return 'Successfully added new income'

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
    # this is sloppy because there's just hidden inputs in the form rather than using data attributes
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
    return 'Transaction successfully edited'

@app.route('/delete_transaction_page', methods=['POST'])
# Change this to use an <id> in the URL instead of using the hidden form thing
def delete_transaction_page():
    id = int(request.form['delete-id'])
    delete_transaction(id)
    return 'Transaction successfully deleted'

@app.route('/api/transaction/<id>/group', methods=['GET'])
def get_json(id):
    return jsonify(get_grouped_json(id))

@app.route('/api/edit-accounts', methods=['POST'])
def edit_account():
    formValues = request.get_json()
    edit_accounts(formValues)
    return 'Accounts successfully updated'

@app.route('/api/edit-envelopes', methods=['POST'])
def edit_envelope():
    formValues = request.get_json()
    edit_envelopes(formValues)
    return 'Envelopes successfully updated'

@app.route('/api/data-reload', methods=['POST'])
def transactions_function():
    # needs to change based on what page you're on
    url = request.get_json()['url']
    print(url)
    if 'account/' in url:
        regex = re.compile('account/(\d+)')
        account_id = int(regex.findall(url)[0])
        transactions_data = get_account_transactions(account_id)
    elif 'envelope/' in url:
        regex = re.compile('envelope/(\d+)')
        envelope_id = int(regex.findall(url)[0])
        transactions_data = get_envelope_transactions(envelope_id)
    else:
        transactions_data = get_all_transactions()
    (active_envelopes, envelopes_data) = get_envelope_dict()
    (active_accounts, accounts_data) = get_account_dict()
    data = {}
    data['total'] = get_total()
    data['transactions_html'] = render_template('transactions.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, transactions_data=transactions_data, active_envelopes=active_envelopes, envelopes_data=envelopes_data, active_accounts=active_accounts, accounts_data=accounts_data)
    data['accounts_html'] = render_template('accounts.html', active_accounts=active_accounts, accounts_data=accounts_data)
    data['envelopes_html'] = render_template('envelopes.html', active_envelopes=active_envelopes, envelopes_data=envelopes_data)
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)