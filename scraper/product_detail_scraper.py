"""
Product detail page scraper
Handles scraping of color variations and size availability from product pages
"""

import time
from config.constants import TIMEOUT_PRODUCT_PAGE, DELAY_PAGE_SETTLE
from scraper.color_extractor import ColorExtractor
from scraper.size_extractor import SizeExtractor
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProductDetailScraper:
    """Scrapes detailed product information from product detail pages"""
    
    def __init__(self):
        self.color_extractor = ColorExtractor()
        self.size_extractor = SizeExtractor()
    
    def scrape_product_page(self, context, base_url, main_product_id):
        """
        Scrape color variations and size availability from product page
        
        Args:
            context: Playwright browser context
            base_url: Product page URL
            main_product_id: ID of the main product
            
        Returns:
            tuple: (color_variations list, size_availability list)
        """
        color_variations = []
        size_availability = []
        
        # Create new page for this product
        page = context.new_page()
        
        try:
            # Navigate to product page
            page.goto(base_url, wait_until="domcontentloaded", timeout=TIMEOUT_PRODUCT_PAGE)
            time.sleep(DELAY_PAGE_SETTLE)
            
            # Extract color variations
            logger.info("  Extracting color variations...")
            colors = self.color_extractor.extract_colors(page, main_product_id)
            color_variations.extend(colors)
            
            # Extract size availability for first color
            if colors:
                current_color = colors[0]
                logger.info(f"  Extracting sizes for: {current_color['color_name']}")
                sizes = self.size_extractor.extract_sizes(
                    page,
                    current_color['unique_color_id'],
                    current_color['color_product_id']
                )
                size_availability.extend(sizes)
                
                # Note about additional colors
                if len(colors) > 1:
                    logger.info(f"  Note: {len(colors)-1} additional colors found (sizes from first color only)")
            
        except Exception as e:
            logger.error(f"  Error scraping product page: {e}")
        finally:
            page.close()
        
        return color_variations, size_availability