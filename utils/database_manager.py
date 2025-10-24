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
            self.conn.autocommit = True
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
        ON CONFLICT (main_product_id) DO UPDATE
        SET name = EXCLUDED.name,
            category = EXCLUDED.category,
            base_url = EXCLUDED.base_url,
            tag = EXCLUDED.tag;
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
        ON CONFLICT (unique_fit_id) DO UPDATE
        SET fit_name = EXCLUDED.fit_name;
        """
        data = [
            (f.get('unique_fit_id'), f.get('main_product_id'),
             f.get('fit_product_id'), f.get('fit_name'))
            for f in fit_variations
        ]
        self._execute_batch(query, data, "fit_variants")

    def save_color_variants(self, color_variations):
        """Insert or update color variants (no main_product_id now)"""
        query = """
        INSERT INTO color_variants (
            unique_color_id, unique_fit_id,
            color_product_id, color_name,
            color_image_url, color_url, style, shown
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (unique_color_id) DO UPDATE
        SET color_name = EXCLUDED.color_name,
            color_image_url = EXCLUDED.color_image_url,
            color_url = EXCLUDED.color_url,
            style = EXCLUDED.style,
            shown = EXCLUDED.shown;
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
        ON CONFLICT (unique_size_id) DO UPDATE
        SET size = EXCLUDED.size,
            size_label = EXCLUDED.size_label;
        """
        data = [
            (s.get('unique_size_id'), s.get('unique_color_id'),
             s.get('size'), s.get('size_label'))
            for s in size_variants
        ]
        self._execute_batch(query, data, "size_variants")

    # -----------------------------------------------------------------------
    # HISTORICAL DATA (prices table)
    # -----------------------------------------------------------------------

    def save_price_logs(self, records):
        """Insert new change logs into prices table (timestamp auto-filled by DB)"""
        if not records:
            logger.info("No historical records to save.")
            return

        # 🟢 Remove 'timestamp' from both column list and values
        query = """
        INSERT INTO prices (
            unique_size_id,
            available, price, original_price,
            discount_percent, change_type
        )
        VALUES (%(unique_size_id)s, %(available)s,
                %(price)s, %(original_price)s,
                %(discount_percent)s, %(change_type)s);
        """

        try:
            with self.conn.cursor() as cur:
                execute_batch(cur, query, records, page_size=500)
            logger.info(f"✅ Inserted {len(records)} new historical records into prices")
        except Exception as e:
            logger.error(f"❌ Error inserting historical changes: {e}")


    def fetch_latest_historical_data(self):
        """Fetch the latest historical record per size"""
        query = """
        SELECT p1.unique_size_id, p1.capture_timestamp, p1.available,
               p1.price, p1.original_price, p1.discount_percent
        FROM prices p1
        INNER JOIN (
            SELECT unique_size_id, MAX(capture_timestamp) AS max_ts
            FROM prices
            GROUP BY unique_size_id
        ) p2 ON p1.unique_size_id = p2.unique_size_id AND p1.capture_timestamp = p2.max_ts;
        """
        try:
            return pd.read_sql(query, self.conn)
        except Exception as e:
            logger.error(f"❌ Error fetching latest historical data: {e}")
            return pd.DataFrame()

    def fetch_historical_by_size(self, unique_size_id):
        """Fetch full history for one product size"""
        query = """
        SELECT unique_size_id, capture_timestamp, available, price,
               original_price, discount_percent, change_type
        FROM prices
        WHERE unique_size_id = %s
        ORDER BY capture_timestamp;
        """
        try:
            return pd.read_sql(query, self.conn, params=[unique_size_id])
        except Exception as e:
            logger.error(f"❌ Error fetching history for {unique_size_id}: {e}")
            return pd.DataFrame()

    def fetch_historical_statistics(self):
        """Return basic stats for the prices table"""
        try:
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

            return {
                "total_records": stats[0],
                "unique_sizes": stats[1],
                "scraping_runs": stats[2],
                "change_counts": change_counts
            }
        except Exception as e:
            logger.error(f"❌ Error fetching historical stats: {e}")
            return {}

    # -----------------------------------------------------------------------
    # INTERNAL HELPER
    # -----------------------------------------------------------------------

    def _execute_batch(self, query, data, table_name):
        """Batch execute a list of inserts/updates"""
        if not data:
            logger.warning(f"No data to insert for {table_name}. Skipping.")
            return
        try:
            with self.conn.cursor() as cur:
                execute_batch(cur, query, data, page_size=500)
            logger.info(f"✅ Inserted/updated {len(data)} records into {table_name}")
        except Exception as e:
            logger.error(f"❌ Error inserting into {table_name}: {e}")
