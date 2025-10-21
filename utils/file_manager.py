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
    
    # === FIX: Add fit_variations to function definition ===
    def save_all_data(self, main_products, fit_variations, color_variations, size_availability, start_time):
        """
        Save all scraped data to CSV files
        
        Args:
            main_products: List of main product data
            fit_variations: List of fit variation data
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
        
        # === FIX: Add saving logic for fit_variations ===
        fit_file = os.path.join(dir_name, CSV_FILENAMES['fit_variations'])
        self.save_to_csv(fit_variations, CSV_HEADERS['fit_variations'], fit_file)
        logger.info(f"Saved {len(fit_variations)} fit variations")
        
        # Save color variations
        color_file = os.path.join(dir_name, CSV_FILENAMES['color_variations'])
        self.save_to_csv(color_variations, CSV_HEADERS['color_variations'], color_file)
        logger.info(f"Saved {len(color_variations)} color variations")
        
        # Save size availability
        size_file = os.path.join(dir_name, CSV_FILENAMES['size_availability'])
        self.save_to_csv(size_availability, CSV_HEADERS['size_availability'], size_file)
        logger.info(f"Saved {len(size_availability)} size availability entries")
        
        # Create time log
        # === FIX: Pass fit_variations to time log function ===
        self.create_time_log(start_time, timestamp, main_products, fit_variations, color_variations, size_availability)
        
        return dir_name
    
    def save_to_csv(self, data, headers, filename):
        """
        Save data to CSV file
        
        Args:
            data: List of dictionaries to save
            headers: List of column headers
            filename: Output filename
        """
        # === Add check for empty data to avoid errors ===
        if not data:
            logger.warning(f"No data for {filename}, skipping.")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                # Filter headers to only include those present in the data
                # This prevents errors if data is missing optional keys
                valid_headers = [h for h in headers if h in data[0]]
                writer = csv.DictWriter(csvfile, fieldnames=valid_headers, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            raise
    
    # === FIX: Add fit_variations to function definition and log content ===
    def create_time_log(self, start_time, timestamp, main_products, fit_variations, color_variations, size_availability):
        """
        Create a time log file with scraping statistics
        
        Args:
            start_time: Timestamp when scraping started
            timestamp: Formatted timestamp string
            main_products: List of main products
            fit_variations: List of fit variations
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
Fit Variations:         {len(fit_variations):>6}
Color Variations:       {len(color_variations):>6}
Size Availability:      {len(size_availability):>6}
------------------------------------
Total Records:          {len(main_products) + len(fit_variations) + len(color_variations) + len(size_availability):>6}

Average Time per Product: {total_time / len(main_products) if main_products else 0:.2f}s
"""
        
        # === FIX: Join path to save log inside the output directory ===
        dir_name = f"{OUTPUT_DIR_PREFIX}_{timestamp}"
        log_filename = f"time_log_{timestamp}.txt"
        log_filepath = os.path.join(dir_name, log_filename)
        
        try:
            with open(log_filepath, 'w', encoding='utf-8') as f:
                f.write(log_content)
            logger.info(f"Time log saved: {log_filepath}")
        except Exception as e:
            logger.error(f"Error saving time log: {e}")
