import os
from typing import List, Dict, Any, Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from config.config import (
    ENABLE_EMAIL_NOTIFICATIONS,
    NOTIFICATION_EMAIL,
    SENDGRID_API_KEY,
    FROM_EMAIL,
    STATUS_UPCOMING,
    STATUS_CLOSING_SOON,
    STATUS_EXPIRED
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NotificationManager:
    """Manage notifications for grant status changes"""
    
    def __init__(self):
        """Initialize the notification manager"""
        self.email_enabled = ENABLE_EMAIL_NOTIFICATIONS
        self.notification_email = NOTIFICATION_EMAIL
        self.from_email = FROM_EMAIL
        self.sendgrid_api_key = SENDGRID_API_KEY
        
    def notify_status_change(
        self, 
        grant_id: str,
        grant_name: str, 
        old_status: str, 
        new_status: str, 
        grant_url: Optional[str] = None
    ) -> bool:
        """
        Send notifications for important status changes
        
        Args:
            grant_id: The ID of the grant
            grant_name: The name of the grant
            old_status: The previous status
            new_status: The new status
            grant_url: Optional URL to the grant
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        # Only notify for important status changes
        if new_status not in [STATUS_UPCOMING, STATUS_CLOSING_SOON, STATUS_EXPIRED]:
            return False
            
        # Compose notification message
        subject = f"Grant Status Change: {grant_name}"
        
        if new_status == STATUS_UPCOMING:
            message = f"The grant '{grant_name}' is now upcoming (In uscita)."
        elif new_status == STATUS_CLOSING_SOON:
            message = f"The grant '{grant_name}' is now closing soon (In scadenza)."
        elif new_status == STATUS_EXPIRED:
            message = f"The grant '{grant_name}' has expired (Scaduto)."
        
        if grant_url:
            message += f"\n\nYou can view the grant at: {grant_url}"
            
        message += f"\n\nGrant ID: {grant_id}"
        
        # Send email notification if enabled
        if self.email_enabled and self.notification_email and self.from_email:
            return self._send_email_notification(subject, message)
            
        # Log notification even if email is not sent
        logger.info(f"Notification: {subject} - {message}")
        return True
        
    def _send_email_notification(self, subject: str, message: str) -> bool:
        """
        Send an email notification using SendGrid
        
        Args:
            subject: Email subject
            message: Email body
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.sendgrid_api_key:
            logger.error("SendGrid API key not configured")
            return False
            
        try:
            email = Mail(
                from_email=self.from_email,
                to_emails=self.notification_email,
                subject=subject,
                plain_text_content=message
            )
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(email)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email notification sent successfully: {subject}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False