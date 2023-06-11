from database import *
import platform, csv

platform = platform.system()
if platform == 'Windows':
    database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
else:
    database = '/home/opc/database.sqlite'

conn = sqlite3.connect(database, check_same_thread=False)
c = conn.cursor()

def generate_csv(filename,data):
    c.execute("PRAGMA table_info(transactions)")
    colnames_chonk = c.fetchall()
    colnames = []
    for row in colnames_chonk:
        colnames.append(row[1])
    with open("Exported_Transactions/" + filename,'w', newline='') as out:
        csv_out=csv.writer(out)
        csv_out.writerow(colnames)
        for row in data:
            csv_out.writerow(row)
    print("Done! Your file is named " + filename)

def generate_account_csv(account_id):
    print("Generating CSV for account " + str(account_id))
    filename = "Account_" + str(account_id) + "_transactions.csv"
    c.execute("SELECT * FROM transactions WHERE user_id=? AND account_id=? ORDER BY day DESC, id DESC", (user_id,account_id))
    account_data = c.fetchall()
    generate_csv(filename,account_data)

def generate_envelope_csv(envelope_id):
    print("Generating CSV for envelope " + str(envelope_id))
    filename = "Envelope_" + str(envelope_id) + "_transactions.csv"
    c.execute("SELECT * FROM transactions WHERE user_id=? AND envelope_id=? ORDER BY day DESC, id DESC", (user_id,envelope_id))
    envelope_data = c.fetchall()
    generate_csv(filename,envelope_data)

def generate_all_csv():
    print("Generating CSV for ALL transactions")
    filename = "All_transactions.csv"
    c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY day DESC, id DESC", (user_id,))
    all_data = c.fetchall()
    generate_csv(filename,all_data)

print("Beginning transaction_export.py")
c.execute("SELECT user_id FROM accounts GROUP BY user_id")
user_ids_chonk = c.fetchall()
user_ids = []
for row in user_ids_chonk:
    user_ids.append(row[0])

user_id_choice_valid = False
while (user_id_choice_valid == False):
    print("User ID's:")
    print(user_ids)
    user_id_choice = input("Which user id are you querying? > ")
    if (user_id_choice.isdigit() and int(user_id_choice) in user_ids):
        user_id = int(user_id_choice)
        user_id_choice_valid = True
        choice = input("Would you like to export transactions from an account (1), an envelope (2), or all transactions (3)? > ")
        choice_valid = False
        while (choice_valid == False):
            if (choice == '1'):
                choice_valid = True
                c.execute("SELECT id,name FROM accounts WHERE user_id=?", (user_id,))
                accounts_chonk = c.fetchall()
                accounts = []
                for row in accounts_chonk:
                    accounts.append(row[0])
                accounts_choice_valid = False
                while (accounts_choice_valid == False):
                    print("Accounts:")
                    print(accounts_chonk)
                    accounts_choice = input("Which account's transactions would you like to export? > ")
                    if (accounts_choice.isdigit() and int(accounts_choice) in accounts):
                        accounts_choice_valid = True
                        generate_account_csv(int(accounts_choice))
                    else:
                        print("Invalid option. Try again.")
            elif (choice == '2'):
                choice_valid = True
                c.execute("SELECT id,name FROM envelopes WHERE user_id=?", (user_id,))
                envelopes_chonk = c.fetchall()
                envelopes = []
                for row in envelopes_chonk:
                    envelopes.append(row[0])
                envelopes_choice_valid = False
                while (envelopes_choice_valid == False):
                    print("Envelopes:")
                    print(envelopes_chonk)
                    envelopes_choice = input("Which envelope's transactions would you like to export? > ")
                    if (envelopes_choice.isdigit() and int(envelopes_choice) in envelopes):
                        envelopes_choice_valid = True
                        generate_envelope_csv(int(envelopes_choice))
                    else:
                        print("Invalid option. Try again.")
            elif (choice == '3'):
                choice_valid = True
                generate_all_csv()
            else:
                print("Invalid option. Try again.")
    else:
        print("Invalid option. Try again")


