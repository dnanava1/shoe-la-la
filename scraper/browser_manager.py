"""
Browser management and scrolling utilities
Handles browser setup, page configuration, and lazy loading
"""

import asyncio
from config.constants import (
    BROWSER_CONFIG, DELAY_SCROLL, SCROLL_PAUSE_INTERVAL,
    NO_NEW_PRODUCTS_THRESHOLD, TEST_MODE, TEST_MODE_PRODUCT_LIMIT,
    PRODUCT_CARD_SELECTORS  # Import test mode and selector constants
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BrowserManager:
    """Manages browser setup and page interactions"""
    
    async def setup_browser(self, playwright):
        """Initialize browser and context with anti-detection settings"""
        logger.info("Launching browser...")
        
        browser = await playwright.chromium.launch(
            headless=BROWSER_CONFIG['headless'],
            args=BROWSER_CONFIG['args']
        )
        
        context = await browser.new_context(
            viewport=BROWSER_CONFIG['viewport'],
            user_agent=BROWSER_CONFIG['user_agent']
        )
        
        return browser, context
    
    async def setup_page(self, page):
        """Configure page with anti-detection scripts"""
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    async def _get_current_product_count(self, page):
        """
        Helper to count products using the official selector list from constants.
        """
        for selector in PRODUCT_CARD_SELECTORS:
            count = len(await page.query_selector_all(selector))
            if count > 0:
                return count  # Return count from first successful selector
        return 0  # No products found with any selector

    async def scroll_and_load(self, page, max_scrolls):
        """
        Scroll page to trigger lazy loading of products.
        If TEST_MODE is True, stops after loading TEST_MODE_PRODUCT_LIMIT items.
        
        Args:
            page: Playwright page object
            max_scrolls: Maximum number of scroll attempts
        """
        logger.info(f"Starting scroll process (max {max_scrolls} scrolls)...")
        if TEST_MODE:
            logger.warning(
                f"--- ⚠️ TEST_MODE ENABLED --- "
                f"Will stop after loading ~{TEST_MODE_PRODUCT_LIMIT} products."
            )
        
        scrolls = 0
        last_product_count = 0
        no_new_products_count = 0
        
        while scrolls < max_scrolls:
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(DELAY_SCROLL)
            
            # Check for new products using the robust helper method
            new_product_count = await self._get_current_product_count(page)
            
            if new_product_count > last_product_count:
                # New products loaded
                newly_loaded = new_product_count - last_product_count
                logger.info(f"Scroll {scrolls + 1}: +{newly_loaded} products (Total: {new_product_count})")
                last_product_count = new_product_count
                no_new_products_count = 0

                # *** TEST MODE CHECK ***
                # If test mode is on and we've loaded enough products, stop.
                if TEST_MODE and new_product_count >= TEST_MODE_PRODUCT_LIMIT:
                    logger.warning(
                        f"--- TEST_MODE: Reached product limit "
                        f"({new_product_count} >= {TEST_MODE_PRODUCT_LIMIT}). "
                        "Stopping scroll. ---"
                    )
                    break  # Exit the while loop
                
            else:
                # No new products
                no_new_products_count += 1
                logger.info(f"Scroll {scrolls + 1}: No new products ({no_new_products_count}/{NO_NEW_PRODUCTS_THRESHOLD})")
                
                # Stop if no new products after threshold
                if no_new_products_count >= NO_NEW_PRODUCTS_THRESHOLD:
                    logger.info(f"✓ Scroll complete after {scrolls + 1} attempts (no new products).")
                    break
            
            scrolls += 1
            
            # Periodic pause to let page catch up
            if scrolls % SCROLL_PAUSE_INTERVAL == 0:
                logger.info("--- Pausing to let page stabilize ---")
                await asyncio.sleep(5)
        
        final_count = await self._get_current_product_count(page)
        
        if scrolls >= max_scrolls:
             logger.info(f"✓ Scrolling finished: Reached max {max_scrolls} scrolls.")
        
        logger.info(f"✓ Scrolling finalized: {final_count} total products found.")
        
        return final_count