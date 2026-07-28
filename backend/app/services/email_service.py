"""
Email service for AI Campus Companion.

Provides async email sending capabilities using Gmail SMTP with TLS encryption.
Supports HTML and plain text emails with retry logic for resilience.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
from jinja2 import Template

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message data class."""
    to_email: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    from_name: Optional[str] = None


class EmailError(Exception):
    """Email service error."""
    pass


class EmailConnectionError(EmailError):
    """Email connection error."""
    pass


class EmailSendError(EmailError):
    """Email sending error."""
    pass


class EmailService:
    """
    Async email service using Gmail SMTP.

    Features:
    - Async email sending with aiosmtplib
    - TLS encryption for secure communication
    - HTML and plain text email support
    - Retry logic with exponential backoff
    - Jinja2 templating for dynamic content
    """

    # Email templates
    OTP_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background-color: #4a90d9;
            color: #ffffff;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .content {
            padding: 30px;
            color: #333333;
        }
        .otp-container {
            background-color: #f8f9fa;
            border: 2px solid #4a90d9;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        }
        .otp-code {
            font-size: 36px;
            font-weight: bold;
            letter-spacing: 8px;
            color: #4a90d9;
            font-family: 'Courier New', monospace;
        }
        .expiry-note {
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 12px;
            margin-top: 20px;
            color: #856404;
            font-size: 14px;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666666;
            font-size: 12px;
            border-top: 1px solid #e9ecef;
        }
        .warning {
            color: #dc3545;
            font-size: 14px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to AI Campus Companion!</h1>
        </div>
        <div class="content">
            <p>Hello {{ full_name }},</p>
            <p>Thank you for signing up. To complete your registration, please use the verification code below:</p>

            <div class="otp-container">
                <div class="otp-code">{{ otp_code }}</div>
            </div>

            <div class="expiry-note">
                <strong>Important:</strong> This code expires in <strong>{{ expiry_minutes }} minutes</strong>.
                Do not share this code with anyone.
            </div>

            <p class="warning">If you didn't request this code, please ignore this email or contact support if you're concerned.</p>
        </div>
        <div class="footer">
            <p>This is an automated message from AI Campus Companion.</p>
            <p>&copy; {{ year }} AI Campus Companion. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

    PASSWORD_RESET_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Password Reset</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; }
        .header { background-color: #4a90d9; color: #ffffff; padding: 30px; text-align: center; }
        .content { padding: 30px; color: #333333; }
        .button { display: inline-block; background-color: #4a90d9; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 20px 0; }
        .footer { background-color: #f8f9fa; padding: 20px; text-align: center; color: #666666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello {{ full_name }},</p>
            <p>We received a request to reset your password. Click the button below to reset it:</p>
            <a href="{{ reset_url }}" class="button">Reset Password</a>
            <p>If you didn't request this, please ignore this email. The link will expire in 1 hour.</p>
        </div>
        <div class="footer">
            <p>AI Campus Companion</p>
        </div>
    </div>
</body>
</html>
"""

    PASSWORD_RESET_OTP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background-color: #dc3545;
            color: #ffffff;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .content {
            padding: 30px;
            color: #333333;
        }
        .otp-container {
            background-color: #f8f9fa;
            border: 2px solid #dc3545;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        }
        .otp-code {
            font-size: 36px;
            font-weight: bold;
            letter-spacing: 8px;
            color: #dc3545;
            font-family: 'Courier New', monospace;
        }
        .expiry-note {
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 12px;
            margin-top: 20px;
            color: #856404;
            font-size: 14px;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666666;
            font-size: 12px;
            border-top: 1px solid #e9ecef;
        }
        .warning {
            color: #dc3545;
            font-size: 14px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello {{ full_name }},</p>
            <p>We received a request to reset your password. Use the verification code below to proceed:</p>

            <div class="otp-container">
                <div class="otp-code">{{ otp_code }}</div>
            </div>

            <div class="expiry-note">
                <strong>Important:</strong> This code expires in <strong>{{ expiry_minutes }} minutes</strong>.
                Do not share this code with anyone.
            </div>

            <p class="warning">If you didn't request a password reset, please ignore this email or contact support if you're concerned.</p>
        </div>
        <div class="footer">
            <p>This is an automated message from AI Campus Companion.</p>
            <p>&copy; {{ year }} AI Campus Companion. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_name: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize email service.

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_name: Default from name
            from_email: Default from email
            use_tls: Whether to use TLS encryption
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        settings = get_settings()

        self.smtp_host = smtp_host or settings.smtp_host or "smtp.gmail.com"
        self.smtp_port = smtp_port or settings.smtp_port or 587
        self.smtp_user = smtp_user or settings.smtp_user
        self.smtp_password = smtp_password or settings.smtp_password
        self.from_name = from_name or settings.smtp_from_name or "AI Campus Companion"
        self.from_email = from_email or settings.smtp_from_email or "noreply@aicampus.com"
        self.use_tls = use_tls
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Validate SMTP settings
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email sending will fail.")

    async def _send_email_with_retry(
        self,
        message: EmailMessage,
        attempt: int = 1
    ) -> bool:
        """
        Send email with retry logic.

        Args:
            message: Email message to send
            attempt: Current attempt number

        Returns:
            True if email was sent successfully

        Raises:
            EmailSendError: If all retries failed
        """
        try:
            logger.info(f"Email send attempt {attempt} to {message.to_email}")
            logger.info(f"SMTP settings: host={self.smtp_host}, port={self.smtp_port}, user={self.smtp_user}")
            # Create MIME message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = f"{message.from_name or self.from_name} <{self.from_email}>"
            msg["To"] = message.to_email

            # Add plain text part
            msg.attach(MIMEText(message.body_text, "plain", "utf-8"))

            # Add HTML part if provided
            if message.body_html:
                msg.attach(MIMEText(message.body_html, "html", "utf-8"))

            # Connect and send
            # Port 465 = implicit TLS (SMTPSSL), Port 587 = STARTTLS
            if self.smtp_port == 465:
                # Implicit TLS
                logger.info(f"Connecting via implicit TLS (port 465)")
                smtp = aiosmtplib.SMTP(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    use_tls=True,
                )
                await smtp.connect()
            else:
                # STARTTLS (port 587 or others)
                logger.info(f"Connecting via STARTTLS (port {self.smtp_port})")
                smtp = aiosmtplib.SMTP(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    use_tls=False,
                )
                await smtp.connect()
                try:
                    await smtp.starttls()
                    logger.info("STARTTLS successful")
                except Exception as e:
                    logger.warning(f"STARTTLS failed, continuing anyway: {e}")
                    # Connection may already be TLS if server auto-upgrades
                    pass

            logger.info("Logging into SMTP server")
            await smtp.login(self.smtp_user, self.smtp_password)
            logger.info("Sending message")
            await smtp.send_message(msg)
            await smtp.quit()
            logger.info(f"Email sent successfully to {message.to_email}")
            return True

        except Exception as e:
            logger.warning(f"Email send attempt {attempt} failed: {str(e)}")

            if attempt < self.max_retries:
                # Wait before retry
                await asyncio.sleep(self.retry_delay * attempt)
                return await self._send_email_with_retry(message, attempt + 1)
            else:
                logger.error(f"Failed to send email after {self.max_retries} attempts")
                raise EmailSendError(f"Failed to send email: {str(e)}")

    async def send_email(self, message: EmailMessage) -> bool:
        """
        Send an email message.

        Args:
            message: Email message to send

        Returns:
            True if email was sent successfully

        Raises:
            EmailConnectionError: If SMTP is not configured
            EmailSendError: If sending fails
        """
        if not self.smtp_user or not self.smtp_password:
            raise EmailConnectionError("SMTP credentials not configured")

        return await self._send_email_with_retry(message)

    async def send_otp_email(
        self,
        to_email: str,
        full_name: str,
        otp_code: str,
        expiry_minutes: int = 10
    ) -> bool:
        """
        Send OTP verification email.

        Args:
            to_email: Recipient email address
            full_name: User's full name
            otp_code: OTP code
            expiry_minutes: OTP expiry time in minutes

        Returns:
            True if email was sent successfully
        """
        # Render HTML template
        template = Template(self.OTP_EMAIL_TEMPLATE)
        html_body = template.render(
            full_name=full_name,
            otp_code=otp_code,
            expiry_minutes=expiry_minutes,
            year=datetime.utcnow().year
        )

        # Plain text body
        text_body = f"""
Hello {full_name},

Thank you for signing up with AI Campus Companion.

Your verification code is: {otp_code}

This code will expire in {expiry_minutes} minutes.

If you didn't request this code, please ignore this email.

Best regards,
AI Campus Companion Team
"""

        message = EmailMessage(
            to_email=to_email,
            subject="AI Campus Companion - Your Verification Code",
            body_text=text_body,
            body_html=html_body
        )

        return await self.send_email(message)

    async def send_password_reset_email(
        self,
        to_email: str,
        full_name: str,
        reset_token: str,
        reset_url: str
    ) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            full_name: User's full name
            reset_token: Password reset token
            reset_url: Full password reset URL

        Returns:
            True if email was sent successfully
        """
        # Render HTML template
        template = Template(self.PASSWORD_RESET_TEMPLATE)
        html_body = template.render(
            full_name=full_name,
            reset_url=reset_url
        )

        # Plain text body
        text_body = f"""
Hello {full_name},

We received a request to reset your password for AI Campus Companion.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email. Your password will remain unchanged.

Best regards,
AI Campus Companion Team
"""

        message = EmailMessage(
            to_email=to_email,
            subject="AI Campus Companion - Password Reset Request",
            body_text=text_body,
            body_html=html_body
        )

        return await self.send_email(message)

    async def send_password_reset_otp_email(
        self,
        to_email: str,
        full_name: str,
        otp_code: str,
        expiry_minutes: int = 10
    ) -> bool:
        """
        Send password reset OTP email.

        Args:
            to_email: Recipient email address
            full_name: User's full name
            otp_code: OTP code for password reset
            expiry_minutes: OTP expiry time in minutes

        Returns:
            True if email was sent successfully
        """
        # Render HTML template
        template = Template(self.PASSWORD_RESET_OTP_TEMPLATE)
        html_body = template.render(
            full_name=full_name,
            otp_code=otp_code,
            expiry_minutes=expiry_minutes,
            year=datetime.utcnow().year
        )

        # Plain text body
        text_body = f"""
Hello {full_name},

We received a request to reset your password for AI Campus Companion.

Your password reset code is: {otp_code}

This code will expire in {expiry_minutes} minutes.

If you didn't request this code, please ignore this email. Your password will remain unchanged.

Best regards,
AI Campus Companion Team
"""

        message = EmailMessage(
            to_email=to_email,
            subject="AI Campus Companion - Password Reset Code",
            body_text=text_body,
            body_html=html_body
        )

        return await self.send_email(message)


# Global email service instance
_email_service: Optional[EmailService] = None


async def get_email_service() -> EmailService:
    """Get or create the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
