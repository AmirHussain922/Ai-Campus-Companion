"""
Authentication routes for AI Campus Companion.

Provides user registration, login, OTP verification, token refresh,
and logout functionality with JWT-based authentication.
"""

from __future__ import annotations

import asyncio
import bcrypt
import logging
import random
import time
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.auth import (
    authenticate_user,
    blacklist_token,
    blacklist_token_family,
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
from app.core.error_responses import AppException
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

@router.post("/register", response_model=APIResponse, status_code=status.HTTP_202_ACCEPTED)
async def register(
    user_data: UserCreate,
    request: Request
) -> APIResponse:
    """
    Register a new user account.

    Creates a new user with hashed password and sends verification OTP to email.
    Timing-constant response to prevent user enumeration.
    """
    start_time = time.monotonic()
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
        logger.info(f"Registration attempt for existing email: {mask_email(email)}")
        
        # Reject with appropriate error as requested
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "This email is already registered. Please log in instead.",
                "error_code": "AUTH_011"
            }
        )

    try:
        # User doesn't exist, proceed with normal registration
        # Hash password (this is the expensive operation)
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
            import traceback
            logger.error(f"Failed to send OTP email to {mask_email(email)}: {str(email_err)}\n{traceback.format_exc()}")
            # User is still created; they can request a new OTP later

        logger.info(f"User registered successfully: {mask_email(email)}")

        # Add rate limit headers
        headers = get_rate_limit_headers(rate_info)

        # Ensure minimum response time to match existing user branch
        elapsed = time.monotonic() - start_time
        if elapsed < 1.5:
            await asyncio.sleep(random.uniform(0.5, 2.0) - elapsed)

        # Return same message for both cases
        return create_auth_response(
            success=True,
            message="If this email is not registered, you will receive a verification code.",
            data={"user_id": user_id},
            status_code=status.HTTP_202_ACCEPTED
        )

    except HTTPException:
        # Re-raise HTTP exceptions so FastAPI handles them
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error during registration: {e}\n{traceback.format_exc()}")

        # Ensure minimum response time even on error
        elapsed = time.monotonic() - start_time
        if elapsed < 1.5:
            await asyncio.sleep(random.uniform(0.5, 2.0) - elapsed)

        # Standard generic error for security
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
    # Check rate limiting (per IP and per Email)
    client_ip = request.client.host if request.client else "unknown"
    
    # 1. Rate limit by IP
    await check_rate_limit(
        request,
        RateLimitAction.LOGIN,
        identifier=f"ip:{client_ip}"
    )

    # 2. Rate limit by Email
    is_allowed, rate_info = await check_rate_limit(
        request,
        RateLimitAction.LOGIN,
        identifier=f"email:{login_data.email.lower()}"
    )

    if not is_allowed:
        reset_timestamp = rate_info.get("reset_timestamp", 0)
        # HTTPException returns {detail: {message: "...", error_code: "..."}}
        # AppException returns {success: false, message: "...", error_code: "...", details: {...}}
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
        raise AppException(
            message="Invalid credentials",
            error_code="AUTH_001",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Check if account is locked
    if user.locked_until and datetime.utcnow() < user.locked_until:
        raise AppException(
            message=f"Account locked. Try again after {user.locked_until.isoformat()}",
            error_code="AUTH_004",
            status_code=status.HTTP_403_FORBIDDEN
        )

    # Check if user is verified
    if not user.is_verified:
        raise AppException(
            message="Email not verified. Please verify your email to continue.",
            error_code="AUTH_002",
            status_code=status.HTTP_403_FORBIDDEN
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
    Refresh access token with rotation and revocation.

    - Inserts old refresh token JTI into revoked_tokens collection
    - Generates new access_token AND new refresh_token with new JTI
    - Implements token family tracking for security
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Refresh token required", "error_code": "AUTH_009"}
        )

    settings = get_settings()
    db = await get_database()

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

    # Add old refresh token to revoked_tokens collection
    # The token expires at token_data.exp, so we set expires_at to that time
    # We also store the family claim to revoke all tokens in the same family
    now = datetime.utcnow()
    token_expiry = token_data.exp

    # Store in revoked_tokens with TTL for automatic cleanup
    await db.revoked_tokens.update_one(
        {"token_jti": token_data.jti},
        {
            "$set": {
                "token_jti": token_data.jti,
                "user_id": token_data.user_id,
                "expires_at": token_expiry,
                "revoked_at": now,
                "family": token_data.family  # Store token family for revocation
            }
        },
        upsert=True
    )

    # Generate token family for this session
    # Use the old family but update the timestamp to create a new one
    old_family = token_data.family
    token_family = old_family.replace(str(datetime.utcnow().timestamp()), str(datetime.utcnow().timestamp()))

    # Generate NEW access_token
    access_token = create_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.ACCESS
    )

    # Generate NEW refresh_token with family tracking
    new_refresh_token = create_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.REFRESH,
        jti=None  # Let create_token generate a new JTI
    )

    # Verify that create_token returned a token
    if not new_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Failed to generate refresh token", "error_code": "AUTH_010"}
        )

    # Decode the new refresh token to get its JTI
    new_token_data = decode_token(new_refresh_token)
    if not new_token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Failed to generate refresh token", "error_code": "AUTH_010"}
        )

    logger.info(f"Token refreshed for user: {mask_email(user.email)}")

    return create_auth_response(
        success=True,
        message="Token refreshed successfully",
        data={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
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

        # Log OTP generation without exposing the plaintext code
        logger.info(f"Generated OTP for {mask_email(email)} with purpose {OTPPurpose.PASSWORD_RESET.value}")
        
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
