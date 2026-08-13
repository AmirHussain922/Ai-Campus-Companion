"""
Standardized error response utilities.

Provides consistent error response format across all API endpoints.
"""

from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """
    Base exception for application errors.

    All custom exceptions should inherit from this class
    to ensure consistent error handling.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AppException.

        Args:
            message: Human-readable error message
            error_code: Application-specific error code (e.g., "AUTH_001")
            status_code: HTTP status code
            details: Additional error details
            data: Response data (success case with error info)
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.data = data or {}
        super().__init__(self.message)


def create_error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = False
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Application error code
        details: Additional error details
        success: Whether this is a success response (contains error info)

    Returns:
        Standardized error response dict
    """
    response = {
        "success": success,
        "message": message,
    }

    if error_code:
        response["error_code"] = error_code

    if details:
        response["details"] = details

    return response


def create_success_response(
    message: str = "Success",
    data: Optional[Dict[str, Any]] = None,
    success: bool = True
) -> Dict[str, Any]:
    """
    Create a standardized success response.

    Args:
        message: Success message
        data: Response data
        success: Whether this is a success response

    Returns:
        Standardized success response dict
    """
    response = {
        "success": success,
        "message": message,
    }

    if data is not None:
        response["data"] = data

    return response


def create_auth_response(
    success: bool = True,
    message: str = "Success",
    user: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    token_type: str = "bearer"
) -> Dict[str, Any]:
    """
    Create a standardized authentication response.

    Args:
        success: Whether the operation was successful
        message: Response message
        user: User data
        access_token: JWT access token
        refresh_token: JWT refresh token
        token_type: Token type

    Returns:
        Standardized auth response dict
    """
    response = create_success_response(message, success=success)

    if user:
        response["user"] = user

    if access_token:
        response["access_token"] = access_token
        response["refresh_token"] = refresh_token
        response["token_type"] = token_type

    return response


def format_exception(exc: Exception) -> Dict[str, Any]:
    """
    Format an exception into a standardized error response.

    Args:
        exc: Exception to format

    Returns:
        Standardized error response
    """
    if isinstance(exc, AppException):
        return create_error_response(
            message=exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code,
            details=exc.details
        )

    # Handle FastAPI HTTPException
    if isinstance(exc, HTTPException):
        # Extract message string from detail dict if needed
        detail = exc.detail
        if isinstance(detail, dict) and 'message' in detail:
            message = detail['message']
        elif isinstance(detail, dict):
            # Try to get message from detail dict
            message = str(detail.get('message', ''))
        elif isinstance(detail, list) and len(detail) > 0:
            # FastAPI often returns detail as array of error objects
            first_error = detail[0]
            if isinstance(first_error, dict) and 'msg' in first_error:
                message = first_error['msg']
            else:
                message = str(first_error)
        else:
            message = str(detail) if detail else 'HTTP error occurred'
        return create_error_response(
            message=message,
            status_code=exc.status_code,
            error_code=f"HTTP_{exc.status_code}",
            details={"type": exc.__class__.__name__}
        )

    # Handle general exceptions
    return create_error_response(
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="GENERIC_ERROR",
        details={
            "type": exc.__class__.__name__,
            "message": str(exc)
        }
    )


async def app_exception_handler(request, exc: AppException) -> JSONResponse:
    """
    FastAPI exception handler for AppException.

    Args:
        request: FastAPI request
        exc: AppException to handle

    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=format_exception(exc)
    )


async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    """
    FastAPI exception handler for HTTPException.

    Args:
        request: FastAPI request
        exc: HTTPException to handle

    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=format_exception(exc)
    )


async def general_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    FastAPI exception handler for general exceptions.

    Args:
        request: FastAPI request
        exc: Exception to handle

    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_exception(exc)
    )
