"""
Authentication and authorization module for AI Campus Companion.

Provides secure JWT-based authentication with bcrypt password hashing,
token refresh mechanism, and role-based access control.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from app.config import get_settings
from app.core.database import get_database
from app.models import TokenData, TokenType, UserInDB, UserRole

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


# ============================================================================
# Password Utilities
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Utilities
# ============================================================================

def create_token(
    user_id: str,
    email: str,
    role: UserRole = UserRole.USER,
    token_type: TokenType = TokenType.ACCESS,
    jti: Optional[str] = None,
    family: Optional[str] = None
) -> str:
    """
    Create a JWT token.

    Args:
        user_id: User ID
        email: User email
        role: User role
        token_type: Token type (access or refresh)
        jti: JWT ID (generated if not provided)
        family: Token family identifier for rotation/revocation

    Returns:
        Encoded JWT token string.
    """
    settings = get_settings()
    now = datetime.utcnow()

    # Set expiration based on token type
    if token_type == TokenType.ACCESS:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    else:  # refresh token
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    exp = now + expires_delta

    # Generate JWT ID if not provided
    if jti is None:
        jti = secrets.token_urlsafe(32)

    # Generate token family if not provided (for refresh tokens)
    # Access tokens use a separate family for security isolation
    if family is None:
        if token_type == TokenType.ACCESS:
            family = f"access:{user_id}:{now.timestamp()}"
        else:
            family = f"family:{user_id}:{now.timestamp()}"

    # Create payload
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role.value,
        "jti": jti,
        "family": family,
        "exp": exp,
        "iat": now,
        "type": token_type.value
    }

    # Encode token
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return token


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode.

    Returns:
        TokenData if token is valid, None otherwise.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        return TokenData(
            user_id=payload["user_id"],
            email=payload["email"],
            role=UserRole(payload.get("role", "user")),
            jti=payload["jti"],
            family=payload.get("family", ""),
            exp=datetime.fromtimestamp(payload["exp"]),
            iat=datetime.fromtimestamp(payload["iat"]),
            type=TokenType(payload.get("type", "access"))
        )

    except jwt.ExpiredSignatureError:
        logger.debug("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid token: {e}")
        return None


# ============================================================================
# Token Blacklist
# ============================================================================

async def is_token_blacklisted(jti: str) -> bool:
    """
    Check if a token is in the blacklist.

    Args:
        jti: JWT ID to check.

    Returns:
        True if token is blacklisted, False otherwise.
    """
    try:
        db = await get_database()
        result = await db.token_blacklist.find_one({"token_jti": jti})
        return result is not None
    except Exception as e:
        logger.error(f"Error checking token blacklist: {e}")
        return False


async def blacklist_token(jti: str, expires_at: datetime) -> None:
    """
    Add a token to the blacklist.

    Args:
        jti: JWT ID to blacklist.
        expires_at: Token expiration time (for TTL).
    """
    try:
        db = await get_database()
        await db.token_blacklist.update_one(
            {"token_jti": jti},
            {
                "$set": {
                    "token_jti": jti,
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        logger.debug(f"Token {jti[:8]}... added to blacklist")
    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")
        raise


async def blacklist_token_family(family: str, expires_at: datetime, user_id: str) -> None:
    """
    Add all tokens in a family to the blacklist.

    Args:
        family: Token family identifier.
        expires_at: Token expiration time.
        user_id: User ID for lookup.
    """
    try:
        db = await get_database()
        now = datetime.utcnow()

        # Mark all tokens with this family as revoked
        result = await db.revoked_tokens.update_many(
            {"family": family, "expires_at": {"$gt": now}},
            {
                "$set": {
                    "expires_at": expires_at,
                    "revoked_at": now
                }
            }
        )
        logger.info(f"Revoked {result.modified_count} tokens in family: {family[:16]}...")
    except Exception as e:
        logger.error(f"Error blacklisting token family: {e}")
        raise


# ============================================================================
# User Authentication
# ============================================================================

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """
    Get user by email address.

    Args:
        email: User email address.

    Returns:
        UserInDB if found, None otherwise.
    """
    try:
        db = await get_database()
        user_data = await db.users.find_one({"email": email.lower()})
        if user_data:
            return UserInDB(**user_data)
        return None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None


async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """
    Get user by ID.

    Args:
        user_id: User ID.

    Returns:
        UserInDB if found, None otherwise.
    """
    try:
        from bson import ObjectId
        db = await get_database()
        user_data = await db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return UserInDB(**user_data)
        return None
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate user with email and password.

    Args:
        email: User email address.
        password: User password.

    Returns:
        UserInDB if authentication successful, None otherwise.
    """
    user = await get_user_by_email(email)
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


async def update_last_login(user_id: str) -> None:
    """
    Update user's last login timestamp.

    Args:
        user_id: User ID.
    """
    try:
        from bson import ObjectId
        db = await get_database()
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "failed_login_attempts": 0,
                    "locked_until": None
                }
            }
        )
    except Exception as e:
        logger.error(f"Error updating last login: {e}")


async def increment_failed_login(email: str) -> Optional[datetime]:
    """
    Increment failed login attempts and possibly lock account.

    Args:
        email: User email address.

    Returns:
        Lock until datetime if account was locked, None otherwise.
    """
    try:
        from bson import ObjectId
        db = await get_database()
        user = await get_user_by_email(email)

        if not user:
            return None

        settings = get_settings()
        max_attempts = settings.max_failed_logins or 5
        lockout_minutes = settings.account_lockout_minutes or 30

        new_attempts = user.failed_login_attempts + 1

        if new_attempts >= max_attempts:
            # Lock account
            locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            await db.users.update_one(
                {"_id": ObjectId(user.id)},
                {
                    "$set": {
                        "failed_login_attempts": new_attempts,
                        "locked_until": locked_until
                    }
                }
            )
            return locked_until
        else:
            await db.users.update_one(
                {"_id": ObjectId(user.id)},
                {"$set": {"failed_login_attempts": new_attempts}}
            )
            return None

    except Exception as e:
        logger.error(f"Error incrementing failed login: {e}")
        return None


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInDB:
    """
    FastAPI dependency to get the current authenticated user.

    Args:
        credentials: HTTP Authorization credentials.

    Returns:
        UserInDB for the authenticated user.

    Raises:
        HTTPException: If authentication fails.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_token(credentials.credentials)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is blacklisted
    is_blacklisted = await is_token_blacklisted(token_data.jti)
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = await get_user_by_id(token_data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Check if account is locked
    if user.locked_until and datetime.utcnow() < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until.isoformat()}"
        )

    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    FastAPI dependency to get current active user (must be verified).

    Args:
        current_user: Current authenticated user.

    Returns:
        UserInDB for the verified user.

    Raises:
        HTTPException: If user is not verified.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email to continue.",
            headers={"X-Error-Code": "AUTH_002"}
        )
    return current_user


def get_current_user_id(token: str) -> str:
    """
    Extract user ID from JWT token.

    Args:
        token: JWT access token.

    Returns:
        User ID extracted from token payload.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data.user_id


class RequireRole:
    """Dependency class to require specific role(s)."""

    def __init__(self, *roles: UserRole):
        """
        Initialize with required role(s).

        Args:
            *roles: Required roles (at least one must match).
        """
        self.roles = roles

    async def __call__(self, user: UserInDB = Depends(get_current_user)) -> UserInDB:
        """
        Check if user has required role.

        Args:
            user: Current authenticated user.

        Returns:
            User if role matches.

        Raises:
            HTTPException: If user doesn't have required role.
        """
        if user.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(r.value for r in self.roles)}"
            )
        return user


# Convenience role dependencies
RequireAdmin = RequireRole(UserRole.ADMIN)
RequireModerator = RequireRole(UserRole.ADMIN, UserRole.MODERATOR)
