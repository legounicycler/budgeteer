from datetime import datetime

def log_write(text, filename="EventLog.txt"):
    """
    Writes a message to an EventLog.txt file
    """
    with open(f"logs/{filename}",'a') as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + " " + text+"\n")