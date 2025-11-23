"""
Product detail page scraper
Handles scraping of fit, color variations, and size availability from product pages
"""

import asyncio
from config.constants import (
    TIMEOUT_PRODUCT_PAGE,
    DELAY_PAGE_SETTLE,
    SELECTORS_PRODUCT_DETAIL,
    TIMEOUT_ELEMENT_WAIT,
    DEFAULT_VALUES,
)
from scraper.fit_extractor import FitExtractor
from scraper.color_extractor import ColorExtractor
from scraper.size_extractor import SizeExtractor
from scraper.pricing_extractor import PricingExtractor
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProductDetailScraper:
    """Scrapes detailed product information from product detail pages"""

    def __init__(self):
        self.fit_extractor = FitExtractor()
        self.color_extractor = ColorExtractor()
        self.size_extractor = SizeExtractor()
        self.pricing_extractor = PricingExtractor()

    async def scrape_product_page(self, context, base_url, main_product_id):
        """
        Scrape fit, color variations, and size availability from product page

        Args:
            context: Playwright browser context
            base_url: Product page URL
            main_product_id: ID of the main product

        Returns:
            tuple: (fit_variations list, color_variations list, size_availability list)
        """
        fit_variations = []
        color_variations = []
        size_availability = []

        # Open new tab for this product
        page = await context.new_page()

        try:
            # Navigate to product page
            logger.info(f" Visiting product page: {base_url}")
            await page.goto(base_url, wait_until="domcontentloaded", timeout=TIMEOUT_PRODUCT_PAGE)
            await asyncio.sleep(DELAY_PAGE_SETTLE)

            # === 1. Extract Fit Variations ===
            logger.info("  Extracting fit variations...")
            fits = await self.fit_extractor.extract_fits(page, main_product_id)
            fit_variations.extend(fits)
            logger.info(f"  Found {len(fits)} fit variations.")

            # === 2. Iterate through each Fit ===
            for fit in fits:
                unique_fit_id = fit.get("unique_fit_id")
                fit_name = fit.get("fit_name")
                fit_pid = fit.get("fit_product_id")

                try:
                    logger.info(f"  Processing fit: {fit_name} ({fit_pid})")

                    # --- 2a. Select the fit on the page (if not default) ---
                    if fit_pid != DEFAULT_VALUES['default_fit_id']:
                        logger.info(f"    Selecting fit: {fit_name}")
                        fit_container = await page.query_selector(SELECTORS_PRODUCT_DETAIL['fit_container'])
                        clicked = False
                        if fit_container:
                            fit_items = await fit_container.query_selector_all(SELECTORS_PRODUCT_DETAIL['fit_items'])
                            for item in fit_items:
                                label_elem = await item.query_selector(SELECTORS_PRODUCT_DETAIL['fit_label'])
                                if label_elem and (await label_elem.inner_text()).strip() == fit_name:
                                    await label_elem.click()
                                    await asyncio.sleep(DELAY_PAGE_SETTLE)
                                    clicked = True
                                    break
                        if not clicked:
                            logger.warning(f"    Could not find or click fit: {fit_name}")
                    
                    # === 3. Extract Color Variations (for this fit) ===
                    logger.info("    Extracting color variations...")
                    colors = await self.color_extractor.extract_colors(page, main_product_id, unique_fit_id)
                    color_variations.extend(colors)
                    logger.info(f"    Found {len(colors)} color variations for this fit.")

                    # === 4. Iterate through each Color (for this fit) ===
                    for color in colors:
                        color_name = color.get("color_name")
                        color_pid = color.get("color_product_id")
                        color_url = color.get("color_url")

                        try:
                            logger.info(f"      Processing color: {color_name} ({color_pid})")

                            # Navigate to color page if URL exists
                            if color_url and color_url != page.url:
                                await page.goto(color_url, wait_until="domcontentloaded", timeout=TIMEOUT_PRODUCT_PAGE)
                                await asyncio.sleep(DELAY_PAGE_SETTLE)

                            # Extract 'shown' + 'style' dynamically from this page
                            shown, style = await self.color_extractor._extract_shown_and_style(page)
                            color["shown"] = shown or "N/A"
                            color["style"] = style or "N/A"

                            # Wait for size grid
                            await page.wait_for_selector(SELECTORS_PRODUCT_DETAIL["size_grid"], timeout=TIMEOUT_ELEMENT_WAIT)

                            # Extract pricing (color-specific if applicable)
                            pricing_data = await self.pricing_extractor.extract_pricing(page)

                            # === 5. Extract Sizes (for this color/fit) ===
                            sizes = await self.size_extractor.extract_sizes(
                                page,
                                color.get("unique_color_id"),
                                color_pid,
                            )

                            # Merge pricing + color/fit info into each size record
                            for s in sizes:
                                s.update(pricing_data)
                                s["color_name"] = color_name
                                s["fit_name"] = fit_name
                                s["unique_fit_id"] = unique_fit_id
                                s["main_product_id"] = main_product_id

                            size_availability.extend(sizes)

                        except Exception as e:
                            logger.error(f"      Error extracting sizes for color {color_pid}: {e}")
                            continue

                except Exception as e:
                    logger.error(f"    Error processing fit {fit_pid}: {e}")
                    continue

            logger.info(f"✅ Completed product {main_product_id}: {len(size_availability)} total size entries.")

        except Exception as e:
            logger.error(f"  Error scraping product page: {e}")

        finally:
            await page.close()

        return fit_variations, color_variations, size_availability
