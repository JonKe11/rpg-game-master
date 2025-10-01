# backend/app/core/exceptions.py
from typing import Any, Optional

class AppException(Exception):
    """Base application exception"""
    def __init__(
        self, 
        message: str, 
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class NotFoundError(AppException):
    """Resource not found"""
    def __init__(self, resource: str, id: Any):
        super().__init__(
            message=f"{resource} with id {id} not found",
            code="NOT_FOUND",
            status_code=404
        )

class ValidationError(AppException):
    """Validation error"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class AIError(AppException):
    """AI processing error"""
    def __init__(self, message: str = "AI processing failed"):
        super().__init__(
            message=message,
            code="AI_ERROR",
            status_code=503
        )