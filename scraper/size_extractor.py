"""
Size availability extractor
Extracts size options, availability, and pricing information
"""

from config.constants import SELECTORS_PRODUCT_DETAIL, DEFAULT_VALUES
from scraper.pricing_extractor import PricingExtractor
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SizeExtractor:
    """Extracts size availability and related data"""
    
    def __init__(self):
        self.pricing_extractor = PricingExtractor()
    
    def extract_sizes(self, page, unique_color_id, color_product_id):
        """
        Extract all size options and their availability
        
        Args:
            page: Playwright page object
            unique_color_id: Unique ID for this color variation
            color_product_id: Color product ID
            
        Returns:
            list: Size availability data dictionaries
        """
        sizes = []
        
        try:
            
            # Find size grid
            size_grid = page.query_selector(SELECTORS_PRODUCT_DETAIL['size_grid'])
            
            if size_grid:
                size_items = size_grid.query_selector_all(SELECTORS_PRODUCT_DETAIL['size_items'])
                
                # Extract pricing once (applies to all sizes)
                pricing_data = self.pricing_extractor.extract_pricing(page)
                
                for size_item in size_items:
                    try:
                        size_data = self._extract_size_data(
                            size_item,
                            unique_color_id,
                            color_product_id,
                            pricing_data,
                        )
                        if size_data:
                            sizes.append(size_data)
                    except Exception as e:
                        logger.error(f"      Error extracting size: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"    Error extracting sizes: {e}")
        
        return sizes
    
    def _extract_size_data(self, size_item, unique_color_id, color_product_id, pricing_data):
        """Extract data for a single size option"""
        size_data = {}
        
        # Check availability
        is_disabled = 'disabled' in size_item.get_attribute('class')
        size_data['available'] = not is_disabled
        
        # Extract size label (display text)
        label = size_item.query_selector(SELECTORS_PRODUCT_DETAIL['size_label'])
        size_data['size_label'] = label.inner_text().strip() if label else DEFAULT_VALUES['not_available']
        
        # Extract size value (numeric/technical size)
        size_input = size_item.query_selector(SELECTORS_PRODUCT_DETAIL['size_input'])
        size_data['size'] = size_input.get_attribute('value') if size_input else DEFAULT_VALUES['not_available']
        
        # Create unique size ID
        size_data['unique_size_id'] = f"{unique_color_id}_{size_data['size']}"
        size_data['unique_color_id'] = unique_color_id
        size_data['color_product_id'] = color_product_id
        
        # Add pricing data
        size_data.update(pricing_data)

        
        return size_data