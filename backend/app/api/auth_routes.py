"""
Authentication routes for AI Campus Companion.

Provides user registration, login, OTP verification, token refresh,
and logout functionality with JWT-based authentication.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.auth import (
    authenticate_user,
    blacklist_token,
    create_token,
    decode_token,
    get_current_user,
    get_user_by_email,
    hash_password,
    increment_failed_login,
    is_token_blacklisted,
    update_last_login,
    verify_password,
)
from app.config import get_settings
from app.core.database import get_database
from app.models import (
    APIResponse,
    OTPResend,
    OTPVerify,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    TokenType,
    UserCreate,
    UserInDB,
    UserLogin,
    UserResponse,
    UserRole,
)
from app.services.otp_service import OTPPurpose, get_otp_service
from app.utils.rate_limiter import RateLimitAction, check_rate_limit, get_rate_limit_headers
from app.core.security import mask_email, sanitize_input
from app.services import get_email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)


# ============================================================================
# Helper Functions
# ============================================================================

def create_auth_response(
    success: bool,
    message: str,
    data: Optional[dict] = None,
    error_code: Optional[str] = None,
    status_code: int = status.HTTP_200_OK
) -> APIResponse:
    """Create standardized API response."""
    return APIResponse(
        success=success,
        message=message,
        data=data,
        error_code=error_code
    )


def user_to_response(user: UserInDB) -> dict:
    """Convert UserInDB to response dict."""
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None
    }


# ============================================================================
# Authentication Routes
# ============================================================================

@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request
) -> APIResponse:
    """
    Register a new user account.

    Creates a new user with hashed password and sends verification OTP to email.
    """
    settings = get_settings()
    db = await get_database()

    # Check rate limiting for registration
    client_ip = request.client.host if request.client else "unknown"
    is_allowed, rate_info = await check_rate_limit(
        request,
        RateLimitAction.REGISTER,
        identifier=f"ip:{client_ip}"
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Rate limit exceeded. Please try again later.",
                "error_code": "AUTH_008"
            }
        )

    # Sanitize inputs
    email = sanitize_input(user_data.email.lower().strip())
    full_name = sanitize_input(user_data.full_name.strip())

    # Check if email already exists
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        # Return generic message to prevent user enumeration
        return create_auth_response(
            success=True,
            message="If this email is not registered, you will receive a verification code.",
            status_code=status.HTTP_201_CREATED
        )

    try:
        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user document
        now = datetime.utcnow()
        user_doc = {
            "email": email,
            "full_name": full_name,
            "password_hash": password_hash,
            "role": UserRole.USER.value,
            "is_verified": False,
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login": None,
            "email_verified_at": None,
            "created_at": now,
            "updated_at": now
        }

        # Insert user
        result = await db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)

        # Generate and send OTP
        otp_service = await get_otp_service()
        otp_code = await otp_service.create_otp(email, OTPPurpose.REGISTRATION)

        # Send OTP email (non-fatal: user is created even if email fails)
        try:
            email_service = await get_email_service()
            await email_service.send_otp_email(
                to_email=email,
                full_name=full_name,
                otp_code=otp_code,
                expiry_minutes=10
            )
        except Exception as email_err:
            logger.warning(f"Failed to send OTP email to {mask_email(email)}: {email_err}")
            # User is still created; they can request a new OTP later

        logger.info(f"User registered successfully: {mask_email(email)}")

        # Add rate limit headers
        headers = get_rate_limit_headers(rate_info)

        return create_auth_response(
            success=True,
            message="Registration successful. Please check your email for the verification code.",
            data={"user_id": user_id},
            status_code=status.HTTP_201_CREATED
        )

    except Exception as e:
        import traceback
        logger.error(f"Error during registration: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration. Please try again."
        )


@router.post("/verify-otp", response_model=APIResponse)
async def verify_otp(
    verify_data: OTPVerify,
    request: Request
) -> APIResponse:
    """
    Verify email with OTP code.

    Verifies the OTP code sent to the user's email and activates the account.
    """
    # Check rate limiting
    is_allowed, rate_info = await check_rate_limit(
        request,
        RateLimitAction.OTP_VERIFY,
        identifier=f"email:{verify_data.email.lower()}"
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Rate limit exceeded. Please try again later.",
                "error_code": "AUTH_008"
            }
        )

    email = verify_data.email.lower().strip()

    # Get user
    db = await get_database()
    user = await db.users.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "error_code": "AUTH_001"}
        )

    if user.get("is_verified"):
        return create_auth_response(
            success=True,
            message="Email is already verified"
        )

    # Verify OTP
    try:
        otp_service = await get_otp_service()
        await otp_service.verify_otp(
            email=email,
            otp=verify_data.otp,
            purpose=OTPPurpose(verify_data.purpose)
        )

        # Update user as verified
        now = datetime.utcnow()
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "is_verified": True,
                    "email_verified_at": now,
                    "updated_at": now
                }
            }
        )

        logger.info(f"Email verified successfully: {mask_email(email)}")

        return create_auth_response(
            success=True,
            message="Email verified successfully. You can now log in."
        )

    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "error_code": "AUTH_003"}
        )


@router.post("/resend-otp", response_model=APIResponse)
async def resend_otp(
    resend_data: OTPResend,
    request: Request
) -> APIResponse:
    """
    Resend OTP code.

    Resends the OTP code to the user's email for verification.
    Rate limited to prevent abuse.
    """
    # Check rate limiting (stricter for resend)
    is_allowed, rate_info = await check_rate_limit(
        request,
        RateLimitAction.OTP_RESEND,
        identifier=f"email:{resend_data.email.lower()}"
    )

    if not is_allowed:
        reset_timestamp = rate_info.get("reset_timestamp", 0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Too many OTP requests. Please try again later.",
                "reset_at": reset_timestamp,
                "error_code": "AUTH_008"
            }
        )

    email = resend_data.email.lower().strip()

    # Get user
    db = await get_database()
    user = await db.users.find_one({"email": email})

    if not user:
        # Return generic message to prevent user enumeration
        return create_auth_response(
            success=True,
            message="If this email is registered and not verified, you will receive a verification code."
        )

    if user.get("is_verified"):
        return create_auth_response(
            success=True,
            message="Email is already verified"
        )

    # Generate and send new OTP
    try:
        otp_service = await get_otp_service()
        otp_code = await otp_service.create_otp(email, OTPPurpose(resend_data.purpose))

        # Send OTP email
        email_service = await get_email_service()
        await email_service.send_otp_email(
            to_email=email,
            full_name=user.get("full_name", "User"),
            otp_code=otp_code,
            expiry_minutes=10
        )

        logger.info(f"OTP resent successfully: {mask_email(email)}")

        return create_auth_response(
            success=True,
            message="Verification code sent successfully. Please check your email."
        )

    except Exception as e:
        logger.error(f"Failed to resend OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code. Please try again later."
        )


@router.post("/login", response_model=APIResponse)
async def login(
    login_data: UserLogin,
    request: Request
) -> APIResponse:
    """
    User login.

    Authenticates user with email and password, returns JWT tokens.
    """
    # Check rate limiting
    is_allowed, rate_info = await check_rate_limit(
        request,
        RateLimitAction.LOGIN,
        identifier=f"email:{login_data.email.lower()}"
    )

    if not is_allowed:
        reset_timestamp = rate_info.get("reset_timestamp", 0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Too many login attempts. Please try again later.",
                "reset_at": reset_timestamp,
                "error_code": "AUTH_008"
            }
        )

    email = login_data.email.lower().strip()

    # Get user
    user = await get_user_by_email(email)

    if not user:
        # Increment failed login (using a placeholder IP)
        await increment_failed_login(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid credentials", "error_code": "AUTH_001"}
        )

    # Check if account is locked
    if user.locked_until and datetime.utcnow() < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": f"Account locked. Try again after {user.locked_until.isoformat()}",
                "error_code": "AUTH_004"
            }
        )

    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Email not verified. Please verify your email to continue.",
                "error_code": "AUTH_002"
            }
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        # Increment failed login
        locked_until = await increment_failed_login(email)
        
        if locked_until:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"Too many failed attempts. Account locked until {locked_until.isoformat()}",
                    "error_code": "AUTH_004"
                }
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid credentials", "error_code": "AUTH_001"}
        )

    # Update last login
    await update_last_login(str(user.id))

    settings = get_settings()

    # Generate tokens
    access_token = create_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.ACCESS
    )
    
    refresh_token = create_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.REFRESH
    )

    logger.info(f"User logged in successfully: {mask_email(user.email)}")

    return create_auth_response(
        success=True,
        message="Login successful",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": user_to_response(user)
        }
    )


@router.post("/refresh", response_model=APIResponse)
async def refresh_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> APIResponse:
    """
    Refresh access token.

    Generates a new access token using a valid refresh token.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Refresh token required", "error_code": "AUTH_009"}
        )

    # Decode and validate refresh token
    token_data = decode_token(credentials.credentials)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or expired refresh token", "error_code": "AUTH_005"}
        )

    # Check if token type is refresh
    if token_data.type != TokenType.REFRESH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid token type", "error_code": "AUTH_009"}
        )

    # Check if token is blacklisted
    is_blacklisted = await is_token_blacklisted(token_data.jti)
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token has been revoked", "error_code": "AUTH_006"}
        )

    # Get user
    user = await get_user_by_id(token_data.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "User not found or inactive", "error_code": "AUTH_001"}
        )

    # Generate new access token
    access_token = create_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.ACCESS
    )

    logger.info(f"Token refreshed for user: {mask_email(user.email)}")

    return create_auth_response(
        success=True,
        message="Token refreshed successfully",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": get_settings().access_token_expire_minutes * 60
        }
    )


@router.post("/logout", response_model=APIResponse)
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> APIResponse:
    """
    Logout user.

    Blacklists the current access token and refresh token.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token required", "error_code": "AUTH_009"}
        )

    # Decode token to get expiration
    token_data = decode_token(credentials.credentials)

    if token_data:
        # Add token to blacklist
        await blacklist_token(token_data.jti, token_data.exp)
        logger.info(f"User logged out: {mask_email(token_data.email)}")
    else:
        # Token is invalid or expired, but we'll still return success
        # as the user wanted to logout anyway
        logger.debug("Logout attempted with invalid/expired token")

    return create_auth_response(
        success=True,
        message="Logged out successfully"
    )


@router.get("/me", response_model=APIResponse)
async def get_me(
    current_user: UserInDB = Depends(get_current_user)
) -> APIResponse:
    """
    Get current user profile.

    Returns the profile information of the currently authenticated user.
    """
    return create_auth_response(
        success=True,
        message="User profile retrieved successfully",
        data={"user": user_to_response(current_user)}
    )


# ============================================================================
# Password Reset Routes
# ============================================================================

@router.post("/forgot-password", response_model=APIResponse)
async def forgot_password(
    request_data: PasswordResetRequest,
    request: Request
) -> APIResponse:
    """
    Request password reset.

    Sends a password reset OTP to the user's email.
    """
    # Check rate limiting
    is_allowed, rate_info = await check_rate_limit(
        request,
        RateLimitAction.PASSWORD_RESET,
        identifier=f"email:{request_data.email.lower()}"
    )

    if not is_allowed:
        reset_timestamp = rate_info.get("reset_timestamp", 0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Too many password reset requests. Please try again later.",
                "reset_at": reset_timestamp,
                "error_code": "AUTH_008"
            }
        )

    email = request_data.email.lower().strip()

    # Get user
    db = await get_database()
    user = await db.users.find_one({"email": email})

    if not user:
        # Return generic message to prevent user enumeration
        return create_auth_response(
            success=True,
            message="If this email is registered, you will receive a password reset code."
        )

    # Generate and send OTP
    try:
        otp_service = await get_otp_service()
        otp_code = await otp_service.create_otp(email, OTPPurpose.PASSWORD_RESET)

        logger.info(f"Generated OTP for {email}: {otp_code}")
        
        # Send password reset OTP email
        email_service = await get_email_service()
        logger.info(f"Calling send_password_reset_otp_email to {email}")
        await email_service.send_password_reset_otp_email(
            to_email=email,
            full_name=user.get("full_name", "User"),
            otp_code=otp_code,
            expiry_minutes=10
        )
        logger.info(f"Password reset OTP sent successfully to: {mask_email(email)}")

        return create_auth_response(
            success=True,
            message="Password reset code sent successfully. Please check your email."
        )

    except Exception as e:
        logger.error(f"Failed to send password reset OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to send password reset code. Please try again later.",
                "error_code": "AUTH_009"
            }
        )


@router.post("/reset-password", response_model=APIResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request
) -> APIResponse:
    """
    Reset password with OTP.

    Resets the user's password using the OTP code sent to their email.
    """
    email = reset_data.email.lower().strip()

    # Get user
    db = await get_database()
    user = await db.users.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "error_code": "AUTH_001"}
        )

    # Verify OTP
    try:
        otp_service = await get_otp_service()
        await otp_service.verify_otp(
            email=email,
            otp=reset_data.otp,
            purpose=OTPPurpose.PASSWORD_RESET
        )

        # Hash new password
        new_password_hash = hash_password(reset_data.new_password)

        # Update user password
        now = datetime.utcnow()
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password_hash": new_password_hash,
                    "updated_at": now,
                    # Reset failed login attempts since they successfully reset
                    "failed_login_attempts": 0,
                    "locked_until": None
                }
            }
        )

        logger.info(f"Password reset successfully for: {mask_email(email)}")

        return create_auth_response(
            success=True,
            message="Password has been reset successfully. You can now log in with your new password."
        )

    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        
        # Check if it's an OTP error
        error_msg = str(e)
        if "OTP" in error_msg or "otp" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": error_msg, "error_code": "AUTH_003"}
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again later."
        )
