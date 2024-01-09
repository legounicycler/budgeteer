from datetime import datetime

def log_write(text):
    """
    Writes a message to an EventLog.txt file
    """
    with open("EventLog.txt",'a') as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + " " + text+"\n")