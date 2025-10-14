"""
File management utilities
Handles saving scraped data to CSV files and creating time logs
"""

import os
import csv
import time
from datetime import datetime
from config.constants import CSV_HEADERS, CSV_FILENAMES, OUTPUT_DIR_PREFIX
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FileManager:
    """Manages file operations for scraped data"""
    
    def save_all_data(self, main_products, color_variations, size_availability, start_time):
        """
        Save all scraped data to CSV files
        
        Args:
            main_products: List of main product data
            color_variations: List of color variation data
            size_availability: List of size availability data
            start_time: Timestamp when scraping started
            
        Returns:
            str: Output directory path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"{OUTPUT_DIR_PREFIX}_{timestamp}"
        
        # Create output directory
        os.makedirs(dir_name, exist_ok=True)
        logger.info(f"Created output directory: {dir_name}")
        
        # Save main products
        main_file = os.path.join(dir_name, CSV_FILENAMES['main_products'])
        self.save_to_csv(main_products, CSV_HEADERS['main_products'], main_file)
        logger.info(f"Saved {len(main_products)} main products")
        
        # Save color variations
        color_file = os.path.join(dir_name, CSV_FILENAMES['color_variations'])
        self.save_to_csv(color_variations, CSV_HEADERS['color_variations'], color_file)
        logger.info(f"Saved {len(color_variations)} color variations")
        
        # Save size availability
        size_file = os.path.join(dir_name, CSV_FILENAMES['size_availability'])
        self.save_to_csv(size_availability, CSV_HEADERS['size_availability'], size_file)
        logger.info(f"Saved {len(size_availability)} size availability entries")
        
        # Create time log
        self.create_time_log(start_time, timestamp, main_products, color_variations, size_availability)
        
        return dir_name
    
    def save_to_csv(self, data, headers, filename):
        """
        Save data to CSV file
        
        Args:
            data: List of dictionaries to save
            headers: List of column headers
            filename: Output filename
        """
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            raise
    
    def create_time_log(self, start_time, timestamp, main_products, color_variations, size_availability):
        """
        Create a time log file with scraping statistics
        
        Args:
            start_time: Timestamp when scraping started
            timestamp: Formatted timestamp string
            main_products: List of main products
            color_variations: List of color variations
            size_availability: List of size availability data
        """
        end_time = time.time()
        total_time = end_time - start_time
        
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        log_content = f"""Nike Shoes Scraping - Time Log
=====================================
Start Time: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}
End Time: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}
Total Duration: {hours}h {minutes}m {seconds}s

Scraping Statistics:
------------------------------------
Main Products:          {len(main_products):>6}
Color Variations:       {len(color_variations):>6}
Size Availability:      {len(size_availability):>6}
------------------------------------
Total Records:          {len(main_products) + len(color_variations) + len(size_availability):>6}

Average Time per Product: {total_time / len(main_products) if main_products else 0:.2f}s
"""
        
        log_filename = f"time_log_{timestamp}.txt"
        
        try:
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(log_content)
            logger.info(f"Time log saved: {log_filename}")
        except Exception as e:
            logger.error(f"Error saving time log: {e}")