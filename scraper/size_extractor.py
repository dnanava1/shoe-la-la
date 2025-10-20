"""
Size availability extractor
Extracts size options, availability, and pricing information
"""

from config.constants import SELECTORS_PRODUCT_DETAIL, DEFAULT_VALUES
from scraper.pricing_extractor import PricingExtractor
from utils.logger import setup_logger
import asyncio

logger = setup_logger(__name__)


class SizeExtractor:
    """Extracts size availability and related data"""
    
    def __init__(self):
        self.pricing_extractor = PricingExtractor()
    
    async def extract_sizes(self, page, unique_color_id, color_product_id):
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
            size_grid = await page.query_selector(SELECTORS_PRODUCT_DETAIL['size_grid'])
            
            if size_grid:
                size_items = await size_grid.query_selector_all(SELECTORS_PRODUCT_DETAIL['size_items'])
                
                # Extract pricing once (applies to all sizes)
                pricing_data = await self.pricing_extractor.extract_pricing(page)
                
                for size_item in size_items:
                    try:
                        size_data = await self._extract_size_data(
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
    
    async def _extract_size_data(self, size_item, unique_color_id, color_product_id, pricing_data):
        """Extract data for a single size option"""
        size_data = {}
        
        # Check availability
        item_class = await size_item.get_attribute('class')
        is_disabled = 'disabled' in item_class if item_class else False
        size_data['available'] = not is_disabled
        
        # Extract size label (display text)
        label = await size_item.query_selector(SELECTORS_PRODUCT_DETAIL['size_label'])
        if label:
            size_data['size_label'] = (await label.inner_text()).strip()
        else:
            size_data['size_label'] = DEFAULT_VALUES['not_available']

        # Extract size value (numeric/technical size)
        size_input = await size_item.query_selector(SELECTORS_PRODUCT_DETAIL['size_input'])
        if size_input:
            size_data['size'] = await size_input.get_attribute('value')
        else:
            size_data['size'] = DEFAULT_VALUES['not_available']

        # Create unique size ID
        size_data['unique_size_id'] = f"{unique_color_id}_{size_data['size']}"
        size_data['unique_color_id'] = unique_color_id
        size_data['color_product_id'] = color_product_id
        
        # Add pricing data
        size_data.update(pricing_data)

        
        return size_data