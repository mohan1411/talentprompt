"""SMTP Email Service for production use."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import jinja2

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service that sends real emails via SMTP."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
        
        # Initialize Jinja2 for email templates
        self.template_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        logger.info(f"SMTP Email Service initialized with host: {self.smtp_host}:{self.smtp_port}")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send an email via SMTP."""
        try:
            # Run the blocking SMTP operation in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._send_email_sync,
                to_email,
                subject,
                html_content,
                text_content,
                cc,
                bcc
            )
            return result
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Synchronous email sending via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add text part
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server
            if self.smtp_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            # Login
            server.login(self.smtp_user, self.smtp_password)
            
            # Send email
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            server.send_message(msg, from_addr=self.from_email, to_addrs=recipients)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email} with subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending email to {to_email}: {e}")
            return False
    
    async def send_submission_invitation(
        self,
        to_email: str,
        candidate_name: str,
        recruiter_name: str,
        submission_link: str,
        message: str,
        deadline_days: int,
        company_name: str,
        is_update: bool = False,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Send invitation email to candidate."""
        try:
            subject = f"{'Update' if is_update else 'Submit'} Your Profile - {company_name}"
            
            # Format expiration date
            if expires_at:
                expiry_date = expires_at.strftime("%B %d, %Y")
            else:
                expiry_date = (datetime.utcnow() + timedelta(days=deadline_days)).strftime("%B %d, %Y")
            
            # Create HTML content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2563eb;">Hello {candidate_name},</h2>
                    
                    <p>{recruiter_name} from {company_name} has requested that you {'update' if is_update else 'submit'} your profile.</p>
                    
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Message from {recruiter_name}:</strong></p>
                        <p style="margin: 10px 0 0 0; font-style: italic;">"{message}"</p>
                    </div>
                    
                    <p>Please click the button below to {'update' if is_update else 'submit'} your information:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{submission_link}" style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            {'Update My Profile' if is_update else 'Submit My Profile'}
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        <strong>Important:</strong> This link will expire on {expiry_date} ({deadline_days} days from now).
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        If the button doesn't work, you can copy and paste this link into your browser:<br>
                        <a href="{submission_link}" style="color: #2563eb; word-break: break-all;">{submission_link}</a>
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="color: #666; font-size: 12px;">
                        This email was sent by {company_name} via Promtitude. If you did not expect this email, please disregard it.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Create text content
            text_content = f"""
Hello {candidate_name},

{recruiter_name} from {company_name} has requested that you {'update' if is_update else 'submit'} your profile.

Message from {recruiter_name}:
"{message}"

Please visit the following link to {'update' if is_update else 'submit'} your information:
{submission_link}

Important: This link will expire on {expiry_date} ({deadline_days} days from now).

This email was sent by {company_name} via Promtitude. If you did not expect this email, please disregard it.
            """.strip()
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending submission invitation: {e}")
            return False
    
    async def send_submission_notification(
        self,
        to_email: str,
        candidate_name: str,
        submission_type: str,
        dashboard_url: Optional[str] = None
    ) -> bool:
        """Send notification to recruiter about new submission."""
        try:
            action = "updated" if submission_type == "update" else "submitted"
            subject = f"New Profile Submission - {candidate_name}"
            
            # Generate dashboard URL if not provided
            if not dashboard_url:
                dashboard_url = f"{settings.FRONTEND_URL}/dashboard/resumes"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2563eb;">New Profile Submission Received</h2>
                    
                    <p><strong>{candidate_name}</strong> has {action} their profile.</p>
                    
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Submission Details:</strong></p>
                        <ul style="margin: 10px 0 0 0;">
                            <li>Candidate: {candidate_name}</li>
                            <li>Type: Profile {'Update' if submission_type == 'update' else 'Submission'}</li>
                            <li>Time: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</li>
                        </ul>
                    </div>
                    
                    <p>You can view the {'updated' if submission_type == 'update' else 'new'} profile in your dashboard:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{dashboard_url}" style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            View in Dashboard
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="color: #666; font-size: 12px;">
                        This is an automated notification from Promtitude. You're receiving this because a candidate responded to your profile request.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
New Profile Submission Received

{candidate_name} has {action} their profile.

Submission Details:
- Candidate: {candidate_name}
- Type: Profile {'Update' if submission_type == 'update' else 'Submission'}
- Time: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}

You can view the {'updated' if submission_type == 'update' else 'new'} profile in your dashboard:
{dashboard_url}

This is an automated notification from Promtitude. You're receiving this because a candidate responded to your profile request.
            """.strip()
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending submission notification: {e}")
            return False
    
    async def send_submission_confirmation(
        self,
        to_email: str,
        candidate_name: str
    ) -> bool:
        """Send confirmation email to candidate after submission."""
        try:
            subject = "Profile Submission Confirmed - Promtitude"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2563eb;">Thank You, {candidate_name}!</h2>
                    
                    <p>We've successfully received your profile submission.</p>
                    
                    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0;">✅ Your information has been securely saved</p>
                        <p style="margin: 10px 0 0 0;">✅ The recruiter has been notified</p>
                    </div>
                    
                    <p>The recruiter will review your information and may reach out if there's a good match for current or future opportunities.</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="color: #666; font-size: 12px;">
                        This is an automated confirmation from Promtitude. Please do not reply to this email.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
Thank You, {candidate_name}!

We've successfully received your profile submission.

✅ Your information has been securely saved
✅ The recruiter has been notified

The recruiter will review your information and may reach out if there's a good match for current or future opportunities.

This is an automated confirmation from Promtitude. Please do not reply to this email.
            """.strip()
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending submission confirmation: {e}")
            return False
    
    async def send_test_email(
        self,
        to_email: str
    ) -> bool:
        """Send a test email to verify configuration."""
        try:
            subject = f"Promtitude Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #2563eb;">Promtitude Email Test</h1>
                    <p>This is a test email from your Promtitude application.</p>
                    
                    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>Configuration:</strong></p>
                        <ul style="margin: 5px 0;">
                            <li>SMTP Host: {self.smtp_host}</li>
                            <li>SMTP Port: {self.smtp_port}</li>
                            <li>From: {self.from_email}</li>
                            <li>Time: {datetime.now()}</li>
                        </ul>
                    </div>
                    
                    <p>If you received this email, your email configuration is working correctly!</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280;">
                        <p>This is an automated test email from Promtitude.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
Promtitude Email Test

This is a test email from your Promtitude application.

Configuration:
- SMTP Host: {self.smtp_host}
- SMTP Port: {self.smtp_port}
- From: {self.from_email}
- Time: {datetime.now()}

If you received this email, your email configuration is working correctly!

This is an automated test email from Promtitude.
            """.strip()
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str
    ) -> bool:
        """Send email verification."""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        subject = "Verify your Promtitude email"
        
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Promtitude!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>Or copy and paste this URL into your browser:</p>
            <p>{verification_url}</p>
            <br>
            <p>Best regards,<br>The Promtitude Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
Welcome to Promtitude!

Please verify your email address by visiting:
{verification_url}

Best regards,
The Promtitude Team
"""
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset(
        self,
        to_email: str,
        reset_token: str
    ) -> bool:
        """Send password reset email."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Reset your Promtitude password"
        
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password. Click the link below to proceed:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>Or copy and paste this URL into your browser:</p>
            <p>{reset_url}</p>
            <p>If you didn't request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The Promtitude Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
Password Reset Request

We received a request to reset your password. Visit the link below:
{reset_url}

If you didn't request this, please ignore this email.

Best regards,
The Promtitude Team
"""
        
        return await self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()