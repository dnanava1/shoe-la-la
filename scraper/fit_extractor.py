"""
Fit variation extractor
Extracts fit options (e.g., Wide, Extra Wide) and related data
from product detail pages.
"""

from config.constants import (
    SELECTORS_PRODUCT_DETAIL, DEFAULT_VALUES
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FitExtractor:
    """Extracts fit variation data from product pages"""

    async def extract_fits(self, page, main_product_id):
        """
        Extract all fit variations from product page
        
        Args:
            page: Playwright page object
            main_product_id: ID of main product
            
        Returns:
            list: Fit variation data dictionaries
        """
        fits = []
        
        try:
            # Find fit selection container
            fit_container = await page.query_selector(SELECTORS_PRODUCT_DETAIL['fit_container'])
            
            if fit_container:
                fits = await self._extract_from_container(fit_container, main_product_id, page)
            
            # If no container was found OR it was empty, create a default fit
            if not fits:
                logger.warning(f"    No fit variations detected for {main_product_id} — creating DEFAULT fit entry.")
                default_fit = await self._create_default_fit(page, main_product_id)
                fits = [default_fit]
                
        except Exception as e:
            logger.error(f"    Error extracting fits: {e}")
            fits = [await self._create_default_fit(page, main_product_id)]
        return fits
    
    async def _extract_from_container(self, fit_container, main_product_id, page):
        """Extract fits from fit picker container"""
        fits = []
        # Use the 'fit_items' selector which points to '.nds-radio'
        fit_items = await fit_container.query_selector_all(SELECTORS_PRODUCT_DETAIL['fit_items'])
        
        for fit_item in fit_items:
            try:
                fit_data = await self._extract_fit_data(fit_item, main_product_id, page)
                if fit_data:
                    fits.append(fit_data)
            except Exception as e:
                logger.error(f"    Error extracting single fit: {e}")
                continue
        
        return fits
    
    async def _extract_fit_data(self, fit_item, main_product_id, page):
        """Extract data for a single fit variation (from a radio button item)"""
        
        fit_label_element = await fit_item.query_selector(SELECTORS_PRODUCT_DETAIL['fit_label'])
        
        if not fit_label_element:
            logger.warning("    Found fit item but no label.")
            return None
            
        fit_name = await fit_label_element.inner_text()
        if not fit_name:
            fit_name = DEFAULT_VALUES['unknown_fit']
        
        # Create a product_id from the fit name (e.g., "Extra Wide" -> "EXTRA_WIDE")
        fit_product_id = fit_name.strip().upper().replace(" ", "_")
        
        fit_data = {
            'unique_fit_id': f"{main_product_id}_{fit_product_id}",
            'main_product_id': main_product_id,
            'fit_product_id': fit_product_id,
            'fit_name': fit_name.strip(),
        }
            
        return fit_data

    async def _create_default_fit(self, page, main_product_id):
        """Create a default fit entry when no fit picker exists"""
        return {
            'unique_fit_id': f"{main_product_id}_{DEFAULT_VALUES['default_fit_id']}",
            'main_product_id': main_product_id,
            'fit_product_id': DEFAULT_VALUES['default_fit_id'],
            'fit_name': DEFAULT_VALUES['default_fit_name'],
        }