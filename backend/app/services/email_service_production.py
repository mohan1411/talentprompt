"""Production email service that uses SMTP when configured, falls back to mock."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import jinja2

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_email_service():
    """Get the appropriate email service based on configuration."""
    # Check if SMTP is configured
    if all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        logger.info("Using SMTP email service")
        try:
            from app.services.email_service_smtp import EmailService
            return EmailService()
        except ImportError as e:
            logger.error(f"Failed to import SMTP email service: {e}")
            logger.warning("Falling back to mock email service")
    else:
        logger.info("SMTP not configured, using mock email service")
    
    # Fall back to mock service
    from app.services.email_service import EmailService
    return EmailService()


# Create singleton instance
email_service = get_email_service()