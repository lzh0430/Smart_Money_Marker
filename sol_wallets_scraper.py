#!/usr/bin/env python3
"""
SOL Wallets Scraper

Daily scheduled script to fetch trending SOL wallets from gmgn API,
filter by winrate threshold, and store/update in MongoDB.
"""

import logging
import sys
import yaml
from datetime import datetime
from typing import List, Dict
from gmgn import gmgn
from database.mongo_client import MongoClientWrapper
from database.models import WalletModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sol_wallets_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("SOLWalletsScraper")

class SOLWalletsScraper:
    """Scraper for SOL trending wallets."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the scraper."""
        self.config = self._load_config(config_path)
        self.gmgn_client = gmgn()
        self.mongo_client = MongoClientWrapper(config_path)
        self.wallet_model = WalletModel()
        
        logger.info("SOL Wallets Scraper initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def fetch_trending_wallets(self) -> List[Dict]:
        """
        Fetch trending wallets from gmgn API.
        
        Returns:
            List of raw wallet data from API
        """
        try:
            timeframe = self.config['scraper']['timeframe']
            wallet_tag = self.config['scraper']['wallet_tag']
            
            logger.info(f"Fetching trending wallets - timeframe: {timeframe}, tag: {wallet_tag}")
            
            response = self.gmgn_client.getTrendingWallets(
                timeframe=timeframe,
                walletTag=wallet_tag
            )
            
            if not response or 'rank' not in response:
                logger.warning("No wallet data received from API")
                return []
            
            wallets = response['rank']
            logger.info(f"Fetched {len(wallets)} wallets from gmgn API")
            
            return wallets
            
        except Exception as e:
            logger.error(f"Error fetching trending wallets: {e}")
            return []
    
    def filter_wallets(self, wallets: List[Dict]) -> List[Dict]:
        """
        Filter wallets by winrate threshold.
        
        Args:
            wallets: List of raw wallet data
            
        Returns:
            Filtered list of wallets
        """
        try:
            min_winrate = self.config['scraper']['min_winrate']
            filtered_wallets = self.wallet_model.filter_by_winrate(wallets, min_winrate)
            
            logger.info(f"Filtered to {len(filtered_wallets)} wallets (min_winrate: {min_winrate})")
            return filtered_wallets
            
        except Exception as e:
            logger.error(f"Error filtering wallets: {e}")
            return []
    
    def enrich_wallets(self, wallets: List[Dict]) -> List[Dict]:
        """
        Enrich wallet data with additional fields.
        
        Args:
            wallets: List of wallet data
            
        Returns:
            List of enriched wallet data
        """
        try:
            enriched_wallets = []
            
            for wallet in wallets:
                enriched_wallet = self.wallet_model.enrich_wallet_data(wallet)
                if enriched_wallet:
                    enriched_wallets.append(enriched_wallet)
                else:
                    logger.warning(f"Skipped invalid wallet: {wallet.get('wallet_address', 'unknown')}")
            
            logger.info(f"Enriched {len(enriched_wallets)} wallets")
            return enriched_wallets
            
        except Exception as e:
            logger.error(f"Error enriching wallets: {e}")
            return []
    
    def store_wallets(self, wallets: List[Dict]) -> Dict[str, int]:
        """
        Store wallets in MongoDB using upsert operations.
        
        Args:
            wallets: List of enriched wallet data
            
        Returns:
            Dictionary with operation statistics
        """
        try:
            if not wallets:
                logger.warning("No wallets to store")
                return {'inserted': 0, 'updated': 0, 'errors': 0}
            
            logger.info(f"Storing {len(wallets)} wallets in MongoDB")
            stats = self.mongo_client.upsert_wallets_batch(wallets)
            
            logger.info(f"Storage completed - Inserted: {stats['inserted']}, Updated: {stats['updated']}, Errors: {stats['errors']}")
            return stats
            
        except Exception as e:
            logger.error(f"Error storing wallets: {e}")
            return {'inserted': 0, 'updated': 0, 'errors': 1}
    
    def run_scrape(self) -> bool:
        """
        Run the complete scraping process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Starting SOL wallets scrape process")
            start_time = datetime.utcnow()
            
            # Step 1: Fetch trending wallets
            raw_wallets = self.fetch_trending_wallets()
            if not raw_wallets:
                logger.error("No wallets fetched from API")
                return False
            
            # Step 2: Filter by winrate
            filtered_wallets = self.filter_wallets(raw_wallets)
            if not filtered_wallets:
                logger.warning("No wallets passed winrate filter")
                return True  # Not an error, just no qualifying wallets
            
            # Step 3: Enrich wallet data
            enriched_wallets = self.enrich_wallets(filtered_wallets)
            if not enriched_wallets:
                logger.error("No wallets successfully enriched")
                return False
            
            # Step 4: Store in MongoDB
            storage_stats = self.store_wallets(enriched_wallets)
            
            # Log summary
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Scrape process completed successfully in {duration:.2f} seconds")
            logger.info(f"Final stats - Total processed: {len(enriched_wallets)}, "
                       f"Inserted: {storage_stats['inserted']}, "
                       f"Updated: {storage_stats['updated']}, "
                       f"Errors: {storage_stats['errors']}")
            
            return storage_stats['errors'] == 0
            
        except Exception as e:
            logger.error(f"Error in scrape process: {e}")
            return False
    
    def close(self):
        """Close connections and cleanup."""
        try:
            self.mongo_client.close()
            logger.info("Scraper cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main entry point."""
    scraper = None
    try:
        scraper = SOLWalletsScraper()
        success = scraper.run_scrape()
        
        if success:
            logger.info("Scraper completed successfully")
            sys.exit(0)
        else:
            logger.error("Scraper completed with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
