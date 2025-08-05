def datetimeformat(d, format='%m/%d/%Y'):
    """
    Accepts a datetime object and returns a formatted string for displaly in HTML
    """
    return d.strftime(format)

def datetimeformatshort(d, format='%b %d\n%Y'):
    """
    Accepts a datetime object and returns a formatted string for displaly in HTML
    """
    return d.strftime(format)

def balanceformat(number):
    """
    Accepts a float or int representing transaction amount and converts into a string with a "$" and "-" if necessary for display in HTML
    """
    if number is None:
        string = "NAN"
    else:
        string = '$%.2f' % abs(number)
        if number < 0:
            string = '-' + string
    return string

def inputformat(num):
    """
    Accepts a float/int and converts it into a string with two decimal places for display in HTML input field (so no "$" before number)
    """
    return '%.2f' % num