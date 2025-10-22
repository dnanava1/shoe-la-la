"""
Configuration and constants for Nike scraper
Centralizes all configurable values and selectors
"""

# ============================================================================
# SCRAPING CONFIGURATION
# ============================================================================

# Target URL
BASE_URL = "https://www.nike.com"
SHOES_SEARCH_URL = f"{BASE_URL}/w?q=shoes&vst=shoes"

# Browser settings
BROWSER_CONFIG = {
    'headless': True,
    'viewport': {'width': 1920, 'height': 1080},
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'args': [
        '--disable-blink-features=AutomationControlled',
        '--no-sandbox',
        '--disable-dev-shm-usage'
    ]
}

# Timeout settings (in milliseconds)
TIMEOUT_PAGE_LOAD = 90000
TIMEOUT_ELEMENT_WAIT = 30000
TIMEOUT_PRODUCT_PAGE = 60000

# Delay settings (in seconds)
DELAY_PAGE_SETTLE = 5
DELAY_SCROLL = 3
DELAY_BETWEEN_PRODUCTS = 2
DELAY_SCROLL_BATCH = 5

# Scrolling configuration
MAX_SCROLLS = 200
SCROLL_PAUSE_INTERVAL = 20
NO_NEW_PRODUCTS_THRESHOLD = 5

# ============================================================================
# CSS SELECTORS
# ============================================================================

# Product card selectors (in order of preference)
PRODUCT_CARD_SELECTORS = [
    'figure',
    '.product-card',
    '[data-testid="product-card"]'
]

# Main product selectors
SELECTORS_MAIN_PRODUCT = {
    'title': '.product-card__title',
    'subtitle': '.product-card__subtitle',
    'link': 'a.product-card__link-overlay',
    'messaging': '[data-testid="product-card__messaging"]'
}

# Product detail page selectors
SELECTORS_PRODUCT_DETAIL = {
    'color_container': '#colorway-picker-container, [data-testid="colorway-picker-container"]',
    'color_links': 'a[data-testid^="colorway-link-"]',
    'color_image': 'img',
    'size_grid': '[data-testid="pdp-grid-selector-grid"]',
    'size_items': '[data-testid="pdp-grid-selector-item"]',
    'size_label': 'label',
    'size_input': 'input'
}

# Pricing selectors
SELECTORS_PRICING = {
    'price_container': '#price-container, [data-testid="price-container"]',
    'current_price': '[data-testid="currentPrice-container"]',
    'original_price': '[data-testid="initialPrice-container"]',
    'discount': '[data-testid="OfferPercentage"]'
}

# ============================================================================
# CSV CONFIGURATION
# ============================================================================

# CSV headers for each table
CSV_HEADERS = {
    'main_products': [
        'main_product_id',
        'name',
        'category',
        'base_url',
        'tag'
    ],
    'color_variations': [
        'unique_color_id',
        'main_product_id',
        'color_product_id',
        'color_name',
        'color_image_url',
        'color_url',
        'style',
        'shown',
    ],
    'size_availability': [
        'unique_size_id',
        'unique_color_id',
        'color_product_id',
        'main_product_id',
        'color_name',
        'size',
        'size_label',
        'available',
        'price',
        'original_price',
        'discount_percent',
    ]
}

# CSV filenames
CSV_FILENAMES = {
    'main_products': 'nike_main_products.csv',
    'color_variations': 'nike_color_variations.csv',
    'size_availability': 'nike_size_availability.csv'
}

# Output directory prefix
OUTPUT_DIR_PREFIX = 'nike_shoes'

# ============================================================================
# DEFAULT VALUES
# ============================================================================

DEFAULT_VALUES = {
    'not_available': 'N/A',
    'unknown_color': 'Unknown Color',
    'default_color_id': 'DEFAULT',
    'default_color_name': 'Default Color',
    'no_discount': '0'
}

# ============================================================================
# DEBUGGING
# ============================================================================

DEBUG_CONFIG = {
    'screenshot_on_error': True,
    'save_page_html': True,
    'error_screenshot_name': 'error_screenshot.png',
    'debug_screenshot_name': 'debug_screenshot.png',
    'debug_html_name': 'debug_page.html'
}

# Test mode (set to True to limit scraping for testing)
TEST_MODE = True
TEST_MODE_PRODUCT_LIMIT = 10

# ============================================================================
# HISTORICAL TRACKING CONFIGURATION
# ============================================================================

# Maximum number of concurrent product page requests
MAX_CONCURRENT_REQUESTS = 15

# Historical data file location
HISTORICAL_FILE_PATH = 'historical_size_availability.csv'

# Static columns that don't change (used as keys/metadata)
HISTORICAL_STATIC_COLUMNS = [
    'unique_size_id',
    'unique_color_id',
    'color_product_id',
    'size',
    'size_label'
]

# Columns to track over time (will have timestamp prefix)
HISTORICAL_TRACKED_COLUMNS = [
    'available',
    'price',
    'original_price',
    'discount_percent'
]

# All columns for historical file
HISTORICAL_ALL_COLUMNS = (
    HISTORICAL_STATIC_COLUMNS +
    ['timestamp'] +
    HISTORICAL_TRACKED_COLUMNS +
    ['change_type']
)