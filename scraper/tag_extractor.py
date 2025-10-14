"""
Special tags extractor
Extracts special messaging tags like low stock warnings
"""

from config.constants import SELECTORS_SPECIAL_TAGS
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TagExtractor:
    """Extracts special tags and messages from product pages"""
    
    def extract_tags(self, page):
        """
        Extract all special tags from product page
        
        Args:
            page: Playwright page object
            
        Returns:
            str: Comma-separated special tags or empty string
        """
        special_tags = []
        
        try:
            # Check for low stock message
            low_stock_tag = self._check_low_stock(page)
            if low_stock_tag:
                special_tags.append(low_stock_tag)
            
            # Add more tag checks here as needed
            # Example: new_release_tag = self._check_new_release(page)
            
        except Exception as e:
            logger.error(f"    Error extracting special tags: {e}")
        
        return ", ".join(special_tags) if special_tags else ""
    
    def _check_low_stock(self, page):
        """Check for low stock/inventory warning"""
        try:
            low_stock_elem = page.query_selector(SELECTORS_SPECIAL_TAGS['low_stock'])
            if low_stock_elem:
                low_stock_text = low_stock_elem.inner_text().strip()
                # Check if text contains low stock indication
                if low_stock_text and "left" in low_stock_text.lower():
                    return "Low Stock"
        except Exception as e:
            logger.error(f"      Error checking low stock: {e}")
        
        return None