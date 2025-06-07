from database import *
from config import *
import platform

app_platform = platform.system()
if app_platform == 'Windows':
    db = Database(config['development'].DATABASE_URI)
else:
    db = Database(config['production'].DATABASE_URI)

db.get_conn()
health_check([],True)