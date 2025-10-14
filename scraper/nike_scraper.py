"""
Main Nike Scraper class
Orchestrates the scraping process and delegates to specialized extractors
"""

import time
from playwright.sync_api import sync_playwright

from config.constants import (
    SHOES_SEARCH_URL, BROWSER_CONFIG, TIMEOUT_PAGE_LOAD,
    DELAY_PAGE_SETTLE, DELAY_BETWEEN_PRODUCTS, MAX_SCROLLS,
    PRODUCT_CARD_SELECTORS, TEST_MODE, TEST_MODE_PRODUCT_LIMIT,
    DEBUG_CONFIG
)
from scraper.browser_manager import BrowserManager
from scraper.product_extractor import ProductExtractor
from scraper.product_detail_scraper import ProductDetailScraper
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NikeScraper:
    """Main scraper class for Nike shoes"""
    
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.product_extractor = ProductExtractor()
        self.detail_scraper = ProductDetailScraper()
        
        self.main_products = []
        self.color_variations = []
        self.size_availability = []
        self.product_url_to_id = {}
    
    def scrape(self):
        """Execute the complete scraping workflow"""
        with sync_playwright() as playwright:
            browser, context = self.browser_manager.setup_browser(playwright)
            
            try:
                page = context.new_page()
                self.browser_manager.setup_page(page)
                
                # Navigate and load products
                self._navigate_to_page(page)
                product_cards = self._load_all_products(page)
                
                if not product_cards:
                    self._handle_no_products(page)
                    return [], [], []
                
                # Phase 1: Extract main products
                self._extract_main_products(product_cards)
                
                # Phase 2: Extract details for each product
                self._extract_product_details(context)
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}", exc_info=True)
                self._save_error_debug(page)
            finally:
                context.close()
                browser.close()
        
        return self.main_products, self.color_variations, self.size_availability
    
    def _navigate_to_page(self, page):
        """Navigate to Nike shoes page"""
        logger.info(f"Navigating to: {SHOES_SEARCH_URL}")
        page.goto(SHOES_SEARCH_URL, wait_until="domcontentloaded", timeout=TIMEOUT_PAGE_LOAD)
        logger.info("Page loaded, waiting for content to settle...")
        time.sleep(DELAY_PAGE_SETTLE)
    
    def _load_all_products(self, page):
        """Load all products by scrolling"""
        logger.info("Loading products...")
        
        # Wait for products to appear
        try:
            page.wait_for_selector(', '.join(PRODUCT_CARD_SELECTORS), timeout=30000)
        except:
            logger.warning("Initial product load timed out, continuing anyway...")
            time.sleep(DELAY_PAGE_SETTLE)
        
        # Scroll to load all products
        self.browser_manager.scroll_and_load(page, max_scrolls=MAX_SCROLLS)
        
        # Find product cards
        product_cards = self._find_product_cards(page)
        logger.info(f"Found {len(product_cards)} product cards")
        
        # Apply test mode limit if enabled
        if TEST_MODE and product_cards:
            product_cards = product_cards[:TEST_MODE_PRODUCT_LIMIT]
            logger.warning(f"TEST MODE: Limited to {len(product_cards)} products")
        
        return product_cards
    
    def _find_product_cards(self, page):
        """Try multiple selectors to find product cards"""
        for selector in PRODUCT_CARD_SELECTORS:
            cards = page.query_selector_all(selector)
            if cards:
                logger.info(f"Products found using selector: {selector}")
                return cards
        logger.warning("No products found with any selector")
        return []
    
    def _extract_main_products(self, product_cards):
        """Phase 1: Extract main product data from cards"""
        logger.info("\n=== PHASE 1: Extracting main product data ===")
        
        for idx, card in enumerate(product_cards, 1):
            try:
                product_data = self.product_extractor.extract_main_product(card)
                if product_data:
                    self.main_products.append(product_data)
                    self.product_url_to_id[product_data['base_url']] = product_data['main_product_id']
                    logger.info(f"[{idx}/{len(product_cards)}] Scraped: {product_data['name']}")
            except Exception as e:
                logger.error(f"Error scraping product {idx}: {e}")
                continue
        
        logger.info(f"✅ Phase 1 complete: {len(self.main_products)} main products extracted")
    
    def _extract_product_details(self, context):
        """Phase 2: Extract color variations and sizes for each product"""
        logger.info("\n=== PHASE 2: Extracting product details ===")
        logger.info(f"Visiting {len(self.main_products)} product pages...")
        
        for idx, product in enumerate(self.main_products, 1):
            try:
                logger.info(f"[{idx}/{len(self.main_products)}] Processing: {product['name']}")
                
                colors, sizes = self.detail_scraper.scrape_product_page(
                    context,
                    product['base_url'],
                    product['main_product_id']
                )
                
                self.color_variations.extend(colors)
                self.size_availability.extend(sizes)
                
                logger.info(f"  → Found {len(colors)} colors, {len(sizes)} size entries")
                
                # Delay between product pages
                time.sleep(DELAY_BETWEEN_PRODUCTS)
                
            except Exception as e:
                logger.error(f"Error processing {product['name']}: {e}")
                continue
        
        logger.info(f"✅ Phase 2 complete: {len(self.color_variations)} colors, {len(self.size_availability)} sizes")
    
    def _handle_no_products(self, page):
        """Handle case where no products are found"""
        logger.error("No products found!")
        
        if DEBUG_CONFIG['screenshot_on_error']:
            page.screenshot(path=DEBUG_CONFIG['debug_screenshot_name'])
            logger.info(f"Screenshot saved: {DEBUG_CONFIG['debug_screenshot_name']}")
        
        if DEBUG_CONFIG['save_page_html']:
            with open(DEBUG_CONFIG['debug_html_name'], 'w', encoding='utf-8') as f:
                f.write(page.content())
            logger.info(f"Page HTML saved: {DEBUG_CONFIG['debug_html_name']}")
    
    def _save_error_debug(self, page):
        """Save debugging information on error"""
        if DEBUG_CONFIG['screenshot_on_error']:
            try:
                page.screenshot(path=DEBUG_CONFIG['error_screenshot_name'])
                logger.info(f"Error screenshot saved: {DEBUG_CONFIG['error_screenshot_name']}")
            except:
                pass