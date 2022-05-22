from database import *

bad_e_ids = []
bad_e_amts_new = []
bad_e_names = []
bad_a_ids = []
bad_a_amts_new = []
bad_a_names = []

# NOTE: This only works for a 1 user database. This will have to be updated when multi-accounts gets fully implemented

def health_check():
    print("----------------------")
    print("BEGINNING HEALTH CHECK")
    print("----------------------\n")
    mismatched_totals = False
    c.execute("SELECT user_id FROM accounts GROUP BY user_id")
    user_ids = c.fetchall()
    for row in user_ids:

        # 1. CONFIRM CONSISTENCY BETWEEN SUM OF ENVELOPE BALANCES AND SUM OF ACCOUNT BALANCES
        user_id = row[0]
        print(">>> CHECKING TOTALS FOR USER ID:", user_id, "<<<")
        # Get accounts total
        c.execute("SELECT SUM(balance) FROM accounts WHERE user_id=?", (user_id,))
        accounts_total = c.fetchone()[0]
        # Get envelopes total
        c.execute("SELECT SUM(balance) FROM envelopes WHERE user_id=?", (user_id,))
        envelopes_total = c.fetchone()[0]
        print("Accounts total:", accounts_total)
        print("Envelopes total:", envelopes_total)
        if (accounts_total == envelopes_total):
            print("HEALTHY")
        else:
            print("INCONSISTENT!!!")
            mismatched_totals = True

        # 2. CONFIRM THAT THESE THREE VALUES ARE THE SAME
        #     a. Balances stored in accounts table
        #     b. Sum of all transactions in an account
        #     c. Account reconcile balance on latest transaction
        print("\n>>> CHECKING ACCOUNTS <<<")
        c.execute("SELECT id,balance,name from accounts")
        accounts = c.fetchall()
        for row in accounts:
            a_name = row[2]
            a_id = row[0]

            # a. Get account balance according to database
            a_balance_db = -1*row[1]

            # b. Get account balance according to summed transaction totals
            c.execute("SELECT SUM(amount) from transactions WHERE account_id=? AND date(day) <= date('now', 'localtime')", (a_id,))
            a_balance_summed = c.fetchone()[0]
            if a_balance_summed is None: #If there's no transactions in the account yet, placeholder of zero
                a_balance_summed = 0

            # c. Get account balance according to latest account reconcile value
            c.execute("SELECT a_reconcile_bal FROM transactions WHERE account_id=? AND date(day) <= date('now', 'localtime') ORDER by day DESC, id DESC LIMIT 1", (a_id,))
            a_balance_reconcile_tuple = c.fetchone()
            if a_balance_reconcile_tuple is None: #If there's no transactions in the account yet, placeholder of zero
                a_balance_reconcile = 0
            else:
                a_balance_reconcile = -1*a_balance_reconcile_tuple[0]

            # d. Check for health!
            if (a_balance_db == a_balance_summed and a_balance_db == a_balance_reconcile and a_balance_summed == a_balance_reconcile):
                print(f"HEALTHY ---> (ID:{a_id}) {a_name}")
            else:
                bad_a_ids.append(a_id)
                bad_a_amts_new.append(a_balance_summed)
                print(f"WRONG!! ---> (ID:{a_id}) {a_name}")
                print("     Account balance VS Summed balance VS Reconcile balance")
                print("    ", -1*a_balance_db, 'vs', a_balance_summed, 'vs',a_balance_reconcile)
                print("Difference: ", abs(a_balance_summed + a_balance_db))

        # 3. CONFIRM THAT THESE THREE VALUES ARE THE SAME
        #     a. Balances stored in envelopes table
        #     b. Sum of all transactions in an envelope
        #     c. Envelope reconcile balance on latest transaction
        print("\n>>> CHECKING ENVELOPES <<<")
        c.execute("SELECT id,balance,name from envelopes")
        envelopes = c.fetchall()
        for row in envelopes:
            e_name = row[2]
            e_id = row[0]

            # a. Get envelope balance according to database
            e_balance_db = -1*row[1]

            # b. Get envelope balance according to summed transaction totals
            c.execute("SELECT SUM(amount) from transactions WHERE envelope_id=? AND date(day) <= date('now', 'localtime')", (e_id,))
            e_balance_summed = c.fetchone()[0]
            if e_balance_summed is None: #If there's no transactions in the envelope yet, placeholder of zero
                e_balance_summed = 0

            # c. Get envelope balance according to latest envelope reconcile value
            c.execute("SELECT e_reconcile_bal FROM transactions WHERE envelope_id=? AND date(day) <= date('now', 'localtime') ORDER by day DESC, id DESC LIMIT 1", (e_id,))
            # NOTE: Sum of e_reconcile_bal to avoid nonetype error when no transactions are in the envelope
            e_balance_reconcile_tuple = c.fetchone()
            if e_balance_reconcile_tuple is None: #If there's no transactions in the envelope yet, placeholder of zero
                e_balance_reconcile = 0
            else:
                e_balance_reconcile = -1*e_balance_reconcile_tuple[0]

            # d. Check for health!
            if (e_balance_db == e_balance_summed and e_balance_db == e_balance_reconcile and e_balance_summed == e_balance_reconcile):
                print(f"HEALTHY ---> (ID:{e_id}) {e_name}")
            else:
                bad_e_ids.append(e_id)
                bad_e_amts_new.append(e_balance_summed)
                print(f"WRONG!! ---> (ID:{e_id}) {e_name}")
                print("     Envelope balance VS Summed balance VS Reconcile Balance")
                print("    ", e_balance_db, 'vs', e_balance_summed, 'vs', e_balance_reconcile)
                print("Difference: ", abs(e_balance_db + e_balance_summed))

        print("\nBad Account IDs:", bad_a_ids)
        print("Bad Envelope IDs:", bad_e_ids)

        print("\n---------------------")
        print("HEALTH CHECK COMPLETE")
        print("---------------------\n")

        if (len(bad_a_ids) > 0 or len(bad_e_ids) > 0 or mismatched_totals == True):
            print("STATUS -> UNHEALTHY")
            choice_valid = False
            while (choice_valid == False):
                choice = input("Would you like to continue healing the database? (y/n):")
                if (choice == 'y' or choice =='Y' or choice == 'yes' or choice == 'Yes' or choice =='YES'):
                    choice_valid = True
                    print("Healing database...")
                    for i in range(0,len(bad_a_ids)):
                        account_heal(bad_a_ids[i], bad_a_amts_new[i])

                    for i in range(0,len(bad_e_ids)):
                        envelope_heal(bad_e_ids[i], bad_e_amts_new[i])
                    print("Database heal complete!")
                elif (choice == 'n' or choice == 'N' or choice =='no' or choice =='No' or choice =='NO'):
                    choice_valid = True
                    print("Database heal aborted.")
                else:
                    print("Invalid option. Try again.")

        else:
            print("STATUS -> HEALTHY")
            print("No further action required.")

def account_heal(a_id, new_balance):
    print("Healing account", a_id)
    update_account_balance(a_id, -1*new_balance)
    print("Account", a_id, "balance set to", new_balance)
    c.execute("SELECT id from transactions WHERE account_id=? ORDER BY day ASC, id ASC LIMIT 1", (a_id,))
    first_t_id = c.fetchone()[0]
    first_t = get_transaction(first_t_id)
    update_reconcile_amounts(first_t.account_id, first_t.envelope_id, first_t_id, INSERT)
    print("Account", a_id, "reconcile balances updated.")

def envelope_heal(e_id, new_balance):
    print("Healing envelope", e_id)
    update_envelope_balance(e_id, -1*new_balance)
    print("Envelope", e_id, "balance set to", new_balance)
    c.execute("SELECT id from transactions WHERE envelope_id=? ORDER BY day ASC, id ASC LIMIT 1", (e_id,))
    first_t_id = c.fetchone()[0]
    first_t = get_transaction(first_t_id)
    update_reconcile_amounts(first_t.account_id, first_t.envelope_id, first_t_id, INSERT)
    print("Envelope", e_id, "reconcile balances updated.")


def main():
    health_check()
    log_write('-----Account healed!-----\n')

if __name__ == "__main__":
    main()
