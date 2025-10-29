from database import *
from secret import LOCAL_DATABASE_PATH
import sys
from blueprints.auth import generate_uuid
from database import User, insert_user, confirm_user

create_default_user = False
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--default-user" or arg == "-du":
                # Check if the script is run with the --default-user or -du argument
                 # If so, create a default user to avoid having to manually create one and sending a confirmation email
                create_default_user = True
                
    database = LOCAL_DATABASE_PATH

    try:
        with open(database, "x") as f:
            db = Database(database)
            db.get_conn()
            db.create_tables()
            if create_default_user:
                (new_password_hash, new_password_salt) = User.hash_password("password")
                new_user = User(generate_uuid(), "email@example.com", new_password_hash, new_password_salt, "Firstname", "Lastname", datetime.now())
                insert_user(new_user)
                confirm_user(new_user)
            db.close_conn()
    except FileExistsError:
        print(f"Database file already exists at {database}")
        print("If you want to recreate the database, please delete the existing file and run this script again.")
