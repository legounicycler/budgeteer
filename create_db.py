from database import *
from secret import WINDOWS_DATABASE_PATH, LINUX_DATABASE_PATH
import platform
    
if __name__ == "__main__":
    platform = platform.system()
    if platform == 'Windows':
        database = WINDOWS_DATABASE_PATH
    else:
        database = LINUX_DATABASE_PATH

    try:
        with open(database, "x") as f:
            db = Database(database)
            db.get_conn()
            db.create_tables()
            db.close_conn()
    except FileExistsError:
        print(f"Database file already exists at {database}")
        print("If you want to recreate the database, please delete the existing file and run this script again.")
