def datetimeformat(value, format='%m/%d/%Y'):
    """
    TODO: Needs description
    """
    return value.strftime(format)

def datetimeformatshort(value, format='%b %d\n%Y'):
    """
    TODO: Needs description
    """
    return value.strftime(format)

def balanceformat(number):
    """
    Formats amount numbers into a string with a "$" and "-" if necessary for display
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
    TODO: Needs description
    """
    return '%.2f' % num