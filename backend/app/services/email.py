"""Email service for sending emails."""

import logging
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content (optional)
            from_email: Sender email (uses settings default if not provided)
            from_name: Sender name (uses settings default if not provided)
            
        Returns:
            True if email was sent successfully
        """
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            logger.warning("Email service not configured, skipping email send")
            logger.info(f"Would send email to {to_email}: {subject}")
            return True
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name or settings.EMAILS_FROM_NAME} <{from_email or settings.EMAILS_FROM_EMAIL}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            msg.attach(MIMEText(body_html, 'html'))
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_verification_email(
        to_email: str,
        full_name: str,
        verification_url: str
    ) -> bool:
        """Send account verification email."""
        subject = "Verify your Promtitude account"
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Promtitude!</h1>
                </div>
                <div class="content">
                    <p>Hi {full_name},</p>
                    <p>Thank you for signing up for Promtitude! To complete your registration, please verify your email address by clicking the button below:</p>
                    <center>
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #4F46E5;">{verification_url}</p>
                    <p>This link will expire in 48 hours.</p>
                    <p>If you didn't create an account with Promtitude, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Promtitude. All rights reserved.</p>
                    <p>AI-powered recruitment made simple.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Hi {full_name},
        
        Welcome to Promtitude! Please verify your email address by visiting the link below:
        
        {verification_url}
        
        This link will expire in 48 hours.
        
        If you didn't create an account, you can safely ignore this email.
        
        Best regards,
        The Promtitude Team
        """
        
        return await EmailService.send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text
        )
    
    @staticmethod
    async def send_welcome_email(
        to_email: str,
        full_name: str
    ) -> bool:
        """Send welcome email after verification."""
        subject = "Welcome to Promtitude - Let's get started!"
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .feature {{ margin: 15px 0; padding: 15px; background: white; border-left: 4px solid #4F46E5; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Promtitude!</h1>
                </div>
                <div class="content">
                    <p>Hi {full_name},</p>
                    <p>Your email has been verified successfully! You're all set to start using Promtitude's AI-powered recruitment features.</p>
                    
                    <h2>Here's what you can do:</h2>
                    
                    <div class="feature">
                        <strong>🔍 Natural Language Search</strong><br>
                        Find candidates by describing what you need in plain English
                    </div>
                    
                    <div class="feature">
                        <strong>📊 AI Resume Screening</strong><br>
                        Let AI help you identify the best matches for your roles
                    </div>
                    
                    <div class="feature">
                        <strong>💬 Interview Assistant</strong><br>
                        Get real-time coaching and insights during interviews
                    </div>
                    
                    <div class="feature">
                        <strong>✉️ Smart Outreach</strong><br>
                        Generate personalized messages to engage candidates
                    </div>
                    
                    <center>
                        <a href="{settings.FRONTEND_URL}/dashboard" class="button">Go to Dashboard</a>
                    </center>
                    
                    <p>Need help getting started? Check out our <a href="{settings.FRONTEND_URL}/help">help center</a> or reply to this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Promtitude. All rights reserved.</p>
                    <p>AI-powered recruitment made simple.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Hi {full_name},
        
        Welcome to Promtitude! Your email has been verified successfully.
        
        You can now access all of Promtitude's AI-powered recruitment features:
        
        - Natural Language Search: Find candidates by describing what you need
        - AI Resume Screening: Identify the best matches for your roles
        - Interview Assistant: Get real-time coaching during interviews
        - Smart Outreach: Generate personalized candidate messages
        
        Get started: {settings.FRONTEND_URL}/dashboard
        
        Need help? Visit {settings.FRONTEND_URL}/help
        
        Best regards,
        The Promtitude Team
        """
        
        return await EmailService.send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text
        )


email_service = EmailService()