from textLogging import log_write

class CustomException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.log_exception()
        
    def log_exception(self):
        log_write(f"EXCEPTION: {str(self)}")

class UnauthorizedAccessError(CustomException):
    pass

class EnvelopeNotFoundError(CustomException):
    pass

class AccountNotFoundError(CustomException):
    pass

class UserIdCookieNotFound(CustomException):
    def __init__(self):
        super().__init__("User ID cookie not found")