import os, sys, pytest
project_directory = os.path.abspath('../..')
sys.path.append(project_directory)
from budgeteer import *

# region ---------------HELPER FUNCTION TESTS---------------

# TODO: Add descriptions for these test functions and their associated functinos in filters.py
# TODO: Add more test cases here
def test_datetimeformat():
    """
    Tests datetimeformat filter function
    """
    assert datetimeformat(datetime.strptime("2022-01-01", "%Y-%m-%d")) == "01/01/2022"

# TODO: Add more test cases here
def test_datetimeformatshort():
    """
    Tests datetimeformatshort filter function
    """
    assert datetimeformatshort(datetime.strptime("2022-01-01", "%Y-%m-%d")) == "Jan 01\n2022"

def test_inputformat():
    """
    Tests inputformat filter function
    """
    assert inputformat(1000) == "1000.00"
    assert inputformat(-1000) == "-1000.00"
    assert inputformat(1000.5) == "1000.50"
    assert inputformat(-1000.5) == "-1000.50"
    assert inputformat(1000.567) == "1000.57"
    assert inputformat(-1000.567) == "-1000.57"
    assert inputformat(-1000.563) == "-1000.56"

def test_balanceformat():
    """
    Tests balanceformat filter function
    """
    assert balanceformat(1000) == "$1000.00"
    assert balanceformat(-1000) == "-$1000.00"
    assert balanceformat(1000.5) == "$1000.50"
    assert balanceformat(-1000.5) == "-$1000.50"
    assert balanceformat(1000.567) == "$1000.57"
    assert balanceformat(-1000.567) == "-$1000.57"
    assert balanceformat(-1000.563) == "-$1000.56"

# endregion ---------------HELPER FUNCTION TESTS----------------

if __name__ == "__main__":
    pytest.main()
