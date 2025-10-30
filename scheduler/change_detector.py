"""
Change Detector
Detects price and availability changes for watched items
"""
from datetime import datetime, timezone
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ChangeDetector:
    """Detects meaningful changes in product price/availability"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def detect_changes(self, unique_size_id, last_notified_timestamp=None):
        """
        Detect changes for a watched item

        Args:
            unique_size_id: Product size ID
            last_notified_timestamp: When user was last notified (None = first time)

        Returns:
            dict: {
                'has_changes': bool,
                'changes': list of change descriptions,
                'current_state': dict with current data,
                'previous_state': dict with previous data
            }
        """
        conn = None
        result = {
            'has_changes': False,
            'changes': [],
            'current_state': None,
            'previous_state': None
        }

        try:
            conn = self.db_manager.get_connection()

            # Get current state
            current_state = self._get_current_state(conn, unique_size_id)
            if not current_state:
                logger.warning(f"Product {unique_size_id} not found in database")
                return result

            result['current_state'] = current_state

            if not last_notified_timestamp or str(last_notified_timestamp).lower() in ['nan', 'none', '']:
                last_notified_timestamp = datetime(2025, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
                logger.info(f"No last_notified_timestamp found for {unique_size_id}, using fallback {last_notified_timestamp}")


            # Get previous state (last known state when notified)
            previous_state = self._get_state_at_timestamp(conn, unique_size_id, last_notified_timestamp)
            if not previous_state:
                logger.warning(f"No historical data found for {unique_size_id}")
                return result

            result['previous_state'] = previous_state

            # Detect changes
            changes = self._compare_states(previous_state, current_state)

            if changes:
                result['has_changes'] = True
                result['changes'] = changes

            return result

        except Exception as e:
            logger.error(f"Error detecting changes for {unique_size_id}: {e}")
            return result
        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def _get_current_state(self, conn, unique_size_id):
        """Get current state from size_availability table"""
        cursor = conn.cursor()

        query = """
            SELECT unique_size_id, capture_timestamp, available,
                   price, original_price,
                   discount_percent, change_type
            FROM prices
            WHERE unique_size_id = %s
            ORDER BY capture_timestamp DESC
            LIMIT 1;
        """

        try:
            cursor.execute(query, (unique_size_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                'unique_size_id': row[0],
                'capture_timestamp': row[1],
                'available': row[2],
                'price': float(row[3]) if row[3] else None,
                'original_price': float(row[4]) if row[4] else None,
                'discount_percent': float(row[5]) if row[5] else 0.0,
                'change_type': row[6] or ''
            }

        finally:
            cursor.close()

    def _get_state_at_timestamp(self, conn, unique_size_id, timestamp):
        """Get historical state closest to the given timestamp"""
        cursor = conn.cursor()

        query = """
            SELECT unique_size_id, capture_timestamp, available,
                   price, original_price,
                   discount_percent, change_type
            FROM prices
            WHERE unique_size_id = %s
            AND capture_timestamp <= %s::timestamptz
            ORDER BY capture_timestamp DESC
            LIMIT 1;
        """

        try:
            cursor.execute(query, (unique_size_id, timestamp))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                'unique_size_id': row[0],
                'capture_timestamp': row[1],
                'available': row[2],
                'price': float(row[3]) if row[3] else None,
                'original_price': float(row[4]) if row[4] else None,
                'discount_percent': float(row[5]) if row[5] else 0.0,
                'change_type': row[6] or ''
            }

        finally:
            cursor.close()

    def _compare_states(self, previous, current):
        """
        Compare previous and current states to detect changes

        Returns:
            list: List of change types
        """
        changes = []

        # Check availability change (unavailable → available)
        if not previous['available'] and current['available']:
            changes.append('NOW_AVAILABLE')

        # Check price decrease
        if previous['price'] and current['price']:
            if current['price'] < previous['price']:
                drop_amount = previous['price'] - current['price']
                drop_percent = (drop_amount / previous['price']) * 100
                changes.append(f'PRICE_DROP')
                logger.info(f"Price dropped ${drop_amount:.2f} ({drop_percent:.0f}%)")

        # Check discount increase (only if price decreased)
        if current['discount_percent'] > previous['discount_percent']:
            if 'PRICE_DROP' not in changes:  # Don't double-report
                changes.append('DISCOUNT_INCREASED')

        return changes

    def get_product_info(self, unique_size_id):
        """Get full product information for display"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT mp.name, cv.color_name, cv.color_url, sv.size_label
                FROM size_variants sv
                JOIN color_variants cv ON sv.unique_color_id = cv.unique_color_id
                JOIN main_products mp ON SPLIT_PART(cv.unique_color_id, '_', 1) = mp.main_product_id
                WHERE sv.unique_size_id = %s
                LIMIT 1;
            """

            cursor.execute(query, (unique_size_id,))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                'product_name': row[0],
                'color_name': row[1],
                'product_url': row[2],
                'size_label': row[3]
            }

        except Exception as e:
            logger.error(f"Error getting product info: {e}")
            return None
        finally:
            if conn:
                cursor.close()
                self.db_manager.return_connection(conn)