from database import *

bad_e_ids = []
bad_e_amts_new = []
bad_e_names = []
bad_a_ids = []
bad_a_amts_new = []
bad_a_names = []

# NOTE: None of this considers deleted accounts/envelopes, but that doesn't seem to be a problem
# NOTE: This only works for a 1 user database. This will have to be updated when multi-accounts gets fully implemented

def health_check():
    print("----------------------")
    print("BEGINNING HEALTH CHECK")
    print("----------------------\n")
    c.execute("SELECT user_id FROM accounts GROUP BY user_id")
    user_ids = c.fetchall()
    for row in user_ids:
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

        print("\n>>> CHECKING ACCOUNTS <<<")
        c.execute("SELECT id,balance,name from accounts")
        accounts = c.fetchall()
        for row in accounts:
            account_name = row[2]
            account_id = row[0]
            # get account balance according to database
            account_balance = row[1]
            # get account balance according to summed transaction totals
            c.execute("SELECT SUM(amount) from transactions WHERE account_id=? AND date(day) <= date('now')", (account_id,))
            a_balance = c.fetchone()[0]
            if a_balance is None:
                a_balance = 0
            if (-1*account_balance == a_balance):
                print("HEALTHY --->", account_name, account_id)
            else:
                bad_a_ids.append(account_id)
                bad_a_amts_new.append(a_balance)
                print("WRONG!! --->", account_name, account_id)
                print("     Account balance VS Summed balance")
                print("    ", -1*account_balance, 'vs', a_balance)
                print("Difference: ", abs(a_balance + account_balance))

        print("\n>>> CHECKING ENVELOPES <<<")
        c.execute("SELECT id,balance,name from envelopes")
        envelopes = c.fetchall()
        for row in envelopes:
            envelope_name = row[2]
            envelope_id = row[0]
            # get envelope balance according to database
            envelope_balance = row[1]
            # get envelope balance according to summed transaction totals
            c.execute("SELECT SUM(amount) from transactions WHERE envelope_id=? AND date(day) <= date('now')", (envelope_id,))
            e_balance = c.fetchone()[0]
            if e_balance is None:
                e_balance = 0
            if (-1*envelope_balance == e_balance):
                print("HEALTHY --->", envelope_name, envelope_id)
            else:
                bad_e_ids.append(envelope_id)
                bad_e_amts_new.append(e_balance)
                print("WRONG!! --->", envelope_name, envelope_id)
                print("     Envelope balance VS Summed balance")
                print("    ", -1*envelope_balance, 'vs', e_balance)
                print("Difference: ", abs(e_balance + envelope_balance))

        print("\nBad Account IDs:", bad_a_ids)
        print("Bad Envelope IDs:", bad_e_ids)

        print("\n---------------------")
        print("HEALTH CHECK COMPLETE")
        print("---------------------\n")

        if (len(bad_a_ids) > 0 or len(bad_e_ids) > 0):
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
    update_reconcile_amounts(a_id, first_t_id, INSERT)
    print("Account", a_id, "reconcile balances updated.")

def envelope_heal(e_id, new_balance):
    print("Healing envelope", e_id)
    update_envelope_balance(e_id, -1*new_balance)
    print("Envelope", e_id, "balance set to", new_balance)


def main():
    health_check()
    log_write('-----Account healed!-----\n')

if __name__ == "__main__":
    main()
