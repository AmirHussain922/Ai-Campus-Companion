"""
Firebase Authentication Routes for AI Campus Companion.

Uses Firebase Authentication for registration, login, password reset,
and token verification with automatic email verification.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from app.config import get_settings
from app.core.database import get_database
from app.core.security import mask_email, sanitize_input
from app.core.error_responses import AppException
from app.models import APIResponse
from app.services.firebase_auth_service import (
    login_user,
    register_user,
    reset_password,
    verify_id_token
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models for Firebase authentication
class UserCreateFirebase(BaseModel):
    """User registration request with Firebase"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")

class UserLoginFirebase(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="User email address")

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    email: EmailStr = Field(..., description="User email address")
    new_password: str = Field(..., min_length=6, description="New password (min 6 chars)")


@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreateFirebase,
    request: Request
) -> APIResponse:
    """
    Register a new user with Firebase Authentication.

    Creates user in Firebase (automatic email verification sent),
    then syncs user to MongoDB for additional features.
    """
    email = sanitize_input(user_data.email.lower().strip())
    full_name = sanitize_input(user_data.full_name.strip())
    settings = get_settings()

    # Check if Firebase is configured
    if not settings.firebase_project_id:
        raise AppException(
            message="Authentication service not configured. Please contact administrator.",
            error_code="AUTH_999",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        # Register user in Firebase (this sends verification email)
        firebase_result = await register_user(
            email=email,
            password=user_data.password,
            full_name=full_name
        )

        if not firebase_result.get("success"):
            # Firebase registration failed
            if firebase_result.get("message") == "An account with this email already exists.":
                raise AppException(
                    message="This email is already registered. Please log in instead.",
                    error_code="AUTH_011",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            raise AppException(
                message=firebase_result.get("message", "Registration failed"),
                error_code="AUTH_999",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # User created in Firebase successfully
        user_info = firebase_result.get("user", {})
        firebase_uid = user_info.get("uid")

        # Sync user to MongoDB for additional features
        db = await get_database()
        existing_user = await db.users.find_one({"email": email})

        if existing_user:
            # Update existing user with Firebase UID
            await db.users.update_one(
                {"email": email},
                {
                    "$set": {
                        "firebase_uid": firebase_uid,
                        "full_name": full_name,
                        "email_verified": user_info.get("email_verified", False),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"User synced to MongoDB: {mask_email(email)}")

        # Return success response
        return create_auth_response(
            success=True,
            message="Registration successful! Please check your email for verification.",
            user={
                "email": email,
                "full_name": full_name,
                "firebase_uid": firebase_uid,
                "email_verified": user_info.get("email_verified", False)
            }
        )

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise AppException(
            message=f"Registration failed: {str(e)}",
            error_code="AUTH_999",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/login", response_model=APIResponse)
async def login(
    login_data: UserLoginFirebase,
    request: Request
) -> APIResponse:
    """
    User login with Firebase Authentication.

    Authenticates with Firebase, returns Firebase ID token,
    then syncs with MongoDB for additional features.
    """
    email = sanitize_input(login_data.email.lower().strip())
    settings = get_settings()

    # Check if Firebase is configured
    if not settings.firebase_project_id:
        raise AppException(
            message="Authentication service not configured. Please contact administrator.",
            error_code="AUTH_999",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        # Login with Firebase
        firebase_result = await login_user(email, login_data.password)

        if not firebase_result.get("success"):
            raise AppException(
                message=firebase_result.get("message", "Login failed"),
                error_code="AUTH_001",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # User logged in successfully
        user_info = firebase_result.get("user", {})
        firebase_uid = user_info.get("uid")
        id_token = user_info.get("id_token")

        # Sync with MongoDB for additional features
        db = await get_database()
        existing_user = await db.users.find_one({"email": email})

        if existing_user:
            # Update last login
            await db.users.update_one(
                {"email": email},
                {
                    "$set": {
                        "last_login": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"User logged in and synced: {mask_email(email)}")

        # Return success response with Firebase token
        return create_auth_response(
            success=True,
            message="Login successful",
            user={
                "email": email,
                "full_name": user_info.get("display_name", ""),
                "firebase_uid": firebase_uid,
                "email_verified": user_info.get("email_verified", False),
                "id_token": id_token,
                "refresh_token": user_info.get("refresh_token", "")
            }
        )

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise AppException(
            message=f"Login failed: {str(e)}",
            error_code="AUTH_999",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/reset-password", response_model=APIResponse)
async def reset_password_request(
    data: PasswordResetRequest,
    request: Request
) -> APIResponse:
    """
    Request password reset via Firebase.

    Sends password reset email with Firebase.
    """
    email = sanitize_input(data.email.lower().strip())
    settings = get_settings()

    # Check if Firebase is configured
    if not settings.firebase_project_id:
        raise AppException(
            message="Authentication service not configured.",
            error_code="AUTH_999",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        result = await reset_password(email)

        if not result.get("success"):
            raise AppException(
                message=result.get("message", "Password reset failed"),
                error_code="AUTH_999",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return create_auth_response(
            success=True,
            message=result.get("message", "Password reset email sent successfully")
        )

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise AppException(
            message=f"Failed to send reset email: {str(e)}",
            error_code="AUTH_999",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/verify-token", response_model=APIResponse)
async def verify_token(
    request: Request,
    id_token: Optional[str] = None
) -> APIResponse:
    """
    Verify Firebase ID token and get user info.

    Required parameters:
    - id_token: Firebase ID token from frontend

    This is called automatically after login to verify the token.
    """
    # Get token from query parameter or Authorization header
    token = id_token or request.query_params.get("id_token")

    if not token:
        raise AppException(
            message="ID token is required",
            error_code="AUTH_003",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    settings = get_settings()

    # Check if Firebase is configured
    if not settings.firebase_project_id:
        raise AppException(
            message="Authentication service not configured.",
            error_code="AUTH_999",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        result = await verify_id_token(token)

        if not result.get("success"):
            raise AppException(
                message=result.get("message", "Invalid token"),
                error_code="AUTH_999",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        user_info = result.get("user", {})
        email = user_info.get("email", "")

        # Sync with MongoDB
        db = await get_database()
        existing_user = await db.users.find_one({"email": email})

        if existing_user:
            # Update last login
            await db.users.update_one(
                {"email": email},
                {"$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()}}
            )
            logger.info(f"User token verified and synced: {mask_email(email)}")

        return create_auth_response(
            success=True,
            user={
                "email": email,
                "full_name": user_info.get("display_name", ""),
                "firebase_uid": user_info.get("uid"),
                "email_verified": user_info.get("email_verified", False)
            }
        )

    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise AppException(
            message=f"Token verification failed: {str(e)}",
            error_code="AUTH_999",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/resend-verification", response_model=APIResponse)
async def resend_verification(
    email: str,
    request: Request
) -> APIResponse:
    """
    Resend verification email.

    Note: Firebase Authentication automatically sends verification email
    when a new user is registered. This endpoint can be used to resend
    if needed, though it requires Firebase Admin SDK.
    """
    raise AppException(
        message="Resending verification email requires Firebase Admin SDK integration. Please login again.",
        error_code="AUTH_005",
        status_code=status.HTTP_501_NOT_IMPLEMENTED
    )


def create_auth_response(success: bool, message: str, user: Optional[dict] = None) -> APIResponse:
    """Create a standardized authentication response"""
    return APIResponse(
        success=success,
        message=message,
        user=user,
        error_code=None,
        details=None
    )
