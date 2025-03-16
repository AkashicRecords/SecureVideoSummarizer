class APIError(Exception):
    """Custom exception for API errors"""
    
    def __init__(self, message, status_code=500, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert the error to a dictionary for JSON response"""
        error_dict = {
            "error": self.message,
            "status_code": self.status_code
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict


class AudioProcessingError(APIError):
    """Exception for audio processing errors"""
    
    def __init__(self, message, details=None):
        super().__init__(message, status_code=400, details=details)


class TranscriptionError(APIError):
    """Exception for transcription errors"""
    
    def __init__(self, message, details=None):
        super().__init__(message, status_code=400, details=details)


class SummarizationError(APIError):
    """Exception for summarization errors"""
    
    def __init__(self, message, details=None):
        super().__init__(message, status_code=400, details=details)


class AuthenticationError(APIError):
    """Exception for authentication errors"""
    
    def __init__(self, message, details=None):
        super().__init__(message, status_code=401, details=details)


class ResourceNotFoundError(APIError):
    """Exception for resource not found errors"""
    
    def __init__(self, message, details=None):
        super().__init__(message, status_code=404, details=details) 