"""
Email Configuration
SMTP settings for Gmail
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Gmail SMTP Configuration
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USE_TLS = True

# Email credentials (from environment variables)
SENDER_EMAIL = os.getenv('EMAIL_SENDER', 'your-email@gmail.com')
SENDER_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
SENDER_NAME = os.getenv('EMAIL_SENDER_NAME', 'Nike Shoe Tracker')

# Email settings
EMAIL_SUBJECT_PREFIX = '[Nike Tracker]'
DEFAULT_REPLY_TO = SENDER_EMAIL

# Notification settings
NOTIFICATION_ENABLED = os.getenv('NOTIFICATION_ENABLED', 'true').lower() == 'true'
DRY_RUN = os.getenv('EMAIL_DRY_RUN', 'false').lower() == 'true'  # If true, only log, don't send

# Mock data paths
USERS_CSV_PATH = 'data/users.csv'
WATCHLIST_CSV_PATH = 'data/watchlist.csv'