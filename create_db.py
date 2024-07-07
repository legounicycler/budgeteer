from database import *
import platform
    
if __name__ == "__main__":
    platform = platform.system()
    if platform == 'Windows':
        database = 'C:\\Users\\norma\\Documents\\Github\\budgeteer\\database.sqlite'
    else:
        database = '/home/opc/database.sqlite'
    conn = sqlite3.connect(database, check_same_thread=False)
    c = conn.cursor()
    create_tables(conn, c)
    conn.close()