"""
Contact form submission endpoints.

Provides public API for collecting user feedback through the landing page
contact form. Submissions are stored in MongoDB and optionally sent via email.
"""

from __future__ import annotations

import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.database import get_database
from app.core.error_responses import AppException
from app.core.security import sanitize_input
from app.core.utils import is_database_available, set_database_available
from app.models import APIResponse
from app.utils.rate_limiter import check_rate_limit, RateLimitAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", response_model=APIResponse)
async def submit_contact_form(
    request: Request
) -> dict:
    """
    Submit a contact form feedback message.

    This is a public endpoint for collecting user feedback. No authentication
    is required.

    Args:
        request: FastAPI request object (for IP address and rate limiting)

    Returns:
        APIResponse with success message

    Raises:
        HTTPException: If validation fails or rate limit exceeded
    """
    # Parse request body
    try:
        body = await request.json()
    except Exception:
        raise AppException(
            message="Invalid request body",
            error_code="VALIDATION_001",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": "body", "constraint": "Request must be JSON"}
        )

    # Validate required fields
    name = body.get("name", "")
    email = body.get("email", "")
    feedback_type = body.get("feedback_type", "")
    message = body.get("message", "")

    if not feedback_type:
        raise AppException(
            message="Feedback type is required",
            error_code="VALIDATION_001",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": "feedback_type", "constraint": "Must be one of: general, bug, feature, suggestion, other"}
        )

    if not message:
        raise AppException(
            message="Message is required",
            error_code="VALIDATION_001",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": "message", "constraint": "Message cannot be empty"}
        )

    # Validate message length
    if len(message) > 1000:
        raise AppException(
            message="Message cannot exceed 1000 characters",
            error_code="VALIDATION_001",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": "message", "constraint": f"Maximum {1000} characters allowed"}
        )

    # Validate name length
    if len(name) > 100:
        raise AppException(
            message="Name cannot exceed 100 characters",
            error_code="VALIDATION_001",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": "name", "constraint": f"Maximum {100} characters allowed"}
        )

    # Validate feedback_type enum
    valid_types = ["general", "bug", "feature", "suggestion", "other"]
    if feedback_type not in valid_types:
        raise AppException(
            message="Invalid feedback type",
            error_code="VALIDATION_001",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": "feedback_type", "constraint": f"Must be one of: {', '.join(valid_types)}"}
        )

    # Validate email format if provided
    if email:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise AppException(
                message="Invalid email format",
                error_code="VALIDATION_001",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details={"field": "email", "constraint": "Please provide a valid email address"}
            )

    # Sanitize input
    message = sanitize_input(message)
    name = sanitize_input(name)

    # Validate rate limit (email-based)
    is_allowed, rate_info = await check_rate_limit(
        request,
        RateLimitAction.GENERAL,
        identifier=email if email else request.client.host if request.client else "unknown"
    )

    if not is_allowed:
        reset_timestamp = rate_info.get("reset_timestamp", 0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Rate limit exceeded. Please try again later.",
                "reset_at": reset_timestamp,
                "error_code": "AUTH_008"
            },
            headers={
                "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_timestamp),
                "Retry-After": str(max(0, reset_timestamp - int(__import__('time').time())))
            }
        )

    # Store submission
    try:
        db = await get_database()
    except Exception as e:
        logger.error(f"Failed to get database: {e}")
        set_database_available(False)
        raise AppException(
            message="Service temporarily unavailable",
            error_code="DB_001",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        result = await db.contact_submissions.insert_one({
            "name": name,
            "email": email,
            "feedback_type": feedback_type,
            "message": message,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent") or "",
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        logger.error(f"Failed to insert contact submission: {e}")
        raise AppException(
            message="Failed to submit feedback. Please try again later.",
            error_code="INTERNAL_002",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) from e

    logger.info(
        f"Contact submission received: type={feedback_type} from {email or 'anonymous'}",
        extra={
            "submission_id": str(result.inserted_id),
            "ip_address": request.client.host if request.client else None
        }
    )

    # Send email notification to admin (optional - don't fail if email fails)
    try:
        await send_contact_notification(result.inserted_id, feedback_type, name, email, message)
    except Exception as e:
        logger.warning(f"Failed to send contact notification email (non-critical): {e}")

    return APIResponse(
        success=True,
        message="Your feedback has been submitted successfully.",
        data={
            "submission_id": str(result.inserted_id)
        }
    )


async def send_contact_notification(submission_id: str, feedback_type: str, name: str, email: str, message: str):
    """
    Send email notification to admin about new contact submission.

    Args:
        submission_id: Submission ID
        feedback_type: Type of feedback
        name: Submitter name
        email: Submitter email
        message: Feedback message
    """
    try:
        from app.config import get_settings
        from app.services.email_service import EmailMessage, EmailService, get_email_service

        settings = get_settings()

        # Don't send email if SMTP is not configured
        if not settings.smtp_user or not settings.smtp_password:
            logger.info("SMTP not configured, skipping contact notification email")
            return

        email_service = await get_email_service()

        # Get admin email (use from settings or default)
        admin_email = settings.smtp_from_email
        if admin_email == "noreply@aicampus.com":
            logger.info("Using default admin email for notifications")
            # This is a placeholder - user should configure their admin email
            return

        # Create notification email
        notification_message = EmailMessage(
            to_email=admin_email,
            subject=f"New Contact Submission: {feedback_type}",
            body_text=f"""
New contact submission received from AI Campus Companion

Type: {feedback_type}
Name: {name or 'Anonymous'}
Email: {email or 'Not provided'}
Submission ID: {submission_id}

Message:
{message}

Created at: {datetime.utcnow().isoformat()}

---
This is an automated notification. You can view submissions in the MongoDB database.
""",
            body_html=f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Contact Submission</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
        }}
        .header {{
            background-color: #4a90d9;
            color: #ffffff;
            padding: 20px;
            border-radius: 8px 8px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            padding: 20px;
            color: #333333;
        }}
        .field {{
            margin: 10px 0;
        }}
        .label {{
            font-weight: bold;
            color: #666666;
            font-size: 14px;
        }}
        .value {{
            margin-left: 10px;
            font-size: 16px;
        }}
        .message {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            font-size: 12px;
            color: #666666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Contact Submission</h1>
        </div>
        <div class="content">
            <div class="field">
                <span class="label">Type:</span>
                <span class="value">{feedback_type}</span>
            </div>
            <div class="field">
                <span class="label">Name:</span>
                <span class="value">{name or 'Anonymous'}</span>
            </div>
            <div class="field">
                <span class="label">Email:</span>
                <span class="value">{email or 'Not provided'}</span>
            </div>
            <div class="field">
                <span class="label">Submission ID:</span>
                <span class="value">{submission_id}</span>
            </div>
            <div class="field">
                <span class="label">Message:</span>
                <div class="message">{message}</div>
            </div>
            <div class="field">
                <span class="label">Created at:</span>
                <span class="value">{datetime.utcnow().isoformat()}</span>
            </div>
        </div>
        <div class="footer">
            <p>This is an automated notification.</p>
        </div>
    </div>
</body>
</html>
"""
        )

        await email_service.send_email(notification_message)
        logger.info(f"Contact notification email sent successfully to {admin_email}")

    except Exception as e:
        # Don't fail the submission if email fails
        logger.error(f"Failed to send contact notification email (non-critical): {e}")
        raise


@router.get("/health")
async def contact_health_check() -> dict:
    """
    Health check endpoint for contact form API.

    Returns:
        API health status
    """
    return {
        "status": "healthy",
        "service": "contact_form",
        "database": "connected" if await is_database_available() else "disconnected"
    }
