"""
Product detail page scraper
Handles scraping of color variations and size availability from product pages
"""

import asyncio
from config.constants import (
    TIMEOUT_PRODUCT_PAGE,
    DELAY_PAGE_SETTLE,
    SELECTORS_PRODUCT_DETAIL,
    TIMEOUT_ELEMENT_WAIT,
)
from scraper.color_extractor import ColorExtractor
from scraper.size_extractor import SizeExtractor
from scraper.pricing_extractor import PricingExtractor
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProductDetailScraper:
    """Scrapes detailed product information from product detail pages"""

    def __init__(self):
        self.color_extractor = ColorExtractor()
        self.size_extractor = SizeExtractor()
        self.pricing_extractor = PricingExtractor()

    async def scrape_product_page(self, context, base_url, main_product_id):
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

        # Open new tab for this product
        page = await context.new_page()

        try:
            # Navigate to product page
            logger.info(f" Visiting product page: {base_url}")
            await page.goto(base_url, wait_until="domcontentloaded", timeout=TIMEOUT_PRODUCT_PAGE)
            await asyncio.sleep(DELAY_PAGE_SETTLE)

            # Extract color variations (includes shown + style now)
            logger.info("  Extracting color variations...")
            colors = await self.color_extractor.extract_colors(page, main_product_id)
            color_variations.extend(colors)

            # If no colors found, we still process DEFAULT one
            if not colors:
                logger.warning("  No color picker found — using DEFAULT color entry.")
            else:
                logger.info(f"  Found {len(colors)} color variations.")


            # Iterate through each color and extract its sizes
            for color in colors:
                color_name = color.get("color_name")
                color_pid = color.get("color_product_id")
                color_url = color.get("color_url")

                try:
                    logger.info(f"  Processing color: {color_name} ({color_pid})")

                    # Navigate to color page if URL exists, else stay on same PDP
                    if color_url:
                        await page.goto(color_url, wait_until="domcontentloaded", timeout=TIMEOUT_PRODUCT_PAGE)
                    await asyncio.sleep(DELAY_PAGE_SETTLE)

                    # Extract shown + style dynamically from this page
                    shown, style = await self.color_extractor._extract_shown_and_style(page)
                    color["shown"] = shown or "N/A"
                    color["style"] = style or "N/A"

                    # Wait for size grid
                    await page.wait_for_selector(SELECTORS_PRODUCT_DETAIL["size_grid"], timeout=TIMEOUT_ELEMENT_WAIT)

                    # Extract pricing (color-specific if applicable)
                    pricing_data = await self.pricing_extractor.extract_pricing(page)

                    # Extract sizes for this color
                    sizes = await self.size_extractor.extract_sizes(
                        page,
                        color.get("unique_color_id"),
                        color_pid,
                    )

                    # Merge pricing + color info into each size record
                    for s in sizes:
                        s.update(pricing_data)
                        s["color_name"] = color_name
                        s["color_product_id"] = color_pid
                        s["main_product_id"] = main_product_id

                    size_availability.extend(sizes)

                except Exception as e:
                    logger.error(f"  Error extracting sizes for color {color_pid}: {e}")
                    continue

            logger.info(f"✅ Completed product {main_product_id}: {len(size_availability)} total size entries.")

        except Exception as e:
            logger.error(f"  Error scraping product page: {e}")

        finally:
            await page.close()

        return color_variations, size_availability