"""
Notification Scheduler
Main orchestrator for watchlist monitoring and notifications
"""

from datetime import datetime
from collections import defaultdict

from scheduler.watchlist_manager import WatchlistManager
from scheduler.change_detector import ChangeDetector
from scheduler.email_notifier import EmailNotifier
from utils.database_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NotificationScheduler:
    """Orchestrates the notification workflow"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.watchlist_manager = WatchlistManager()
        self.change_detector = ChangeDetector(self.db_manager)
        self.email_notifier = EmailNotifier()

    def run(self):
        """
        Main execution method
        1. Load watchlist
        2. Detect changes for each item
        3. Group by user
        4. Send notifications
        5. Update last_notified timestamps
        """
        logger.info("=" * 70)
        logger.info("STARTING NOTIFICATION SCHEDULER")
        logger.info("=" * 70)

        try:
            # Test database connection
#             if not self.db_manager.test_connection():
#                 logger.error("Database connection failed. Exiting.")
#                 return

            # Load data
            logger.info("\n📋 Loading watchlist and users...")
            users = self.watchlist_manager.load_users()
            watchlist = self.watchlist_manager.load_watchlist()

            if not watchlist:
                logger.warning("⚠️  Watchlist is empty. Nothing to check.")
                return

            logger.info(f"✅ Loaded {len(watchlist)} watchlist items for {len(users)} users")

            # Detect changes for all watched items
            logger.info("\n🔍 Detecting changes...")
            user_changes = self._detect_all_changes(watchlist)

            if not user_changes:
                logger.info("✅ No changes detected. No notifications to send.")
                return

            # Send notifications
            logger.info(f"\n📧 Sending notifications to {len(user_changes)} users...")
            self._send_notifications(users, user_changes, watchlist)

            logger.info("\n" + "=" * 70)
            logger.info("NOTIFICATION SCHEDULER COMPLETED")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Error in notification scheduler: {e}", exc_info=True)
#         finally:
#             self.db_manager.close_all_connections()

    def _detect_all_changes(self, watchlist):
        """
        Detect changes for all watchlist items

        Returns:
            dict: {user_id: [change_info_dicts]}
        """
        user_changes = defaultdict(list)

        for item in watchlist:
            try:
                unique_size_id = item['unique_size_id']
                user_id = item['user_id']
                watchlist_id = item['watchlist_id']
                last_notified = item.get('last_notified_timestamp', '')

                logger.info(f"Checking {unique_size_id}...")

                # Detect changes
                result = self.change_detector.detect_changes(unique_size_id, last_notified)

                if result['has_changes']:
                    # Get full product info
                    product_info = self.change_detector.get_product_info(unique_size_id)

                    if product_info:
                        change_data = {
                            'watchlist_id': watchlist_id,
                            'unique_size_id': unique_size_id,
                            'changes': result['changes'],
                            'current_state': result['current_state'],
                            'previous_state': result['previous_state'],
                            'product_info': product_info
                        }

                        user_changes[user_id].append(change_data)
                        logger.info(f"  ✅ Changes detected: {', '.join(result['changes'])}")
                    else:
                        logger.warning(f"  ⚠️  Could not get product info for {unique_size_id}")
                else:
                    logger.info(f"  ℹ️  No changes")

            except Exception as e:
                logger.error(f"Error checking {item.get('unique_size_id', 'unknown')}: {e}")
                continue

        return dict(user_changes)

    def _send_notifications(self, users, user_changes, watchlist):
        """Send email notifications to users with changes"""

        success_count = 0
        fail_count = 0

        for user_id, changes_list in user_changes.items():
            try:
                user = users.get(user_id)
                if not user:
                    logger.warning(f"User {user_id} not found in users list")
                    continue

                user_email = user['email']
                first_name = user['first_name']

                logger.info(f"\n📧 Sending notification to {first_name} ({user_email})...")
                logger.info(f"   {len(changes_list)} item(s) changed")

                # Send email
                success = self.email_notifier.send_changes_notification(
                    user_email,
                    first_name,
                    changes_list
                )

                if success:
                    success_count += 1

                    # Update last_notified timestamps
                    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    for change in changes_list:
                        self.watchlist_manager.update_last_notified(
                            change['watchlist_id'],
                            current_timestamp
                        )

                    logger.info(f"   ✅ Notification sent and timestamps updated")
                else:
                    fail_count += 1
                    logger.error(f"   ❌ Failed to send notification")

            except Exception as e:
                fail_count += 1
                logger.error(f"Error sending notification to {user_id}: {e}")

        logger.info(f"\n📊 Notification Summary:")
        logger.info(f"   ✅ Successful: {success_count}")
        logger.info(f"   ❌ Failed: {fail_count}")

    def test_notification_system(self, test_email):
        """Test the notification system with a test email"""
        logger.info("Testing notification system...")

        # Test database connection
        if not self.db_manager.test_connection():
            logger.error("Database connection test failed")
            return False

        # Test email sending
        success = self.email_notifier.test_email(test_email)

        if success:
            logger.info("✅ Notification system test successful!")
        else:
            logger.error("❌ Notification system test failed")

        return success