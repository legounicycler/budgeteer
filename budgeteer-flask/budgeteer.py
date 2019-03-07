  # Features to add
  # Photo of recipt (maybe until reconciled)
  # envelope average spending/ spent last month
  # cover overspending button
  # goals function (target category balance/ balance by date)
  # average spent in each envelope
  # sort transaction lists (multiple ways date, amount, name, etc.)
  # one click reconcile button
  # temporary envelopes (archive feature)
  #
  #
  #
  #
  #
  # THINGS TO DO STILL
  #
  # Form validations
  # Envelope/Account editors
  # Add functionality to transaction editor
  # Make date formatter more efficient (materialize docs for datepicker?)
  # add toasts for each submit thingy

from flask import Flask, render_template, url_for, request, redirect
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
    envelopes_data = get_envelope_list()
    accounts_data = get_account_list()
    total_funds = '$%.2f' % get_total()
    current_view = 'All transactions'
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, envelopes_data=envelopes_data, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route("/envelope/<envelope_id>", methods=['GET'], )
def envelope(envelope_id):
    transactions_data = get_envelope_transactions(envelope_id)
    envelopes_data = get_envelope_list()
    accounts_data = get_account_list()
    total_funds = '$%.2f' % get_total()
    current_view = get_envelope(envelope_id).name
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, envelopes_data=envelopes_data, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route("/account/<account_id>", methods=['GET'], )
def account(account_id):
    transactions_data = get_account_transactions(account_id)
    envelopes_data = get_envelope_list()
    accounts_data = get_account_list()
    total_funds = '$%.2f' % get_total()
    current_view = get_account(account_id).name
    return render_template('data.html', t_type_dict=t_type_dict, t_type_dict2 = t_type_dict2, envelopes_data=envelopes_data, accounts_data=accounts_data, transactions_data=transactions_data, total_funds=total_funds, current_view=current_view)

@app.route('/new_expense', methods=['POST'])
def new_expense():
    name = request.form['name']
    amount = float(request.form['amount'])
    date = datetime.strptime(request.form['date'], '%d %B, %Y')
    envelope_id = request.form['envelope_id']
    account_id = request.form['account_id']
    note = request.form['note']
    t = Transaction(BASIC_TRANSACTION, name, amount, date, envelope_id, account_id, 0, note)
    insert_transaction(t)
    return redirect(url_for('home'))

@app.route('/new_transfer', methods=['POST'])
def new_transfer():
    transfer_type = request.form['transfer_type']
    name = request.form['name']
    amount = float(request.form['amount'])
    date = datetime.strptime(request.form['date'], '%d %B, %Y')
    note = request.form['note']

    if (transfer_type == 'ACCOUNT_TRANSFER'):
        to_account = request.form['to_account']
        from_account = request.form['from_account']
        account_transfer(name, amount, date, to_account, from_account, note)
    elif (transfer_type == 'ENVELOPE_TRANSFER'):
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
    date = datetime.strptime(request.form['date'], '%d %B, %Y')
    # envelope_id = request.form['envelope_id']
    account_id = request.form['account_id']
    note = request.form['note']
    t = Transaction(INCOME, name, -1 * amount, date, 1, account_id, 0, note)
    insert_transaction(t)
    print_database()
    return redirect(url_for('home'))

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():

    return redirect(url_for('home'))

@app.route('/delete_transaction_page', methods=['POST'])
def delete_transaction_page():
    id = request.form['delete-id']
    id = int(id)
    delete_transaction(id)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)