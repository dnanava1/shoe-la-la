"""
Database management utilities
Handles inserting/updating scraped data into AWS RDS (PostgreSQL)
"""

import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from utils.logger import setup_logger
import os
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)


class DatabaseManager:
    """Manages all database operations (inserts, updates, historical logs)"""

    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                sslmode='require'
            )
            # ❗ Important: Disable autocommit for manual transaction control
            self.conn.autocommit = False
            logger.info("✅ Connected to AWS RDS successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    # -----------------------------------------------------------------------
    # TABLE OPERATIONS (core tables)
    # -----------------------------------------------------------------------

    def save_main_products(self, main_products):
        """Insert or update main products"""
        query = """
        INSERT INTO main_products (main_product_id, name, category, base_url, tag)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (main_product_id) DO NOTHING;
        """
        data = [
            (p.get('main_product_id'), p.get('name'), p.get('category'),
             p.get('base_url'), p.get('tag'))
            for p in main_products
        ]
        self._execute_batch(query, data, "main_products")

    def save_fit_variants(self, fit_variations):
        """Insert or update fit variants"""
        query = """
        INSERT INTO fit_variants (unique_fit_id, main_product_id, fit_product_id, fit_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (unique_fit_id) DO NOTHING;
        """
        data = [
            (f.get('unique_fit_id'), f.get('main_product_id'),
             f.get('fit_product_id'), f.get('fit_name'))
            for f in fit_variations
        ]
        self._execute_batch(query, data, "fit_variants")

    def save_color_variants(self, color_variations):
        """Insert or update color variants"""
        query = """
        INSERT INTO color_variants (
            unique_color_id, unique_fit_id,
            color_product_id, color_name,
            color_image_url, color_url, style, shown
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (unique_color_id) DO NOTHING;
        """
        data = [
            (c.get('unique_color_id'), c.get('unique_fit_id'),
             c.get('color_product_id'), c.get('color_name'),
             c.get('color_image_url'), c.get('color_url'),
             c.get('style'), c.get('shown'))
            for c in color_variations
        ]
        self._execute_batch(query, data, "color_variants")

    def save_size_variants(self, size_variants):
        """Insert or update size variants"""
        query = """
        INSERT INTO size_variants (unique_size_id, unique_color_id, size, size_label)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (unique_size_id) DO NOTHING;
        """
        data = [
            (s.get('unique_size_id'), s.get('unique_color_id'),
             s.get('size'), s.get('size_label'))
            for s in size_variants
        ]
        self._execute_batch(query, data, "size_variants")

    # -----------------------------------------------------------------------
    # HISTORICAL DATA (prices table) - HYBRID BATCHING
    # -----------------------------------------------------------------------

    def save_price_logs(self, records, batch_size=500):
        """
        Insert new change logs into prices table using hybrid batching.
        Attempts batch insert; if a batch fails, falls back to row-by-row
        insert for that specific batch, logging individual errors.
        """
        if not records:
            logger.info("No historical records to save.")
            return

        # 🧹 Convert invalid numeric strings ("N/A", "", etc.) to None
        def safe_float(value):
            if isinstance(value, str):
                value = value.strip()
            if value in ("N/A", "", None):
                return None
            try:
                # Handle potential currency symbols or commas if necessary
                # value = str(value).replace('$', '').replace(',', '')
                return float(value)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert '{value}' to float, using None.")
                return None

        # --- SQL Query --- (Using named placeholders is clearer)
        insert_query = """
        INSERT INTO prices (
            unique_size_id, available, price, original_price,
            discount_percent, change_type
        )
        VALUES (
            %(unique_size_id)s, %(available)s, %(price)s, %(original_price)s,
            %(discount_percent)s, %(change_type)s
        );
        """

        # --- Counters ---
        total_inserted_count = 0
        total_failed_count = 0
        total_processed = 0

        # --- Process records in batches ---
        for i in range(0, len(records), batch_size):
            batch_records_raw = records[i : i + batch_size]
            total_processed += len(batch_records_raw)
            logger.info(f"Processing batch {i // batch_size + 1} ({len(batch_records_raw)} records)...")

            # 1. Clean data for the current batch
            batch_data_cleaned = []
            for rec in batch_records_raw:
                # Ensure boolean conversion if 'available' is string 'True'/'False'
                available_bool = None
                available_raw = rec.get("available")
                if isinstance(available_raw, str):
                    available_bool = available_raw.lower() == 'true'
                elif isinstance(available_raw, bool):
                    available_bool = available_raw

                cleaned_record = {
                    "unique_size_id": rec.get("unique_size_id"),
                    "available": available_bool,
                    "price": safe_float(rec.get("price")),
                    "original_price": safe_float(rec.get("original_price")),
                    # Use safe_float for discount too, handle potential % sign if needed
                    "discount_percent": int(safe_float(rec.get("discount_percent"))) if safe_float(rec.get("discount_percent")) is not None else None,
                    "change_type": rec.get("change_type"),
                }
                batch_data_cleaned.append(cleaned_record)

            # 2. Attempt batch insert within a transaction
            try:
                with self.conn.cursor() as cur:
                    # Manually start transaction block if needed (depends on psycopg2 version/settings)
                    # cur.execute("BEGIN;") # Often not needed if autocommit=False
                    execute_batch(cur, insert_query, batch_data_cleaned, page_size=batch_size)
                    self.conn.commit() # Commit the successful batch
                    total_inserted_count += len(batch_data_cleaned)
                    logger.debug(f"Batch {i // batch_size + 1} inserted successfully.")

            except Exception as batch_error:
                # 3. Batch failed - Rollback and Fallback to row-by-row
                self.conn.rollback() # Rollback the failed batch attempt
                logger.warning(
                    f"⚠️ Batch {i // batch_size + 1} failed: {batch_error}. "
                    f"Falling back to row-by-row insertion for this batch."
                )
                batch_inserted_count = 0
                batch_failed_count = 0

                try:
                    with self.conn.cursor() as cur_single:
                        for record_dict in batch_data_cleaned:
                            try:
                                cur_single.execute(insert_query, record_dict)
                                self.conn.commit() # Commit each successful single insert
                                batch_inserted_count += 1
                            except Exception as row_error:
                                self.conn.rollback() # Rollback the single failed insert
                                batch_failed_count += 1
                                logger.error(
                                    f"❌ Error inserting row for "
                                    f"unique_size_id '{record_dict.get('unique_size_id')}': {row_error}"
                                )
                    total_inserted_count += batch_inserted_count
                    total_failed_count += batch_failed_count
                    logger.info(f"Fallback complete for batch {i // batch_size + 1}: "
                                f"{batch_inserted_count} inserted, {batch_failed_count} failed.")
                except Exception as fallback_critical_error:
                    # Handle potential errors during the fallback cursor setup itself
                    logger.critical(f"❌ CRITICAL error during fallback processing "
                                    f"for batch {i // batch_size + 1}: {fallback_critical_error}")
                    total_failed_count += len(batch_data_cleaned) - batch_inserted_count # Assume remaining failed

        # 4. Final Summary Logging
        logger.info(f"✅ ---- Historical Data Save Summary ----")
        logger.info(f"Total records processed: {total_processed}")
        logger.info(f"Successfully inserted: {total_inserted_count}")
        if total_failed_count > 0:
            logger.warning(f"⚠️ Failed to insert: {total_failed_count}. See error logs above.")
        logger.info(f"---------------------------------------")

    # --- Other fetch methods remain the same ---

    def fetch_latest_historical_data(self):
        """Fetch the latest historical record per size"""
        # ... (keep existing code) ...
        query = """
        SELECT p1.unique_size_id, p1.capture_timestamp, p1.available,
               p1.price, p1.original_price, p1.discount_percent, p1.change_type
        FROM prices p1
        INNER JOIN (
            SELECT unique_size_id, MAX(capture_timestamp) AS max_ts
            FROM prices
            GROUP BY unique_size_id
        ) p2 ON p1.unique_size_id = p2.unique_size_id AND p1.capture_timestamp = p2.max_ts;
        """
        try:
            # Ensure connection is valid before reading
            if self.conn is None or self.conn.closed:
                 raise Exception("Database connection is closed.")
            return pd.read_sql(query, self.conn)
        except Exception as e:
            logger.error(f"❌ Error fetching latest historical data: {e}")
            # Optional: Reconnect or handle error differently
            return pd.DataFrame()

    def fetch_historical_by_size(self, unique_size_id):
        """Fetch full history for one product size"""
        # ... (keep existing code) ...
        query = """
        SELECT unique_size_id, capture_timestamp, available, price,
               original_price, discount_percent, change_type
        FROM prices
        WHERE unique_size_id = %s
        ORDER BY capture_timestamp;
        """
        try:
             if self.conn is None or self.conn.closed:
                 raise Exception("Database connection is closed.")
             return pd.read_sql(query, self.conn, params=[unique_size_id])
        except Exception as e:
            logger.error(f"❌ Error fetching history for {unique_size_id}: {e}")
            return pd.DataFrame()


    def fetch_historical_statistics(self):
        """Return basic stats for the prices table"""
        # ... (keep existing code, but ensure transaction state is clean) ...
        stats_data = {}
        try:
             if self.conn is None or self.conn.closed:
                 raise Exception("Database connection is closed.")
             with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) AS total_records,
                           COUNT(DISTINCT unique_size_id) AS unique_sizes,
                           COUNT(DISTINCT capture_timestamp) AS scraping_runs
                    FROM prices;
                """)
                stats = cur.fetchone()

                cur.execute("""
                    SELECT change_type, COUNT(*) FROM prices GROUP BY change_type;
                """)
                change_counts = dict(cur.fetchall())
             # No changes needed? Commit/rollback is usually not required for SELECT
             # self.conn.commit() # Or rollback if there was an error implicitly? Usually not needed.
             stats_data = {
                 "total_records": stats[0] if stats else 0,
                 "unique_sizes": stats[1] if stats else 0,
                 "scraping_runs": stats[2] if stats else 0,
                 "change_counts": change_counts
             }
        except Exception as e:
            logger.error(f"❌ Error fetching historical stats: {e}")
            self.conn.rollback() # Rollback if SELECT caused an error state
        finally:
            return stats_data


    # -----------------------------------------------------------------------
    # INTERNAL HELPER - NOW COMMITS ON SUCCESS
    # -----------------------------------------------------------------------

    def _execute_batch(self, query, data, table_name):
        """Batch execute a list of inserts/updates and commit on success."""
        if not data:
            logger.warning(f"No data to insert for {table_name}. Skipping.")
            return
        try:
            with self.conn.cursor() as cur:
                # Start transaction if needed (often implicit with autocommit=False)
                # cur.execute("BEGIN;")
                execute_batch(cur, query, data, page_size=500)
            self.conn.commit() # Commit the transaction if execute_batch was successful
            logger.info(f"✅ Inserted/updated {len(data)} records into {table_name} and committed.")
        except Exception as e:
            self.conn.rollback() # Rollback the transaction on error
            logger.error(f"❌ Error inserting into {table_name}: {e}. Transaction rolled back.")
            # Optionally re-raise the exception if you want the calling code to know
            # raise e