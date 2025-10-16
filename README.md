# Nike Shoes Scraper

A professional, modular web scraper for extracting Nike shoes data including product information, color variations, sizes, and pricing.

## Project Structure

```
nike-scraper/
│
├── main.py                          # Main entry point
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
│
├── config/
│   ├── __init__.py
│   └── constants.py                # All configuration and constants
│
├── scraper/
│   ├── __init__.py
│   ├── nike_scraper.py            # Main scraper orchestration
│   ├── browser_manager.py         # Browser setup and scrolling
│   ├── product_extractor.py       # Extract main product data
│   ├── product_detail_scraper.py  # Product page scraping
│   ├── color_extractor.py         # Color variation extraction
│   ├── size_extractor.py          # Size availability extraction
│   ├── pricing_extractor.py       # Price and discount extraction
│
└── utils/
    ├── __init__.py
    ├── file_manager.py             # CSV file operations
    └── logger.py                   # Logging configuration
```

## Features

- **Modular Architecture**: Easy to extend and maintain
- **Three-Table Data Model**: 
  - Main Products
  - Color Variations
  - Size Availability
- **Comprehensive Data Extraction**:
  - Product names and categories
  - Multiple color options per product
  - Size availability for each color
  - Current and original pricing
  - Discount percentages
- **Robust Scraping**:
  - Handles lazy loading with intelligent scrolling
  - Anti-detection browser configuration
  - Error handling and logging
  - Debug screenshots on failure

## Installation

1. **Clone the repository** (or create the directory structure)

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**:
```bash
playwright install chromium
```

## Usage

Run the scraper:
```bash
python main.py
```

The scraper will:
1. Launch a browser and navigate to Nike's shoes page
2. Scroll to load all products
3. Extract main product information
4. Visit each product page to get colors and sizes
5. Save data to CSV files in a timestamped directory

## Output

The scraper creates a directory named `nike_shoes_YYYYMMDD_HHMMSS/` containing:

- `nike_main_products.csv` - Main product information
- `nike_color_variations.csv` - Color options for each product
- `nike_size_availability.csv` - Size availability and pricing
- `time_log_YYYYMMDD_HHMMSS.txt` - Scraping statistics and duration

## Configuration

All configuration is centralized in `config/constants.py`:

- **URLs**: Target website URLs
- **Browser Settings**: Viewport, user agent, arguments
- **Timeouts**: Page load and element wait times
- **Delays**: Pause durations between actions
- **Selectors**: CSS selectors for elements
- **CSV Headers**: Column definitions for output files
- **Test Mode**: Limit scraping for testing

### Test Mode

To test with limited products, edit `config/constants.py`:
```python
TEST_MODE = True
TEST_MODE_PRODUCT_LIMIT = 5  # Only scrape 5 products
```

## Extending the Scraper

### Adding New Data Fields

1. **Add selector** to `config/constants.py`
2. **Create/modify extractor** in `scraper/` directory
3. **Update CSV headers** in `config/constants.py`
4. **Update data collection** in appropriate scraper class

## Logging

The scraper uses Python's logging module. Logs are output to console with timestamps and module names. Adjust log level in `utils/logger.py`:

```python
logger = setup_logger(__name__, level=logging.DEBUG)  # For verbose output
```

## Error Handling

- Errors are logged with full context
- Screenshots saved on failures (`error_screenshot.png`, `debug_screenshot.png`)
- Page HTML saved for debugging (`debug_page.html`)
- Scraper continues on individual product errors

## Best Practices

1. **Respect Website**: Add appropriate delays between requests
2. **Monitor**: Watch logs for errors and adjust selectors if needed
3. **Test First**: Use TEST_MODE before full scraping
4. **Backup Data**: Save output directories before re-running

## Troubleshooting

### No products found
- Check if Nike's page structure changed
- Review debug screenshots and HTML
- Update selectors in `config/constants.py`

### Browser won't start
- Ensure Playwright browsers are installed: `playwright install`
- Try running with `headless=True` in `config/constants.py`

### Timeouts
- Increase timeout values in `config/constants.py`
- Check internet connection
- Verify target website is accessible

## License

This project is for educational purposes only. Please review Nike's Terms of Service and robots.txt before scraping.

## Contributing

1. Create feature branches for new functionality
2. Follow existing code style and structure
3. Add appropriate logging
4. Update constants.py for new configuration
5. Document changes in README.md