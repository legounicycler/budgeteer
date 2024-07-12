from textLogging import log_write

class CustomException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.log_exception()
        
    def log_exception(self):
        log_write(f"EXCEPTION: {str(self)}")

class UnauthorizedAccessError(CustomException):
    pass

class TransactionNotFoundError(CustomException):
    pass

class EnvelopeNotFoundError(CustomException):
    pass

class AccountNotFoundError(CustomException):
    pass

class UserNotFoundError(CustomException):
    pass

class UserIdCookieNotFoundError(CustomException):
    def __init__(self):
        super().__init__("User ID cookie not found")

class InvalidFormDataError(CustomException):
    pass

class TimestampParseError(CustomException):
    pass

class InvalidFileSizeError(CustomException):
    pass

class InvalidFileTypeError(CustomException):
    pass

class RecaptchaFailError(CustomException):
    def __init__(self, response):
        if response['success'] is False:
            log_write(f"EXCEPTION: ReCaptcha Fail - Success: {response['success']}, error-codes: {response['error-codes']}", "LoginAttemptsLog.txt")
        else:
            log_write(f"EXCEPTION: ReCaptcha Fail - Success: {response['success']}, Hostname: {response['hostname']}, Timestamp: {response['challenge_ts']}", "LoginAttemptsLog.txt")
        super().__init__("Error: ReCaptcha failed!")

class OtherError(CustomException):
    pass