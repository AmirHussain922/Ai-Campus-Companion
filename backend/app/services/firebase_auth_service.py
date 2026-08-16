"""
Firebase Authentication Service
Handles user registration and login using Firebase Auth
"""
import logging
from typing import Optional
from app.firebase_config import initialize_firebase
from firebase_admin import auth, credentials
from app.config import get_settings

logger = logging.getLogger(__name__)


async def register_user(email: str, password: str, full_name: str) -> dict:
    """
    Register a new user with Firebase Authentication

    Args:
        email: User email address
        password: User password
        full_name: User's full name

    Returns:
        dict with user creation status and user data
    """
    try:
        # Initialize Firebase
        app = initialize_firebase()
        if not app:
            logger.error("Failed to initialize Firebase")
            return {
                "success": False,
                "message": "Failed to initialize authentication service"
            }

        # Create user in Firebase
        user = auth.create_user(
            email=email,
            password=password,
            display_name=full_name,
            email_verified=False  # User will receive verification email
        )

        logger.info(f"User created in Firebase: {email}")

        return {
            "success": True,
            "message": "Registration successful! Please check your email for verification.",
            "user": {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "email_verified": user.email_verified
            }
        }

    except auth.EmailAlreadyExistsError:
        logger.error(f"Email already exists: {email}")
        return {
            "success": False,
            "message": "An account with this email already exists. Please login instead."
        }

    except auth.InvalidArgumentError as e:
        logger.error(f"Invalid argument for email/password: {e}")
        return {
            "success": False,
            "message": "Invalid email or password. Password should be at least 6 characters."
        }

    except auth.RevokedIdTokenError as e:
        logger.error(f"Revoked ID token error: {e}")
        return {
            "success": False,
            "message": "Authentication service temporarily unavailable."
        }

    except Exception as e:
        logger.error(f"Firebase registration error: {e}")
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }


async def login_user(email: str, password: str) -> dict:
    """
    Login a user with Firebase Authentication

    Args:
        email: User email address
        password: User password

    Returns:
        dict with login status and user data
    """
    try:
        # Initialize Firebase
        app = initialize_firebase()
        if not app:
            logger.error("Failed to initialize Firebase")
            return {
                "success": False,
                "message": "Failed to initialize authentication service"
            }

        # Sign in with email and password
        user = auth.sign_in_with_email_and_password(email, password)

        logger.info(f"User logged in: {email}")

        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "uid": user['localId'],
                "email": user['email'],
                "display_name": user.get('displayName'),
                "email_verified": user['emailVerified'],
                "id_token": user['idToken'],
                "refresh_token": user['refreshToken']
            }
        }

    except auth.InvalidCredentialError:
        logger.error(f"Invalid credentials for email: {email}")
        return {
            "success": False,
            "message": "Invalid email or password."
        }

    except auth.EmailNotFound:
        logger.error(f"Email not found: {email}")
        return {
            "success": False,
            "message": "No account found with this email. Please register first."
        }

    except Exception as e:
        logger.error(f"Firebase login error: {e}")
        return {
            "success": False,
            "message": f"Login failed: {str(e)}"
        }


async def reset_password(email: str) -> dict:
    """
    Send password reset email via Firebase

    Args:
        email: User email address

    Returns:
        dict with reset status
    """
    try:
        # Initialize Firebase
        app = initialize_firebase()
        if not app:
            logger.error("Failed to initialize Firebase")
            return {
                "success": False,
                "message": "Failed to initialize authentication service"
            }

        # Send password reset email
        auth.send_password_reset_email(email)

        logger.info(f"Password reset email sent to: {email}")

        return {
            "success": True,
            "message": "Password reset email sent! Please check your inbox."
        }

    except auth.EmailNotFound:
        logger.error(f"Email not found: {email}")
        return {
            "success": False,
            "message": "No account found with this email."
        }

    except Exception as e:
        logger.error(f"Firebase password reset error: {e}")
        return {
            "success": False,
            "message": f"Failed to send reset email: {str(e)}"
        }


async def verify_id_token(id_token: str) -> dict:
    """
    Verify Firebase ID token and get user info

    Args:
        id_token: Firebase ID token

    Returns:
        dict with verified user info or error
    """
    try:
        # Initialize Firebase
        app = initialize_firebase()
        if not app:
            logger.error("Failed to initialize Firebase")
            return {
                "success": False,
                "message": "Failed to initialize authentication service"
            }

        # Verify the token
        decoded_token = auth.verify_id_token(id_token)
        user = auth.get_user(decoded_token['uid'])

        logger.info(f"ID token verified for user: {user.email}")

        return {
            "success": True,
            "user": {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "email_verified": user.email_verified
            }
        }

    except auth.InvalidIdTokenError:
        logger.error("Invalid ID token")
        return {
            "success": False,
            "message": "Invalid authentication token."
        }

    except auth.ExpiredIdTokenError:
        logger.error("Expired ID token")
        return {
            "success": False,
            "message": "Authentication token expired. Please login again."
        }

    except Exception as e:
        logger.error(f"Firebase token verification error: {e}")
        return {
            "success": False,
            "message": f"Token verification failed: {str(e)}"
        }
