class BaseError(Exception):
    """Base error class for custom exceptions"""
    def __init__(self, message, status_code=500, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or status_code

class ValidationError(BaseError):
    """Raised when input validation fails"""
    def __init__(self, message, field=None):
        super().__init__(message, status_code=400, error_code=4000)
        self.field = field

class AuthenticationError(BaseError):
    """Raised when authentication fails"""
    def __init__(self, message):
        super().__init__(message, status_code=401, error_code=4010)

class AuthorizationError(BaseError):
    """Raised when authorization fails"""
    def __init__(self, message):
        super().__init__(message, status_code=403, error_code=4030)

class ResourceNotFoundError(BaseError):
    """Raised when a requested resource is not found"""
    def __init__(self, message, resource_type=None):
        super().__init__(message, status_code=404, error_code=4040)
        self.resource_type = resource_type

class RateLimitError(BaseError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message, limit=None, reset_time=None):
        super().__init__(message, status_code=429, error_code=4290)
        self.limit = limit
        self.reset_time = reset_time

class FileError(BaseError):
    """Raised when there are issues with file operations"""
    def __init__(self, message, file_type=None, max_size=None):
        super().__init__(message, status_code=400, error_code=4001)
        self.file_type = file_type
        self.max_size = max_size

class ProcessingError(BaseError):
    """Raised when video/audio processing fails"""
    def __init__(self, message, stage=None):
        super().__init__(message, status_code=500, error_code=5000)
        self.stage = stage

class StorageError(BaseError):
    """Raised when storage operations fail"""
    def __init__(self, message, operation=None):
        super().__init__(message, status_code=500, error_code=5001)
        self.operation = operation

class ConfigurationError(BaseError):
    """Raised when there are configuration issues"""
    def __init__(self, message, config_key=None):
        super().__init__(message, status_code=500, error_code=5002)
        self.config_key = config_key

class ExtensionError(BaseError):
    """Raised when there are extension-specific issues"""
    def __init__(self, message, extension_id=None):
        super().__init__(message, status_code=400, error_code=4002)
        self.extension_id = extension_id

class SessionError(BaseError):
    """Raised when there are session-related issues"""
    def __init__(self, message, session_id=None):
        super().__init__(message, status_code=400, error_code=4003)
        self.session_id = session_id

# Error code ranges:
# 4000-4099: Validation errors
# 4100-4199: Authentication errors
# 4200-4299: Authorization errors
# 4300-4399: Resource errors
# 4400-4499: Request errors
# 4500-4599: Extension errors
# 5000-5099: Processing errors
# 5100-5199: Storage errors
# 5200-5299: Configuration errors
