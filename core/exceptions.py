"""Custom exceptions for the application"""


class BaseCustomException(Exception):
    """Base exception class for custom exceptions"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(BaseCustomException):
    """Raised when validation fails"""
    pass


class NotFoundError(BaseCustomException):
    """Raised when a resource is not found"""
    pass


class DuplicateError(BaseCustomException):
    """Raised when trying to create a duplicate resource"""
    pass


class BusinessLogicError(BaseCustomException):
    """Raised when business logic validation fails"""
    pass


class AuthenticationError(BaseCustomException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(BaseCustomException):
    """Raised when authorization fails"""
    pass