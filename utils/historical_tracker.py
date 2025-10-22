"""
Historical data tracking
Maintains a time-series CSV file that tracks size availability and pricing over time
"""

import os
import pandas as pd
from config.constants import (
    HISTORICAL_FILE_PATH,
    HISTORICAL_STATIC_COLUMNS,
    HISTORICAL_TRACKED_COLUMNS
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class HistoricalTracker:
    """Tracks size availability and pricing changes over time"""

    def __init__(self, historical_file_path=HISTORICAL_FILE_PATH):
        self.historical_file_path = historical_file_path
        self.static_columns = HISTORICAL_STATIC_COLUMNS
        self.tracked_columns = HISTORICAL_TRACKED_COLUMNS

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

            # Load existing historical data or create new
            if os.path.exists(self.historical_file_path):
                historical_df = pd.read_csv(self.historical_file_path)
                logger.info(f"Loaded existing historical data: {len(historical_df)} products")
            else:
                historical_df = pd.DataFrame(columns=self.static_columns)
                logger.info("Creating new historical data file")

            # Prepare new data with timestamp columns
            new_data_prepared = self._prepare_new_data(new_df, timestamp)

            # Merge with historical data
            updated_df = self._merge_data(historical_df, new_data_prepared)

            # Save updated historical data
            updated_df.to_csv(self.historical_file_path, index=False)
            logger.info(f"✅ Historical data updated: {len(updated_df)} total products")
            logger.info(f"   Added {len(updated_df.columns) - len(historical_df.columns)} new columns")
            logger.info(f"   Saved to: {self.historical_file_path}")

            return True

        except Exception as e:
            logger.error(f"Error updating historical data: {e}", exc_info=True)
            return False

    def _prepare_new_data(self, new_df, timestamp):
        """
        Prepare new data by renaming tracked columns with timestamp prefix

        Args:
            new_df: DataFrame with new data
            timestamp: Timestamp string

        Returns:
            DataFrame with renamed columns
        """
        # Start with static columns
        prepared_df = new_df[self.static_columns].copy()

        # Rename tracked columns with timestamp prefix
        for col in self.tracked_columns:
            if col in new_df.columns:
                new_col_name = f"{timestamp}_{col}"
                prepared_df[new_col_name] = new_df[col]

        return prepared_df

    def _merge_data(self, historical_df, new_df):
        """
        Merge historical and new data

        Args:
            historical_df: Existing historical DataFrame
            new_df: New data DataFrame with timestamp columns

        Returns:
            Merged DataFrame
        """
        if historical_df.empty:
            # First run - just return new data
            return new_df

        # Merge on unique_size_id (outer join to keep all products)
        merged_df = historical_df.merge(
            new_df,
            on='unique_size_id',
            how='outer',
            suffixes=('', '_new')
        )

        # Handle static columns - prefer existing values, fill with new if missing
        for col in self.static_columns:
            if col != 'unique_size_id':  # Skip the merge key
                new_col = f"{col}_new"
                if new_col in merged_df.columns:
                    # Fill missing values in original column with new values
                    merged_df[col] = merged_df[col].fillna(merged_df[new_col])
                    # Drop the _new column
                    merged_df.drop(columns=[new_col], inplace=True)

        # Reorder columns: static columns first, then timestamp columns sorted
        static_cols = [col for col in self.static_columns if col in merged_df.columns]
        timestamp_cols = [col for col in merged_df.columns if col not in self.static_columns]
        timestamp_cols.sort()  # Sort chronologically

        ordered_columns = static_cols + timestamp_cols
        merged_df = merged_df[ordered_columns]

        # Fill NaN with empty string for better CSV readability
        merged_df = merged_df.fillna('')

        return merged_df

    def get_product_history(self, unique_size_id):
        """
        Get historical data for a specific product

        Args:
            unique_size_id: Unique size identifier

        Returns:
            dict: Historical data for the product or None if not found
        """
        try:
            if not os.path.exists(self.historical_file_path):
                logger.warning("Historical data file does not exist")
                return None

            df = pd.read_csv(self.historical_file_path)
            product_data = df[df['unique_size_id'] == unique_size_id]

            if product_data.empty:
                logger.warning(f"Product {unique_size_id} not found in historical data")
                return None

            return product_data.iloc[0].to_dict()

        except Exception as e:
            logger.error(f"Error retrieving product history: {e}")
            return None

    def get_statistics(self):
        """
        Get statistics about the historical data

        Returns:
            dict: Statistics including total products, number of scraping runs, etc.
        """
        try:
            if not os.path.exists(self.historical_file_path):
                return {
                    'exists': False,
                    'total_products': 0,
                    'scraping_runs': 0
                }

            df = pd.read_csv(self.historical_file_path)

            # Count timestamp columns (each run adds 4 columns)
            timestamp_cols = [col for col in df.columns if col not in self.static_columns]
            scraping_runs = len(timestamp_cols) // len(self.tracked_columns)

            # Extract unique timestamps
            timestamps = set()
            for col in timestamp_cols:
                timestamp = col.rsplit('_', 1)[0]  # Get timestamp part before last underscore
                timestamps.add(timestamp)

            return {
                'exists': True,
                'total_products': len(df),
                'scraping_runs': scraping_runs,
                'total_columns': len(df.columns),
                'timestamps': sorted(list(timestamps))
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return None