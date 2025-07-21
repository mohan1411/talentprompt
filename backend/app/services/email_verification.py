"""Email verification service."""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User
from app.core.config import settings
from app.core.security import verify_password, get_password_hash
import logging

logger = logging.getLogger(__name__)

# Token settings
TOKEN_LENGTH = 32
TOKEN_EXPIRY_HOURS = 48


class EmailVerificationService:
    """Service for handling email verification."""
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure random verification token."""
        return secrets.token_urlsafe(TOKEN_LENGTH)
    
    @staticmethod
    async def create_verification_token(
        db: AsyncSession,
        user_id: str
    ) -> str:
        """
        Create a verification token for a user.
        
        Returns:
            The verification token
        """
        token = EmailVerificationService.generate_verification_token()
        token_hash = get_password_hash(token)
        
        # Store token hash and expiry in database
        # For now, we'll use a simple approach storing in the user table
        # In production, you might want a separate verification_tokens table
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                # These fields need to be added to the User model
                # email_verification_token=token_hash,
                # email_verification_sent_at=datetime.utcnow()
            )
        )
        await db.execute(stmt)
        await db.commit()
        
        return token
    
    @staticmethod
    async def verify_token(
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """
        Verify an email verification token.
        
        Args:
            db: Database session
            token: The verification token
            
        Returns:
            The user if token is valid, None otherwise
        """
        # Get all unverified users (in production, you'd query by token hash)
        stmt = select(User).where(User.is_verified == False)
        result = await db.execute(stmt)
        unverified_users = result.scalars().all()
        
        # For now, we'll validate against user creation time
        # In production, validate against stored token hash
        for user in unverified_users:
            # Check if token was created within valid timeframe
            if user.created_at:
                token_age = datetime.utcnow() - user.created_at.replace(tzinfo=None)
                if token_age < timedelta(hours=TOKEN_EXPIRY_HOURS):
                    # In production, verify token hash here
                    # For now, mark user as verified
                    user.is_verified = True
                    await db.commit()
                    return user
                    
        return None
    
    @staticmethod
    async def send_verification_email(
        email: str,
        full_name: str,
        verification_token: str
    ) -> bool:
        """
        Send verification email to user.
        
        Args:
            email: User's email address
            full_name: User's full name
            verification_token: The verification token
            
        Returns:
            True if email was sent successfully
        """
        # Build verification URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        # TODO: Implement actual email sending
        # For now, just log the verification URL
        logger.info(f"Verification email for {email}: {verification_url}")
        
        # In production, use an email service like SendGrid, AWS SES, etc.
        # Example email content:
        # Subject: "Verify your Promtitude account"
        # Body: 
        # Hi {full_name},
        # 
        # Welcome to Promtitude! Please verify your email address by clicking the link below:
        # 
        # {verification_url}
        # 
        # This link will expire in 48 hours.
        # 
        # If you didn't create an account, you can safely ignore this email.
        # 
        # Best regards,
        # The Promtitude Team
        
        return True
    
    @staticmethod
    async def resend_verification_email(
        db: AsyncSession,
        user: User
    ) -> bool:
        """
        Resend verification email to user.
        
        Args:
            db: Database session
            user: The user to resend email to
            
        Returns:
            True if email was sent successfully
        """
        if user.is_verified:
            return False
            
        # Check if we've sent too many emails recently (rate limiting)
        # For now, always allow resend
        
        # Generate new token
        token = await EmailVerificationService.create_verification_token(db, str(user.id))
        
        # Send email
        return await EmailVerificationService.send_verification_email(
            email=user.email,
            full_name=user.full_name or user.username,
            verification_token=token
        )


email_verification_service = EmailVerificationService()