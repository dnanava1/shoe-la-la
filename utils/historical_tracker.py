"""
Historical data tracking - Change-based approach
Tracks only when availability, pricing, or discount changes occur
"""

import os
import pandas as pd
from config.constants import (
    HISTORICAL_FILE_PATH,
    HISTORICAL_STATIC_COLUMNS,
    HISTORICAL_TRACKED_COLUMNS,
    HISTORICAL_ALL_COLUMNS
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class HistoricalTracker:
    """Tracks size availability and pricing changes over time"""

    def __init__(self, historical_file_path=HISTORICAL_FILE_PATH):
        self.historical_file_path = historical_file_path

    def update_historical_data(self, new_size_availability, timestamp):
        """
        Update historical CSV with new scraping data

        Args:
            new_size_availability: List of dicts with new size availability data
            timestamp: Timestamp string in format YYYYMMDD_HHMMSS
        """
        logger.info("Updating historical size availability data...")

        try:
            # Convert new data to DataFrame
            new_df = pd.DataFrame(new_size_availability)

            # Load existing historical data
            if os.path.exists(self.historical_file_path):
                historical_df = pd.read_csv(self.historical_file_path)
                logger.info(f"Loaded existing historical data: {len(historical_df)} records")
            else:
                historical_df = pd.DataFrame(columns=self.ALL_COLUMNS)
                logger.info("Creating new historical data file")

            # Detect changes and create new records
            new_records = self._detect_changes(historical_df, new_df, timestamp)

            if new_records is not None and not new_records.empty:
                # Append new records to historical data
                historical_df = pd.concat([historical_df, new_records], ignore_index=True)

                # Save updated historical data
                historical_df.to_csv(self.historical_file_path, index=False)
                logger.info(f"✅ Added {len(new_records)} new records (changes detected)")
                logger.info(f"   Total historical records: {len(historical_df)}")
                logger.info(f"   Saved to: {self.historical_file_path}")
            else:
                logger.info("✅ No changes detected - historical file unchanged")

            return True

        except Exception as e:
            logger.error(f"Error updating historical data: {e}", exc_info=True)
            return False

    def _detect_changes(self, historical_df, new_df, timestamp):
        """
        Detect changes between historical and new data

        Args:
            historical_df: Existing historical DataFrame
            new_df: New data DataFrame
            timestamp: Current timestamp string

        Returns:
            DataFrame with only records that have changes
        """
        new_records = []

        # Get the latest record for each unique_size_id from historical data
        if not historical_df.empty:
            latest_historical = historical_df.sort_values('timestamp').groupby('unique_size_id').tail(1)
            latest_historical = latest_historical.set_index('unique_size_id')
        else:
            latest_historical = pd.DataFrame()

        # Check each new size entry
        for _, new_row in new_df.iterrows():
            unique_size_id = new_row['unique_size_id']

            # Check if this product exists in historical data
            if unique_size_id not in latest_historical.index:
                # NEW PRODUCT - Add as INITIAL
                record = self._create_record(new_row, timestamp, 'INITIAL')
                new_records.append(record)
                logger.info(f"  NEW: {unique_size_id}")
            else:
                # EXISTS - Check for changes
                old_row = latest_historical.loc[unique_size_id]
                changes = self._get_changes(old_row, new_row)

                if changes:
                    # CHANGED - Add new record
                    change_type = ','.join(changes)
                    record = self._create_record(new_row, timestamp, change_type)
                    new_records.append(record)
                    logger.info(f"  CHANGED: {unique_size_id} → {change_type}")
                # else: NO CHANGE - Skip (don't add record)

        if new_records:
            return pd.DataFrame(new_records)
        return None

    def _get_changes(self, old_row, new_row):
        """
        Compare old and new row to detect which fields changed
        Uses normalization to avoid false positives (e.g., 220.0 vs 220)

        Returns:
            list: List of field names that changed
        """
        changes = []

        for col in HISTORICAL_TRACKED_COLUMNS:
            old_val = self._normalize_value(old_row[col], col)
            new_val = self._normalize_value(new_row[col], col)

            if old_val != new_val:
                changes.append(col)

        return changes

    def _normalize_value(self, value, column):
        """
        Normalize values for accurate comparison
        Handles type inconsistencies (220.0 vs 220, "True" vs True, etc.)

        Args:
            value: The value to normalize
            column: The column name (determines normalization strategy)

        Returns:
            Normalized value for comparison
        """
        # Handle NaN/None/empty
        if pd.isna(value) or value == '' or value is None:
            return None

        # Numeric columns - normalize to float
        if column in ['price', 'original_price', 'discount_percent']:
            try:
                return float(value)
            except (ValueError, TypeError):
                # Can't convert to float, treat as string
                return str(value).strip().upper()

        # Boolean column - normalize to boolean
        if column == 'available':
            val_str = str(value).strip().upper()
            # Handle various boolean representations
            if val_str in ['TRUE', '1', 'YES', 'T', 'Y']:
                return True
            elif val_str in ['FALSE', '0', 'NO', 'F', 'N', '']:
                return False
            else:
                # Fallback to string comparison
                return val_str

        # Default: string comparison (case-insensitive, stripped)
        return str(value).strip().upper()

    def _create_record(self, row, timestamp, change_type):
        """Create a historical record from a data row"""
        record = {}

        # Add static columns
        for col in HISTORICAL_STATIC_COLUMNS:
            record[col] = row.get(col, '')

        # Add timestamp
        record['timestamp'] = timestamp

        # Add tracked columns
        for col in HISTORICAL_TRACKED_COLUMNS:
            record[col] = row.get(col, '')

        # Add change type
        record['change_type'] = change_type

        return record

    def get_product_history(self, unique_size_id):
        """
        Get full history for a specific product size

        Args:
            unique_size_id: Unique size identifier

        Returns:
            DataFrame: All historical records for this product
        """
        try:
            if not os.path.exists(self.historical_file_path):
                logger.warning("Historical data file does not exist")
                return None

            df = pd.read_csv(self.historical_file_path)
            product_history = df[df['unique_size_id'] == unique_size_id].sort_values('timestamp')

            if product_history.empty:
                logger.warning(f"Product {unique_size_id} not found in historical data")
                return None

            return product_history

        except Exception as e:
            logger.error(f"Error retrieving product history: {e}")
            return None

    def get_statistics(self):
        """
        Get statistics about the historical data

        Returns:
            dict: Statistics including total records, unique products, timestamps, etc.
        """
        try:
            if not os.path.exists(self.historical_file_path):
                return {
                    'exists': False,
                    'total_records': 0,
                    'unique_products': 0,
                    'scraping_runs': 0,
                    'changes_detected': 0
                }

            df = pd.read_csv(self.historical_file_path)

            # Count different types of changes
            change_counts = df['change_type'].value_counts().to_dict()

            return {
                'exists': True,
                'total_records': len(df),
                'unique_products': df['unique_size_id'].nunique(),
                'scraping_runs': df['timestamp'].nunique(),
                'timestamps': sorted(df['timestamp'].unique().tolist()),
                'change_counts': change_counts,
                'initial_records': len(df[df['change_type'] == 'INITIAL']),
                'change_records': len(df[df['change_type'] != 'INITIAL'])
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return None

    def get_recent_changes(self, limit=50):
        """
        Get most recent changes

        Args:
            limit: Maximum number of records to return

        Returns:
            DataFrame: Recent change records
        """
        try:
            if not os.path.exists(self.historical_file_path):
                return None

            df = pd.read_csv(self.historical_file_path)

            # Exclude INITIAL records, sort by timestamp descending
            changes = df[df['change_type'] != 'INITIAL'].sort_values('timestamp', ascending=False)

            return changes.head(limit)

        except Exception as e:
            logger.error(f"Error getting recent changes: {e}")
            return None