"""
Run Notifications
Main entry point for running the notification scheduler manually
"""

import sys
import argparse
from scheduler.notification_scheduler import NotificationScheduler
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Nike Shoe Tracker - Notification Scheduler')
    parser.add_argument('--test', type=str, help='Test mode: send test email to specified address')

    args = parser.parse_args()

    print("=" * 70)
    print("NIKE SHOE TRACKER - NOTIFICATION SCHEDULER")
    print("=" * 70)
    print()

    scheduler = NotificationScheduler()

    if args.test:
        # Test mode
        logger.info(f"Running in TEST mode - sending test email to {args.test}")
        scheduler.test_notification_system(args.test)
    else:
        # Normal mode
        logger.info("Running notification scheduler...")
        scheduler.run()


if __name__ == "__main__":
    main()