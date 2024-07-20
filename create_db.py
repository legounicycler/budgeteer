from database import *
import platform
    
if __name__ == "__main__":
    platform = platform.system()
    if platform == 'Windows':
        database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
    else:
        database = '/home/opc/database.sqlite'
    db = Database(database)
    db.get_conn()
    db.create_tables()
    db.close_conn()