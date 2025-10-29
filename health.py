from database import Database, health_check
from config import LOCAL_DATABASE_PATH

db = Database(LOCAL_DATABASE_PATH)

db.get_conn()
health_check([],True)