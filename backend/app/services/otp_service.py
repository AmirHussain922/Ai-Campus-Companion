"""
OTP (One-Time Password) service for email verification.

Provides secure OTP generation, storage, and validation with MongoDB TTL indexes
for automatic expiration.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database

logger = logging.getLogger(__name__)


class OTPPurpose(str, Enum):
    """OTP purpose enumeration."""
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"
    EMAIL_CHANGE = "email_change"


class OTPError(Exception):
    """OTP-related error."""
    pass


class OTPNotFoundError(OTPError):
    """OTP not found or expired."""
    pass


class OTPInvalidError(OTPError):
    """Invalid OTP code."""
    pass


class OTPExpiredError(OTPError):
    """OTP has expired."""
    pass


class OTPRateLimitError(OTPError):
    """OTP rate limit exceeded."""
    pass


class OTPService:
    """
    Service for managing One-Time Passwords (OTPs).

    Features:
    - Cryptographically secure random OTP generation
    - MongoDB storage with TTL for automatic expiration
    - Rate limiting for OTP requests
    - Multiple OTP purposes (registration, password reset, etc.)
    """

    def __init__(
        self,
        db: Optional[AsyncIOMotorDatabase] = None,
        otp_length: int = 6,
        otp_ttl_minutes: int = 10,
        max_resend_attempts: int = 3,
        resend_window_minutes: int = 60
    ):
        """
        Initialize OTP service.

        Args:
            db: MongoDB database instance (optional, will use get_database() if not provided)
            otp_length: Length of OTP code (default: 6)
            otp_ttl_minutes: OTP expiration time in minutes (default: 10)
            max_resend_attempts: Maximum OTP resend attempts per window (default: 3)
            resend_window_minutes: Time window for rate limiting in minutes (default: 60)
        """
        self._db = db
        self._otp_length = otp_length
        self._otp_ttl_minutes = otp_ttl_minutes
        self._max_resend_attempts = max_resend_attempts
        self._resend_window_minutes = resend_window_minutes

    async def _get_db(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self._db is None:
            self._db = await get_database()
        return self._db

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """
        Generate a cryptographically secure random OTP.

        Uses secrets module for cryptographically strong random number generation.
        Returns a numeric OTP of specified length.

        Args:
            length: Length of OTP (default: 6)

        Returns:
            Random numeric OTP as string.
        """
        # Generate random number with specified number of digits
        min_val = 10 ** (length - 1)
        max_val = (10 ** length) - 1
        otp = secrets.randbelow(max_val - min_val + 1) + min_val
        return str(otp)

    async def create_otp(
        self,
        email: str,
        purpose: OTPPurpose = OTPPurpose.REGISTRATION
    ) -> str:
        """
        Create and store a new OTP for the given email.

        Args:
            email: User email address
            purpose: OTP purpose (registration, password_reset, etc.)

        Returns:
            Generated OTP code

        Raises:
            OTPRateLimitError: If too many OTP requests
        """
        db = await self._get_db()

        # Check rate limiting
        rate_key = f"otp_resend:{email.lower()}"
        rate_limit = await db.rate_limits.find_one({"key": rate_key})

        if rate_limit:
            attempts = rate_limit.get("count", 0)
            window_start = rate_limit.get("window_start")

            if attempts >= self._max_resend_attempts:
                raise OTPRateLimitError(
                    f"Maximum resend attempts exceeded. Try again in {self._resend_window_minutes} minutes."
                )

        # Delete any existing OTP for this email and purpose
        await db.otps.delete_many({
            "email": email.lower(),
            "purpose": purpose.value
        })

        # Generate new OTP
        otp = self.generate_otp(self._otp_length)
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self._otp_ttl_minutes)

        # Store OTP in database
        await db.otps.insert_one({
            "email": email.lower(),
            "otp": otp,
            "purpose": purpose.value,
            "expires_at": expires_at,
            "created_at": now,
            "attempts": 0
        })

        # Update rate limit
        if rate_limit:
            await db.rate_limits.update_one(
                {"key": rate_key},
                {
                    "$inc": {"count": 1},
                    "$set": {"updated_at": now}
                }
            )
        else:
            await db.rate_limits.insert_one({
                "key": rate_key,
                "count": 1,
                "window_start": now,
                "expires_at": now + timedelta(minutes=self._resend_window_minutes)
            })

        logger.info(f"OTP created for {email} with purpose {purpose.value}")
        return otp

    async def verify_otp(
        self,
        email: str,
        otp: str,
        purpose: OTPPurpose = OTPPurpose.REGISTRATION,
        max_attempts: int = 3
    ) -> bool:
        """
        Verify an OTP for the given email.

        Args:
            email: User email address
            otp: OTP code to verify
            purpose: OTP purpose
            max_attempts: Maximum verification attempts before OTP is invalidated

        Returns:
            True if OTP is valid, False otherwise

        Raises:
            OTPNotFoundError: If OTP not found or expired
            OTPInvalidError: If OTP is invalid
            OTPExpiredError: If OTP has expired
        """
        db = await self._get_db()
        now = datetime.utcnow()

        # Find OTP record
        otp_record = await db.otps.find_one({
            "email": email.lower(),
            "purpose": purpose.value
        })

        if not otp_record:
            raise OTPNotFoundError("OTP not found or has expired")

        # Check if OTP has expired
        expires_at = otp_record.get("expires_at")
        if expires_at and now > expires_at:
            # Delete expired OTP
            await db.otps.delete_one({"_id": otp_record["_id"]})
            raise OTPExpiredError("OTP has expired. Please request a new one.")

        # Check attempts
        attempts = otp_record.get("attempts", 0)
        if attempts >= max_attempts:
            # Delete OTP after max attempts
            await db.otps.delete_one({"_id": otp_record["_id"]})
            raise OTPInvalidError("Too many failed attempts. Please request a new OTP.")

        # Verify OTP
        stored_otp = otp_record.get("otp")
        if not stored_otp or stored_otp != otp:
            # Increment attempts
            await db.otps.update_one(
                {"_id": otp_record["_id"]},
                {"$inc": {"attempts": 1}}
            )
            raise OTPInvalidError("Invalid OTP. Please try again.")

        # OTP is valid - delete it
        await db.otps.delete_one({"_id": otp_record["_id"]})

        logger.info(f"OTP verified successfully for {email}")
        return True

    async def delete_otp(self, email: str, purpose: OTPPurpose = OTPPurpose.REGISTRATION) -> None:
        """
        Delete an OTP for the given email.

        Args:
            email: User email address
            purpose: OTP purpose
        """
        db = await self._get_db()
        result = await db.otps.delete_many({
            "email": email.lower(),
            "purpose": purpose.value
        })

        if result.deleted_count > 0:
            logger.info(f"Deleted {result.deleted_count} OTP(s) for {email}")


# Global OTP service instance
_otp_service: OTPService | None = None


async def get_otp_service() -> OTPService:
    """Get or create the global OTP service instance."""
    global _otp_service
    if _otp_service is None:
        _otp_service = OTPService()
    return _otp_service
