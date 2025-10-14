"""
Browser management and scrolling utilities
Handles browser setup, page configuration, and lazy loading
"""

import time
from config.constants import (
    BROWSER_CONFIG, DELAY_SCROLL, SCROLL_PAUSE_INTERVAL,
    NO_NEW_PRODUCTS_THRESHOLD
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BrowserManager:
    """Manages browser setup and page interactions"""
    
    def setup_browser(self, playwright):
        """Initialize browser and context with anti-detection settings"""
        logger.info("Launching browser...")
        
        browser = playwright.chromium.launch(
            headless=BROWSER_CONFIG['headless'],
            args=BROWSER_CONFIG['args']
        )
        
        context = browser.new_context(
            viewport=BROWSER_CONFIG['viewport'],
            user_agent=BROWSER_CONFIG['user_agent']
        )
        
        return browser, context
    
    def setup_page(self, page):
        """Configure page with anti-detection scripts"""
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
    
    def scroll_and_load(self, page, max_scrolls):
        """
        Scroll page to trigger lazy loading of products
        
        Args:
            page: Playwright page object
            max_scrolls: Maximum number of scroll attempts
        """
        logger.info(f"Starting scroll process (max {max_scrolls} scrolls)...")
        
        scrolls = 0
        last_product_count = 0
        no_new_products_count = 0
        
        while scrolls < max_scrolls:
            # Get current product count
            current_products = len(page.query_selector_all('figure'))
            
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(DELAY_SCROLL)
            
            # Check for new products
            new_product_count = len(page.query_selector_all('figure'))
            
            if new_product_count > last_product_count:
                # New products loaded
                newly_loaded = new_product_count - last_product_count
                logger.info(f"Scroll {scrolls + 1}: +{newly_loaded} products (Total: {new_product_count})")
                last_product_count = new_product_count
                no_new_products_count = 0
            else:
                # No new products
                no_new_products_count += 1
                logger.info(f"Scroll {scrolls + 1}: No new products ({no_new_products_count}/{NO_NEW_PRODUCTS_THRESHOLD})")
                
                # Stop if no new products after threshold
                if no_new_products_count >= NO_NEW_PRODUCTS_THRESHOLD:
                    logger.info(f"✓ Scroll complete after {scrolls + 1} attempts")
                    break
            
            scrolls += 1
            
            # Periodic pause to let page catch up
            if scrolls % SCROLL_PAUSE_INTERVAL == 0:
                logger.info("--- Pausing to let page stabilize ---")
                time.sleep(5)
        
        final_count = len(page.query_selector_all('figure'))
        logger.info(f"✓ Scrolling finished: {final_count} total products")
        
        return final_count