from requests.exceptions import ConnectionError
from sqlalchemy.exc import IntegrityError as DatabaseIntegrityError


class CumException(Exception):
    """Base class for all cum exceptions."""

    def __init__(self, message=''):
        self.message = message

    def __str__(self):
        return repr(self.message)


class LoginError(CumException):
    pass


class ScrapingError(CumException):
    pass


class ConfigError(CumException):
    """Exception that is thrown when cum encounters a malformed configuration
    file. Accepts a string representing the raw text of the configuration file,
    the cursor position as a (row, column) tuple and a message.
    """

    def __init__(self, config, cursor, message=''):
        self.config = config
        self.cursor = cursor
        super().__init__(message)
