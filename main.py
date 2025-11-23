"""
Nike Shoes Scraper - Main Entry Point (RDS version)
Handles scraping workflow and directly saves results to AWS RDS
"""

import time
import asyncio
from datetime import datetime

from scraper.nike_scraper import NikeScraper
from utils.logger import setup_logger
from utils.database_manager import DatabaseManager
from utils.historical_tracker import HistoricalTracker

logger = setup_logger(__name__)


async def main():
    """Main execution flow"""
    start_time = time.time()
    print("=" * 60)
    print("Nike Shoes Scraper - AWS RDS Edition")
    print("=" * 60)
    print()

    try:
        # Initialize scraper
        logger.info("Initializing Nike scraper...")
        scraper = NikeScraper()

        # Execute scraping workflow
        logger.info("Starting scraping process...")
        main_products, fit_variants, color_variants, size_variants = await scraper.scrape()

        if main_products:
            # Initialize DB connection
            logger.info("Connecting to AWS RDS...")
            db_manager = DatabaseManager()

            # Save scraped data to RDS (✅ updated to call separate functions)
            logger.info("Saving scraped data to AWS RDS tables...")
            db_manager.save_main_products(main_products)
            db_manager.save_fit_variants(fit_variants)
            db_manager.save_color_variants(color_variants)
            db_manager.save_size_variants(size_variants)

            # Update historical tracking in RDS
            logger.info("Updating historical data in RDS...")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            historical_tracker = HistoricalTracker(db_manager)
            historical_tracker.update_historical_data(size_variants, timestamp)

            # Print summary
            print_summary(main_products, fit_variants, color_variants, size_variants)
            print_historical_stats(historical_tracker)

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
    print("Scraping completed and synced to RDS!")
    print("=" * 60)


# ------------------------------------------------------------------------
# Summary / Stats Printers
# ------------------------------------------------------------------------

def print_summary(main_products, fit_variants, color_variants, size_variants):
    """Print scraping summary"""
    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)
    print(f"✅ Main Products:       {len(main_products):>6}")
    print(f"✅ Fit Variants:        {len(fit_variants):>6}")
    print(f"✅ Color Variants:      {len(color_variants):>6}")
    print(f"✅ Size Entries:        {len(size_variants):>6}")
    print("=" * 60)


def print_historical_stats(historical_tracker):
    """Print historical data statistics from RDS"""
    stats = historical_tracker.get_statistics()

    if stats and stats.get('exists'):
        print("\n" + "=" * 60)
        print("HISTORICAL TRACKING (RDS)")
        print("=" * 60)
        print(f"📊 Total Records:       {stats['total_records']:>6}")
        print(f"🔢 Unique Products:     {stats['unique_products']:>6}")
        print(f"🔄 Scraping Runs:       {stats['scraping_runs']:>6}")
        print(f"📈 Initial Records:     {stats['initial_records']:>6}")
        print(f"📉 Change Records:      {stats['change_records']:>6}")

        if stats.get('change_counts'):
            print(f"\nChange Types:")
            for change_type, count in sorted(stats['change_counts'].items()):
                print(f"   {change_type:25s} {count:>6}")

        print(f"\n📅 Latest Run:          {stats['timestamps'][-1] if stats['timestamps'] else 'N/A'}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("HISTORICAL TRACKING (RDS)")
        print("=" * 60)
        print("📊 First run - historical tracking initialized")
        print("=" * 60)


def format_duration(seconds):
    """Format duration in human-readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"


if __name__ == "__main__":
    asyncio.run(main())
