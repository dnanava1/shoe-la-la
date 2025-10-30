"""
Watchlist Manager
Handles loading and updating watchlist data from CSV
"""

import pandas as pd
import os
from datetime import datetime, timezone
from config.email_config import USERS_CSV_PATH, WATCHLIST_CSV_PATH
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WatchlistManager:
    """Manages watchlist and user data from CSV files"""

    def __init__(self):
        self.users_path = USERS_CSV_PATH
        self.watchlist_path = WATCHLIST_CSV_PATH
        self._ensure_data_files_exist()

    def _ensure_data_files_exist(self):
        """Create data directory and sample files if they don't exist"""
        os.makedirs('data', exist_ok=True)

        # Create sample users.csv if doesn't exist
        if not os.path.exists(self.users_path):
            logger.warning(f"Users file not found. Creating sample at {self.users_path}")
            sample_users = pd.DataFrame({
                'user_id': ['user_001', 'user_002'],
                'user_email': ['user1@example.com', 'user2@example.com'],
                'first_name': ['John', 'Jane']
            })
            sample_users.to_csv(self.users_path, index=False)

        # Create sample watchlist.csv if doesn't exist
        if not os.path.exists(self.watchlist_path):
            logger.warning(f"Watchlist file not found. Creating sample at {self.watchlist_path}")
            sample_watchlist = pd.DataFrame({
                'watchlist_id': ['watch_001', 'watch_002'],
                'user_id': ['user_001', 'user_001'],
                'unique_size_id': ['SAMPLE_ID_1', 'SAMPLE_ID_2'],
                'added_timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * 2,
                'last_notified_timestamp': ['', '']
            })
            sample_watchlist.to_csv(self.watchlist_path, index=False)

    def load_users(self):
        """
        Load users from CSV

        Returns:
            dict: {user_id: {email, first_name}}
        """
        try:
            df = pd.read_csv(self.users_path)
            users = {}

            for _, row in df.iterrows():
                users[row['user_id']] = {
                    'email': row['user_email'],
                    'first_name': row.get('first_name', 'User')
                }

            logger.info(f"Loaded {len(users)} users")
            return users

        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return {}

    def load_watchlist(self):
        """
        Load watchlist from CSV

        Returns:
            list: List of watchlist items as dicts
        """
        try:
            df = pd.read_csv(self.watchlist_path)

            # Convert to list of dicts
            watchlist = df.to_dict('records')

            logger.info(f"Loaded {len(watchlist)} watchlist items")
            return watchlist

        except Exception as e:
            logger.error(f"Error loading watchlist: {e}")
            return []

    def update_last_notified(self, watchlist_id, timestamp=None):
        """
        Update last_notified_timestamp for a watchlist item

        Args:
            watchlist_id: ID of watchlist item
            timestamp: Timestamp to set (defaults to now)
        """
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f+00')


            df = pd.read_csv(self.watchlist_path)

            # Update the timestamp
            df.loc[df['watchlist_id'] == watchlist_id, 'last_notified_timestamp'] = timestamp

            # Save back to CSV
            df.to_csv(self.watchlist_path, index=False)

            logger.info(f"Updated last_notified for {watchlist_id} to {timestamp}")
            return True

        except Exception as e:
            logger.error(f"Error updating last_notified: {e}")
            return False

    def get_user_watchlist(self, user_id):
        """
        Get all watchlist items for a specific user

        Args:
            user_id: User ID

        Returns:
            list: Watchlist items for this user
        """
        watchlist = self.load_watchlist()
        return [item for item in watchlist if item['user_id'] == user_id]

    def add_to_watchlist(self, user_id, unique_size_id):
        """
        Add an item to user's watchlist (only if user exists)

        Args:
            user_id (str): User ID
            unique_size_id (str): Product size ID to watch

        Returns:
            str | None: watchlist_id of created item, or None if failed
        """
        try:
            # Load users to validate user_id
            users_df = pd.read_csv(self.users_path)
            if user_id not in users_df['user_id'].values:
                logger.error(f"Cannot add to watchlist: user_id '{user_id}' not found in users.csv")
                print(f"❌ User '{user_id}' not found in users.csv. Please add user first.")
                return None

            df = pd.read_csv(self.watchlist_path)

            # Generate new watchlist_id
            if df.empty or 'watchlist_id' not in df.columns:
                new_id = "watch_001"
            else:
                max_id = df['watchlist_id'].str.extract(r'watch_(\d+)').astype(float).max()[0]
                next_id_num = int(max_id) + 1 if not pd.isna(max_id) else 1
                new_id = f"watch_{next_id_num:03d}"

            # Check if the same item already exists for this user
            exists = ((df['user_id'] == user_id) & (df['unique_size_id'] == unique_size_id)).any()
            if exists:
                logger.warning(f"User '{user_id}' already watching '{unique_size_id}'")
                print(f"⚠️  Item '{unique_size_id}' already in watchlist for user '{user_id}'.")
                return None

            # Create new entry
            new_entry = pd.DataFrame([{
                'watchlist_id': new_id,
                'user_id': user_id,
                'unique_size_id': unique_size_id,
                'added_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_notified_timestamp': ''
            }])

            # Append and save
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(self.watchlist_path, index=False)

            logger.info(f"✅ Added {unique_size_id} to watchlist for user {user_id}")
            print(f"✅ Added {unique_size_id} to watchlist for user {user_id}")
            return new_id

        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
            print(f"❌ Error adding to watchlist: {e}")
            return None


    def remove_from_watchlist(self, watchlist_id):
        """
        Remove an item from watchlist

        Args:
            watchlist_id: Watchlist item ID
        """
        try:
            df = pd.read_csv(self.watchlist_path)
            df = df[df['watchlist_id'] != watchlist_id]
            df.to_csv(self.watchlist_path, index=False)

            logger.info(f"Removed {watchlist_id} from watchlist")
            return True

        except Exception as e:
            logger.error(f"Error removing from watchlist: {e}")
            return False