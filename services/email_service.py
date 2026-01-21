# services/email_service.py

import os
import smtplib
import logging
from email.mime.text import MIMEText
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def send_otp_email(email: str, otp: str):
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    # ─────────────────────────
    # HARD FAIL: env missing
    # ─────────────────────────
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.critical("SMTP credentials are missing in environment variables")
        raise HTTPException(
            status_code=500,
            detail="Email service not configured. Please contact support.",
        )

    msg = MIMEText(f"Your OTP code is: {otp}")
    msg["Subject"] = "Your OTP Code"
    msg["From"] = SMTP_USER
    msg["To"] = email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [email], msg.as_string())

            # log success for traceability (optional but useful)
            logger.info(f"OTP email accepted by SMTP for {email}")

    # ─────────────────────────
    # AUTH ERROR (VERY COMMON)
    # ─────────────────────────
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP auth failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Email service authentication failed. Please try later.",
        )

    # ─────────────────────────
    # CONNECTION / NETWORK
    # ─────────────────────────
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Unable to connect to email server. Please try later.",
        )

    # ─────────────────────────
    # ANY OTHER SMTP ERROR
    # ─────────────────────────
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error while sending OTP to {email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP email. Please try again later.",
        )

    # ─────────────────────────
    # UNKNOWN ERROR
    # ─────────────────────────
    except Exception as e:
        logger.exception(f"Unexpected error while sending OTP to {email}")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while sending OTP. Please try again later.",
        )
