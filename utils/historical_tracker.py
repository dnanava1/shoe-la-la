"""
Historical data tracking - Change-based approach
Tracks only when availability, pricing, or discount changes occur
"""

import pandas as pd
from utils.logger import setup_logger

logger = setup_logger(__name__)


class HistoricalTracker:
    """Tracks size availability and pricing changes over time (stored in RDS)"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def update_historical_data(self, new_size_availability, timestamp):
        logger.info("Updating historical size availability data...")

        try:
            new_df = pd.DataFrame(new_size_availability)
            old_df = self.db_manager.fetch_latest_historical_data()
            logger.info(f"Loaded {len(old_df)} latest historical records from DB")

            new_records = self._detect_changes(old_df, new_df, timestamp)

            if new_records is not None and not new_records.empty:
                logger.info(f"✅ Detected {len(new_records)} new changes")
                self.db_manager.save_price_logs(new_records.to_dict(orient="records"))
                logger.info("📦 Saved changes to RDS successfully")
            else:
                logger.info("✅ No changes detected - historical data unchanged")

            return True

        except Exception as e:
            logger.error(f"Error updating historical data: {e}", exc_info=True)
            return False

    # -----------------------------------------------------------------------
    # CHANGE DETECTION
    # -----------------------------------------------------------------------

    def _detect_changes(self, historical_df, new_df, timestamp):
        """Detect changes between old (historical) and new data"""
        new_records = []

        # Get the latest known values by unique_size_id
        if not historical_df.empty:
            latest_historical = historical_df.set_index('unique_size_id')
        else:
            latest_historical = pd.DataFrame()

        for _, new_row in new_df.iterrows():
            unique_size_id = new_row['unique_size_id']

            if unique_size_id not in latest_historical.index:
                record = self._create_record(new_row, timestamp, 'INITIAL')
                new_records.append(record)
                logger.info(f"  NEW: {unique_size_id}")
            else:
                old_row = latest_historical.loc[unique_size_id]
                changes = self._get_changes(old_row, new_row)

                if changes:
                    change_type = ','.join(changes)
                    record = self._create_record(new_row, timestamp, change_type)
                    new_records.append(record)
                    logger.info(f"  CHANGED: {unique_size_id} → {change_type}")

        return pd.DataFrame(new_records) if new_records else None

    def _get_changes(self, old_row, new_row):
        """Detect which tracked columns changed"""
        tracked = ['available', 'price', 'original_price', 'discount_percent']
        changes = []

        for col in tracked:
            old_val = self._normalize_value(old_row[col])
            new_val = self._normalize_value(new_row[col])
            if old_val != new_val:
                changes.append(col)
        return changes

    def _normalize_value(self, value):
        """Normalize values for comparison"""
        if pd.isna(value) or value in ['', None]:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value).strip().upper()

    def _create_record(self, row, timestamp, change_type):
        """Format a new record for insertion"""
        return {
            'unique_size_id': row.get('unique_size_id'),
            'timestamp': timestamp,
            'available': row.get('available'),
            'price': row.get('price'),
            'original_price': row.get('original_price'),
            'discount_percent': row.get('discount_percent'),
            'change_type': change_type
        }

    # -----------------------------------------------------------------------
    # RETRIEVAL HELPERS
    # -----------------------------------------------------------------------

    def get_product_history(self, unique_size_id):
        """Fetch full history for a product from RDS"""
        return self.db_manager.fetch_historical_by_size(unique_size_id)

    def get_statistics(self):
        """Fetch overall statistics from RDS"""
        return self.db_manager.fetch_historical_statistics()
