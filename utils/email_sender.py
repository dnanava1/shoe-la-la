"""
Email Sender
Low-level email sending utility using Gmail SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.email_config import (
    SMTP_HOST, SMTP_PORT, SMTP_USE_TLS,
    SENDER_EMAIL, SENDER_PASSWORD, SENDER_NAME,
    DRY_RUN
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailSender:
    """Handles sending emails via Gmail SMTP"""

    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.use_tls = SMTP_USE_TLS
        self.sender_email = SENDER_EMAIL
        self.sender_password = SENDER_PASSWORD
        self.sender_name = SENDER_NAME
        self.dry_run = DRY_RUN

    def send_email(self, recipient_email, subject, body_text, body_html=None):
        """
        Send an email

        Args:
            recipient_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)

        Returns:
            bool: Success status
        """
        if self.dry_run:
            logger.info("=" * 60)
            logger.info("DRY RUN - Email would be sent:")
            logger.info(f"To: {recipient_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body:\n{body_text}")
            logger.info("=" * 60)
            return True

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Add plain text part
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)

            # Add HTML part if provided
            if body_html:
                part2 = MIMEText(body_html, 'html')
                msg.attach(part2)

            # Connect and send
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            if self.use_tls:
                server.starttls()

            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipient_email, msg.as_string())
            server.quit()

            logger.info(f"✅ Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email to {recipient_email}: {e}")
            return False

    def test_connection(self):
        """Test SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            if self.use_tls:
                server.starttls()

            server.login(self.sender_email, self.sender_password)
            server.quit()

            logger.info("✅ SMTP connection test successful")
            return True

        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {e}")
            return False