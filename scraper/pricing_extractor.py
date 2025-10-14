"""
Pricing information extractor
Extracts current price, original price, and discount information
"""

import re
from config.constants import SELECTORS_PRICING, DEFAULT_VALUES
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PricingExtractor:
    """Extracts pricing and discount information"""
    
    def extract_pricing(self, page):
        """
        Extract pricing information from product page
        
        Args:
            page: Playwright page object
            
        Returns:
            dict: Pricing data (price, original_price, discount_percent)
        """
        price_data = {
            'price': DEFAULT_VALUES['not_available'],
            'original_price': DEFAULT_VALUES['not_available'],
            'discount_percent': DEFAULT_VALUES['no_discount']
        }
        
        try:
            # Look for main price container
            price_container = page.query_selector(SELECTORS_PRICING['price_container'])
            
            if price_container:
                price_data = self._extract_from_container(price_container)
            
            # Try alternative locations if not found
            if price_data['price'] == DEFAULT_VALUES['not_available']:
                price_data = self._extract_from_alternatives(page, price_data)
            
            # Calculate discount if both prices available
            if (price_data['price'] != DEFAULT_VALUES['not_available'] and 
                price_data['original_price'] != DEFAULT_VALUES['not_available'] and 
                price_data['discount_percent'] == DEFAULT_VALUES['no_discount']):
                price_data['discount_percent'] = self._calculate_discount(
                    price_data['price'], 
                    price_data['original_price']
                )
            
            # If no original price, set it equal to current price
            if (price_data['price'] != DEFAULT_VALUES['not_available'] and 
                price_data['original_price'] == DEFAULT_VALUES['not_available']):
                price_data['original_price'] = price_data['price']
                
        except Exception as e:
            logger.error(f"      Error extracting pricing: {e}")
        
        return price_data
    
    def _extract_from_container(self, price_container):
        """Extract prices from main price container"""
        price_data = {
            'price': DEFAULT_VALUES['not_available'],
            'original_price': DEFAULT_VALUES['not_available'],
            'discount_percent': DEFAULT_VALUES['no_discount']
        }
        
        # Current price
        current_price_elem = price_container.query_selector(SELECTORS_PRICING['current_price'])
        if current_price_elem:
            price_data['price'] = self._extract_price_number(current_price_elem.inner_text())
        
        # Original price
        original_price_elem = price_container.query_selector(SELECTORS_PRICING['original_price'])
        if original_price_elem:
            price_data['original_price'] = self._extract_price_number(original_price_elem.inner_text())
        
        # Discount percentage
        discount_elem = price_container.query_selector(SELECTORS_PRICING['discount'])
        if discount_elem:
            discount_text = discount_elem.inner_text().strip()
            discount_match = re.search(r'(\d+)%', discount_text)
            if discount_match:
                price_data['discount_percent'] = discount_match.group(1)
        
        return price_data
    
    def _extract_from_alternatives(self, page, price_data):
        """Try alternative selectors for price"""
        # Try current price
        if price_data['price'] == DEFAULT_VALUES['not_available']:
            alt_current = page.query_selector(SELECTORS_PRICING['current_price'])
            if alt_current:
                price_data['price'] = self._extract_price_number(alt_current.inner_text())
        
        # Try original price
        if price_data['original_price'] == DEFAULT_VALUES['not_available']:
            alt_original = page.query_selector(SELECTORS_PRICING['original_price'])
            if alt_original:
                price_data['original_price'] = self._extract_price_number(alt_original.inner_text())
        
        return price_data
    
    @staticmethod
    def _extract_price_number(price_text):
        """
        Extract numeric price from text
        
        Args:
            price_text: Text containing price (e.g., '$63.97')
            
        Returns:
            str: Numeric price or 'N/A'
        """
        if not price_text:
            return DEFAULT_VALUES['not_available']
        
        # Remove $ and any non-numeric characters except decimal point
        price_clean = re.sub(r'[^\d.]', '', price_text.strip())
        return price_clean if price_clean else DEFAULT_VALUES['not_available']
    
    @staticmethod
    def _calculate_discount(current_price, original_price):
        """
        Calculate discount percentage
        
        Args:
            current_price: Current price string
            original_price: Original price string
            
        Returns:
            str: Discount percentage or '0'
        """
        try:
            current_num = float(current_price)
            original_num = float(original_price)
            
            if original_num > 0 and current_num < original_num:
                discount = ((original_num - current_num) / original_num) * 100
                return str(round(discount))
        except:
            pass
        
        return DEFAULT_VALUES['no_discount']