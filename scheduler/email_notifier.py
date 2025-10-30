"""
Email Notifier
Generates and sends notification emails
"""

from utils.email_sender import EmailSender
from config.email_config import EMAIL_SUBJECT_PREFIX
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailNotifier:
    """Handles email notification generation and sending"""

    def __init__(self):
        self.email_sender = EmailSender()

    def send_changes_notification(self, user_email, first_name, changes_list):
        """
        Send notification email about product changes

        Args:
            user_email: User's email address
            first_name: User's first name
            changes_list: List of dicts with change information

        Returns:
            bool: Success status
        """
        if not changes_list:
            logger.warning("No changes to notify")
            return False

        # Generate email content
        subject = f"{EMAIL_SUBJECT_PREFIX} Price Alert - {len(changes_list)} Item(s) Updated"
        body_text = self._generate_text_email(first_name, changes_list)

        # Send email
        return self.email_sender.send_email(user_email, subject, body_text)

    def _generate_text_email(self, first_name, changes_list):
        """Generate plain text email body"""

        lines = []
        lines.append(f"Hi {first_name},")
        lines.append("")
        lines.append(f"Great news! {len(changes_list)} item(s) in your watchlist have changed:")
        lines.append("")
        lines.append("=" * 70)

        for idx, change_info in enumerate(changes_list, 1):
            product = change_info['product_info']
            changes = change_info['changes']
            current = change_info['current_state']
            previous = change_info.get('previous_state')

            lines.append("")
            lines.append(f"{idx}. {product['product_name']}")
            lines.append(f"   Color: {product['color_name']}")

            lines.append("")
            lines.append("   WHAT CHANGED:")

            for change_type in changes:
                if change_type == 'NOW_AVAILABLE':
                    lines.append("   ✅ Now Available!")

                elif change_type == 'PRICE_DROP':
                    old_price = previous['price'] if previous else current['price']
                    new_price = current['price']
                    savings = old_price - new_price if old_price and new_price else 0

                    lines.append(f"   💰 Price Drop!")
                    lines.append(f"      Was: ${old_price:.2f}")
                    lines.append(f"      Now: ${new_price:.2f}")
                    lines.append(f"      Save: ${savings:.2f}")

                    if current['discount_percent'] > 0:
                        lines.append(f"      Discount: {current['discount_percent']}% off")

                elif change_type == 'DISCOUNT_INCREASED':
                    lines.append(f"   🎉 Discount Increased!")
                    if previous:
                        lines.append(f"      Was: {previous['discount_percent']}% off")
                    lines.append(f"      Now: {current['discount_percent']}% off")

            lines.append("")
            lines.append(f"   🔗 View Product: {product['product_url']}")
            lines.append("")
            lines.append("-" * 70)

        lines.append("")
        lines.append("Happy shopping!")
        lines.append("")
        lines.append("-- Nike Shoe Tracker")
        lines.append("")
        lines.append("(This is an automated notification. You're receiving this because")
        lines.append("these items are in your watchlist.)")

        return "\n".join(lines)

    def test_email(self, recipient_email):
        """Send a test email"""
        subject = f"{EMAIL_SUBJECT_PREFIX} Test Email"
        body = """This is a test email from Nike Shoe Tracker.

If you're receiving this, your email configuration is working correctly!

-- Nike Shoe Tracker"""

        return self.email_sender.send_email(recipient_email, subject, body)