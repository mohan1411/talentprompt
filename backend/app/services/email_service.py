"""Mock email service for development without SMTP dependencies."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import jinja2

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Mock email service that logs emails instead of sending them."""
    
    def __init__(self):
        # Setup Jinja2 for email templates
        template_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.template_loader = jinja2.FileSystemLoader(searchpath=str(template_dir))
        self.template_env = jinja2.Environment(loader=self.template_loader)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Mock send an email - just log it."""
        # Use print to ensure it shows in console
        print("\n" + "="*50 + " MOCK EMAIL " + "="*50)
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"FROM: {settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>")
        
        # Extract submission link from HTML first
        import re
        link_match = re.search(r'href="([^"]+submit/[^"]+)"', html_content)
        submission_url = link_match.group(1) if link_match else None
        
        print("\nTEXT CONTENT:")
        print("-" * 112)
        print(text_content if text_content else 'None')
        print("-" * 112)
        
        if submission_url:
            print(f"\nSUBMISSION LINK: {submission_url}")
        
        print("\nHTML PREVIEW (email will be properly formatted):")
        print("-" * 112)
        # Show more complete preview
        if html_content:
            # Extract key parts from HTML
            import re
            # Get greeting
            greeting_match = re.search(r'<h1>([^<]+)</h1>', html_content)
            if greeting_match:
                print(f"Greeting: {greeting_match.group(1)}")
            
            # Get main message paragraphs
            paragraphs = re.findall(r'<p>([^<]+)</p>', html_content)
            if paragraphs:
                print("\nContent:")
                # Show introduction and custom message
                shown = 0
                for para in paragraphs:
                    para = para.strip()
                    if para and not para.startswith('©') and not para.startswith('This invitation'):
                        print(f"  {para}")
                        shown += 1
                        if shown >= 3:  # Limit to 3 paragraphs
                            break
            
            # Show button link
            button_match = re.search(r'<a[^>]+href="([^"]+)"[^>]+class="button"', html_content)
            if button_match:
                print(f"\nButton URL: {button_match.group(1)}")
        print("-" * 112)
        print("=" * 112 + "\n")
        
        # Also log it
        logger.info(f"Mock email sent to {to_email} with subject: {subject}")
        return True
    
    async def send_submission_invitation(
        self,
        to_email: str,
        candidate_name: str,
        recruiter_name: str,
        submission_link: str,
        message: str,
        deadline_days: int,
        company_name: Optional[str] = None,
        is_update: bool = False,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Send submission invitation email."""
        print(f"\n[MOCK EMAIL] send_submission_invitation called for {to_email}")
        print(f"[MOCK EMAIL] Submission link: {submission_link}")
        try:
            # Calculate expiration if not provided
            if expires_at is None:
                from datetime import datetime, timedelta
                expires_at = datetime.utcnow() + timedelta(days=deadline_days)
            
            # Render template with message included
            template = self.template_env.get_template("submission_invitation.html")
            html_content = template.render(
                candidate_name=candidate_name,
                recruiter_name=recruiter_name,
                company_name=company_name or "Promtitude",
                submission_link=submission_link,
                submission_url=submission_link,  # Template uses submission_url
                message=message,  # Pass the custom message to template
                deadline_days=deadline_days,
                is_update=is_update,
                expires_at=expires_at,
                current_year=2025
            )
            
            # Create text version with proper greeting
            text_content = f"""
Hello {candidate_name},

{recruiter_name} from {company_name or 'Promtitude'} {'has requested that you update your profile' if is_update else 'would like to invite you to submit your profile'}.

{message}

Please click the following link to {'update' if is_update else 'submit'} your information:
{submission_link}

This link will expire in {deadline_days} days.

Best regards,
{recruiter_name}
{company_name or ''}
            """.strip()
            
            # Set appropriate subject based on type
            if is_update:
                subject = f"Request to Update Your Profile - {company_name or 'Promtitude'}"
            else:
                subject = f"Invitation to Submit Your Profile - {company_name or 'Promtitude'}"
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
        except Exception as e:
            logger.error(f"Failed to send submission invitation: {str(e)}")
            return False
    
    async def send_submission_confirmation(
        self,
        to_email: str,
        candidate_name: str,
        company_name: Optional[str] = None
    ) -> bool:
        """Send confirmation email after submission."""
        subject = "Thank You for Your Submission"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Submission Received</h2>
                <p>Hi {candidate_name},</p>
                <p>Thank you for submitting your information. We have successfully received your profile and will review it shortly.</p>
                <p>If we have any questions or would like to move forward, we'll be in touch.</p>
                <p>Best regards,<br>
                {company_name or 'The Recruitment Team'}</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Hi {candidate_name},

Thank you for submitting your information. We have successfully received your profile and will review it shortly.

If we have any questions or would like to move forward, we'll be in touch.

Best regards,
{company_name or 'The Recruitment Team'}
        """.strip()
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_submission_notification(
        self,
        to_email: str,
        candidate_name: str,
        submission_type: str
    ) -> bool:
        """Notify recruiter of new candidate submission."""
        is_update = submission_type == 'update'
        subject = f"{'Profile Update' if is_update else 'New Candidate Submission'} - {candidate_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">{'Profile Update Received' if is_update else 'New Candidate Submission'}</h2>
                <p>Good news! A candidate has {'updated their profile' if is_update else 'submitted their information'}.</p>
                
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Candidate:</strong> {candidate_name}</p>
                    <p style="margin: 0;"><strong>Type:</strong> {'Profile Update' if submission_type == 'update' else 'New Submission'}</p>
                </div>
                
                <p>The candidate's information has been automatically processed and is now available in your resume database.</p>
                
                <div style="margin-top: 30px;">
                    <a href="{settings.FRONTEND_URL}/dashboard/resumes" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Resume
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
{'Profile Update Received' if is_update else 'New Candidate Submission'}

Good news! A candidate has {'updated their profile' if is_update else 'submitted their information'}.

Candidate: {candidate_name}
Type: {'Profile Update' if is_update else 'New Submission'}

The candidate's information has been automatically processed and is now available in your resume database.

View in dashboard: {settings.FRONTEND_URL}/dashboard/resumes
        """.strip()
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


# Create singleton instance
email_service = EmailService()