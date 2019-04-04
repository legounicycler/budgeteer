  # Features to add
  # Photo of recipt (maybe until reconciled)
  # envelope average spending /spent last month
  # cover overspending button
  # goals function (target category balance / balance by date)
  # average spent in each envelope
  # sort transaction lists (multiple ways date, amount, name, etc.)
  # one click reconcile button
  # temporary envelopes (archive feature)
  # add cash back feature!!!
  #
  #
  #
  #
  #
  # THINGS TO DO STILL
  #
  # Form validations
  # add toasts for each submit function
  # Envelope/Account editors submit functions
  # Add split transaction functionability
  # add "You don't have any transactions yet" things
  # get rid of unallocated envelope in select menus
  # change name of get_account_dict
  # change get_account_dict to disclude $ and update the rest of the code accordingly
  # Maybe add neutral class back in with grayed out color for $0.00
  # check one last time if it's possible to include blocks inside of include statments jinja2
  # sort transactions by date and id so they show up in the right order

from flask import Flask, render_template, url_for, request, redirect, jsonify
from database import *
from datetime import datetime

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
    envelopes_data = get_envelope_dict()
    accounts_data = get_account_dict()
    total_funds = '$%.2f' % get_total()
    current_view = 'All transactions'
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, envelopes_data=envelopes_data, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route("/envelope/<envelope_id>", methods=['GET'], )
def envelope(envelope_id):
    transactions_data = get_envelope_transactions(envelope_id)
    envelopes_data = get_envelope_dict()
    accounts_data = get_account_dict()
    total_funds = '$%.2f' % get_total()
    current_view = get_envelope(envelope_id).name
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, envelopes_data=envelopes_data, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route("/account/<account_id>", methods=['GET'], )
def account(account_id):
    transactions_data = get_account_transactions(account_id)
    envelopes_data = get_envelope_dict()
    accounts_data = get_account_dict()
    total_funds = '$%.2f' % get_total()
    current_view = get_account(account_id).name
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, envelopes_data=envelopes_data, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route('/new_expense', methods=['POST'])
def new_expense():
    name = request.form['name']
    amount = float(request.form['amount'])
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    envelope_id = request.form['envelope_id']
    account_id = request.form['account_id']
    note = request.form['note']
    t = Transaction(BASIC_TRANSACTION, name, amount, date, envelope_id, account_id, 0, note)
    insert_transaction(t)
    return redirect(url_for('home'))

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
    return redirect(url_for('home'))


@app.route('/new_income', methods=['POST'])
def new_income():
    name = request.form['name']
    amount = float(request.form['amount'])
    date = datetime.strptime(request.form['date'], '%m/%d/%Y')
    account_id = request.form['account_id']
    note = request.form['note']
    t = Transaction(INCOME, name, -1 * amount, date, 1, account_id, 0, note)
    insert_transaction(t)
    return redirect(url_for('home'))

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
    id = int(request.form['edit-id'])
    type = int(request.form['type'])
    delete_transaction(id)
    if (type == BASIC_TRANSACTION):
        new_expense()
    elif (type == 1 or type == 2):
        new_transfer()
    elif (type == 3):
        new_income()
    return redirect(url_for('home'))


@app.route('/delete_transaction_page', methods=['POST'])
def delete_transaction_page():
    id = int(request.form['delete-id'])
    delete_transaction(id)
    return redirect(url_for('home'))

@app.route('/api/transaction/<id>/group', methods=['GET'])
def get_json(id):
    return jsonify(get_grouped_json(id))

@app.route('/api/edit-accounts', methods=['POST'])
def edit_account():
    formValues = request.get_json()
    edit_accounts(formValues)
    return jsonify(formValues)

@app.route('/api/edit-envelopes', methods=['POST'])
def edit_envelope():
    formValues = request.get_json()
    edit_envelopes(formValues)
    return jsonify(formValues)

if __name__ == '__main__':
    app.run(debug=True)