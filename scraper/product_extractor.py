"""
Product data extraction from main listing page
Extracts basic product information from product cards
"""

import hashlib
from config.constants import SELECTORS_MAIN_PRODUCT, BASE_URL, DEFAULT_VALUES
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProductExtractor:
    """Extracts product data from listing page cards"""
    
    @staticmethod
    def generate_product_id(base_url):
        # Create consistent hash from URL
        url_hash = hashlib.md5(base_url.encode()).hexdigest()[:8].upper()
        return f"PROD-{url_hash}"
    
    def extract_main_product(self, card):
        """
        Extract main product data from product card element
        
        Args:
            card: Playwright element handle for product card
            
        Returns:
            dict: Product data or None if extraction fails
        """
        try:

            base_url = self._extract_url(card)
            product_data = {
                'main_product_id': self.generate_product_id(base_url),
                'base_url': base_url
            }
            
            # Extract product name
            product_data['name'] = self._extract_name(card)
            if product_data['name'] == DEFAULT_VALUES['not_available']:
                return None
            
            # Extract category/subtitle
            product_data['category'] = self._extract_category(card)
            
            # Extract product URL
            product_data['base_url'] = self._extract_url(card)
            
            # Extract special tag (e.g., "Best Seller")
            product_data['tag'] = self._extract_tag(card)
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None
    
    def _extract_name(self, card):
        """Extract product name"""
        name_elem = card.query_selector(SELECTORS_MAIN_PRODUCT['title'])
        if name_elem:
            return name_elem.inner_text().strip()
        return DEFAULT_VALUES['not_available']
    
    def _extract_category(self, card):
        """Extract product category/subtitle"""
        subtitle_elem = card.query_selector(SELECTORS_MAIN_PRODUCT['subtitle'])
        if subtitle_elem:
            return subtitle_elem.inner_text().strip()
        return DEFAULT_VALUES['not_available']
    
    def _extract_url(self, card):
        """Extract and format product URL"""
        link_elem = card.query_selector(SELECTORS_MAIN_PRODUCT['link'])
        if link_elem:
            href = link_elem.get_attribute('href')
            if href:
                # Build full URL
                full_url = f"{BASE_URL}{href}" if href.startswith('/') else href
                # Remove color-specific part (last segment)
                base_url = '/'.join(full_url.split('/')[:-1])
                return base_url
        return DEFAULT_VALUES['not_available']
    
    def _extract_tag(self, card):
        """Extract special messaging tag (e.g., 'Best Seller')"""
        messaging_elem = card.query_selector(SELECTORS_MAIN_PRODUCT['messaging'])
        if messaging_elem:
            return messaging_elem.inner_text().strip()
        return ""