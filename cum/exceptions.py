from requests.exceptions import ConnectionError


class CumException(Exception):
    """Base class for all cum exceptions."""

    def __init__(self, message=''):
        self.message = message

    def __str__(self):
        return repr(self.message)


class ScrapingError(CumException):
    pass


class LoginError(CumException):
    pass
