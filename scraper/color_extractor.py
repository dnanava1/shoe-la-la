"""
Color variation extractor
Extracts color options and related data from product detail pages
"""

from config.constants import (
    SELECTORS_PRODUCT_DETAIL, BASE_URL, DEFAULT_VALUES
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ColorExtractor:
    """Extracts color variation data from product pages"""
    
    async def extract_colors(self, page, main_product_id):
        """
        Extract all color variations from product page
        
        Args:
            page: Playwright page object
            main_product_id: ID of main product
            
        Returns:
            list: Color variation data dictionaries
        """
        colors = []
        
        try:
            # Find color selection container
            color_container = await page.query_selector(SELECTORS_PRODUCT_DETAIL['color_container'])
            
            if color_container:
                colors = await self._extract_from_container(color_container, main_product_id, page)
            if not colors:
                logger.warning("    No color variations detected — creating DEFAULT color entry.")
                default_color = await self._create_default_color(page, main_product_id)
                colors = [default_color]
#             else:
#                 # No color picker found - create default single color
#                 colors = [await self._create_default_color(page, main_product_id)]
                
        except Exception as e:
            logger.error(f"    Error extracting colors: {e}")
            colors = [await self._create_default_color(page, main_product_id)]
        return colors
    
    async def _extract_from_container(self, color_container, main_product_id, page):
        """Extract colors from color picker container"""
        colors = []
        color_links = await color_container.query_selector_all(SELECTORS_PRODUCT_DETAIL['color_links'])
        
        for color_link in color_links:
            try:
                color_data = await self._extract_color_data(color_link, main_product_id, page)
                if color_data:
                    colors.append(color_data)
            except Exception as e:
                logger.error(f"    Error extracting single color: {e}")
                continue
        
        return colors
    
    async def _extract_color_data(self, color_link, main_product_id, page):
        """Extract data for a single color variation"""
        # Get color product ID from data-testid
        testid = await color_link.get_attribute('data-testid')
        color_product_id = testid.replace('colorway-link-', '') if testid else "UNKNOWN"
        
        color_data = {
            'unique_color_id': f"{main_product_id}_{color_product_id}",
            'main_product_id': main_product_id,
            'color_product_id': color_product_id
        }
        
        # Extract color name and image from img element
        color_img = await color_link.query_selector(SELECTORS_PRODUCT_DETAIL['color_image'])
        if color_img:
            color_data['color_name'] = await color_img.get_attribute('alt') or DEFAULT_VALUES['unknown_color']
            color_data['color_image_url'] = await color_img.get_attribute('src') or ""
        else:
            color_data['color_name'] = DEFAULT_VALUES['unknown_color']
            color_data['color_image_url'] = ""
        
        # Extract color URL
        color_href = await color_link.get_attribute('href')
        if color_href:
            color_data['color_url'] = f"{BASE_URL}{color_href}" if color_href.startswith('/') else color_href
        else:
            color_data['color_url'] = ""

        shown, style = await self._extract_shown_and_style(page)
        color_data["shown"] = shown or "N/A"
        color_data["style"] = style or "N/A"
        color_data.update({"shown": shown or "N/A", "style": style or "N/A"})
        return color_data

    async def _extract_shown_and_style(self, page):
        """Extract 'Shown' and 'Style' details if available"""

        async def safe_text(selector, label):
            elem = await page.query_selector(selector)
            if not elem:
                return None
            text = await elem.inner_text()   # ✅ added await
            text = text.replace(label, "").strip()
            return text or None

        shown = await safe_text('li[data-testid="product-description-color-description"]', "Shown:")  # ✅ added await
        style = await safe_text('li[data-testid="product-description-style-color"]', "Style:")        # ✅ added await

        return shown, style


    
    async def _create_default_color(self, page, main_product_id):
        """Create a default color entry when no color picker exists"""
        shown, style = await self._extract_shown_and_style(page)
        return {
            'unique_color_id': f"{main_product_id}_{DEFAULT_VALUES['default_color_id']}",
            'main_product_id': main_product_id,
            'color_product_id': DEFAULT_VALUES['default_color_id'],
            'color_name': DEFAULT_VALUES['default_color_name'],
            'color_image_url': "",
            'color_url': page.url,
            'shown': shown,
            'style': style,
        }