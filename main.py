"""
Nike Shoes Scraper - Main Entry Point
Orchestrates the scraping workflow and coordinates between modules
"""

import time
from datetime import datetime

from scraper.nike_scraper import NikeScraper
from utils.logger import setup_logger
from utils.file_manager import FileManager

logger = setup_logger(__name__)


def main():
    """Main execution flow"""
    start_time = time.time()
    
    # Print header
    print("=" * 60)
    print("Nike Shoes Scraper - Professional Edition")
    print("=" * 60)
    print()
    
    try:
        # Initialize scraper
        logger.info("Initializing Nike scraper...")
        scraper = NikeScraper()
        
        # Execute scraping workflow
        logger.info("Starting scraping process...")
        main_products, color_variations, size_availability = scraper.scrape()
        
        # Save results
        if main_products:
            logger.info("Saving scraped data...")
            file_manager = FileManager()
            output_dir = file_manager.save_all_data(
                main_products, 
                color_variations, 
                size_availability,
                start_time
            )
            
            # Print summary
            print_summary(main_products, color_variations, size_availability, output_dir)
        else:
            logger.warning("No data collected. Scraping may have failed.")
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during scraping: {e}", exc_info=True)
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Total execution time: {format_duration(duration)}")
    
    print("\n" + "=" * 60)
    print("Scraping completed!")
    print("=" * 60)


def print_summary(main_products, color_variations, size_availability, output_dir):
    """Print scraping summary"""
    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)
    print(f"✅ Main Products:       {len(main_products):>6}")
    print(f"✅ Color Variations:    {len(color_variations):>6}")
    print(f"✅ Size Entries:        {len(size_availability):>6}")
    print(f"\n📁 Output Directory: {output_dir}")
    print("=" * 60)


def format_duration(seconds):
    """Format duration in human-readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"


if __name__ == "__main__":
    main()