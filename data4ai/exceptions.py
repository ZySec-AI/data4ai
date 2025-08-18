"""Custom exception hierarchy for Data4AI."""


class Data4AIError(Exception):
    """Base exception for all Data4AI errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(Data4AIError):
    """Configuration related errors."""

    pass


class APIError(Data4AIError):
    """API communication errors."""

    def __init__(self, message: str, status_code: int = None, details: dict = None):
        super().__init__(message, details)
        self.status_code = status_code


class GenerationError(Data4AIError):
    """Generation process errors."""

    pass


class ValidationError(Data4AIError):
    """Data validation errors."""

    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, details)
        self.field = field


class SchemaError(ValidationError):
    """Schema validation errors."""

    pass


class DocumentError(Data4AIError):
    """Document processing errors."""

    pass


class PublishingError(Data4AIError):
    """Dataset publishing errors."""

    pass


class RateLimitError(APIError):
    """Rate limiting errors from API."""

    def __init__(self, message: str, retry_after: int = None, details: dict = None):
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """Authentication errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=401, details=details)
