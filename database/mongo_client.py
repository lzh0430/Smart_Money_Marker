import logging
from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import yaml
import os

class MongoClientWrapper:
    """MongoDB client wrapper for Smart Money Follower."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize MongoDB connection."""
        self.logger = logging.getLogger("MongoClientWrapper")
        self.client = None
        self.db = None
        self.collection = None
        self._load_config(config_path)
        self._connect()
    
    def _load_config(self, config_path: str):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.mongodb_config = config['mongodb']
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            raise
    
    def _connect(self):
        """Establish MongoDB connection."""
        try:
            # Build connection string with authentication
            if self.mongodb_config.get('username') and self.mongodb_config.get('password'):
                # Use authentication
                connection_string = f"mongodb://{self.mongodb_config['username']}:{self.mongodb_config['password']}@{self.mongodb_config['host']}:{self.mongodb_config['port']}"
                self.client = MongoClient(connection_string)
            else:
                # No authentication
                self.client = MongoClient(
                    host=self.mongodb_config['host'],
                    port=self.mongodb_config['port']
                )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.mongodb_config['database']]
            self.collection = self.db[self.mongodb_config['collection']]
            self._create_indexes()
            self.logger.info("Successfully connected to MongoDB with authentication")
        except ConnectionFailure as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create necessary indexes for optimal performance."""
        try:
            # Create unique index on wallet_address
            self.collection.create_index("wallet_address", unique=True)
            # Create index on scrapeTimestamp for date range queries
            self.collection.create_index("scrapeTimestamp")
            # Create index on winrate_7d for filtering
            self.collection.create_index("winrate_7d")
            self.logger.info("MongoDB indexes created successfully")
        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")
    
    def upsert_wallet(self, wallet_data: Dict) -> bool:
        """
        Upsert a wallet document.
        
        Args:
            wallet_data: Wallet data dictionary with wallet_address as unique key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add scrapeTimestamp if not present
            if 'scrapeTimestamp' not in wallet_data:
                wallet_data['scrapeTimestamp'] = datetime.utcnow()
            
            # Use wallet_address as the unique identifier for upsert
            result = self.collection.replace_one(
                {"wallet_address": wallet_data['wallet_address']},
                wallet_data,
                upsert=True
            )
            
            if result.upserted_id:
                self.logger.info(f"Inserted new wallet: {wallet_data['wallet_address']}")
            else:
                self.logger.info(f"Updated existing wallet: {wallet_data['wallet_address']}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error upserting wallet {wallet_data.get('wallet_address', 'unknown')}: {e}")
            return False
    
    def upsert_wallets_batch(self, wallets: List[Dict]) -> Dict[str, int]:
        """
        Upsert multiple wallets in batch.
        
        Args:
            wallets: List of wallet data dictionaries
            
        Returns:
            Dict with counts: {'inserted': int, 'updated': int, 'errors': int}
        """
        stats = {'inserted': 0, 'updated': 0, 'errors': 0}
        
        for wallet in wallets:
            try:
                # Add scrapeTimestamp if not present
                if 'scrapeTimestamp' not in wallet:
                    wallet['scrapeTimestamp'] = datetime.utcnow()
                
                result = self.collection.replace_one(
                    {"wallet_address": wallet['wallet_address']},
                    wallet,
                    upsert=True
                )
                
                if result.upserted_id:
                    stats['inserted'] += 1
                else:
                    stats['updated'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing wallet {wallet.get('wallet_address', 'unknown')}: {e}")
                stats['errors'] += 1
        
        self.logger.info(f"Batch upsert completed: {stats}")
        return stats
    
    def get_wallet(self, wallet_address: str) -> Optional[Dict]:
        """Get a specific wallet by address."""
        try:
            return self.collection.find_one({"wallet_address": wallet_address})
        except Exception as e:
            self.logger.error(f"Error retrieving wallet {wallet_address}: {e}")
            return None
    
    def get_wallets(self, 
                   min_winrate: Optional[float] = None,
                   limit: Optional[int] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get wallets with optional filtering.
        
        Args:
            min_winrate: Minimum winrate filter
            limit: Maximum number of results
            start_date: Filter wallets scraped after this date
            end_date: Filter wallets scraped before this date
            
        Returns:
            List of wallet documents
        """
        try:
            query = {}
            
            # Add winrate filter
            if min_winrate is not None:
                query['winrate_7d'] = {'$gte': min_winrate}
            
            # Add date range filter
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter['$gte'] = start_date
                if end_date:
                    date_filter['$lte'] = end_date
                query['scrapeTimestamp'] = date_filter
            
            cursor = self.collection.find(query).sort('scrapeTimestamp', -1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except Exception as e:
            self.logger.error(f"Error retrieving wallets: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get collection statistics."""
        try:
            total_count = self.collection.count_documents({})
            
            # Get average winrate
            pipeline = [
                {"$group": {"_id": None, "avg_winrate": {"$avg": "$winrate_7d"}}}
            ]
            avg_result = list(self.collection.aggregate(pipeline))
            avg_winrate = avg_result[0]['avg_winrate'] if avg_result else 0
            
            # Get latest scrape timestamp
            latest_doc = self.collection.find_one(sort=[("scrapeTimestamp", -1)])
            latest_scrape = latest_doc['scrapeTimestamp'] if latest_doc else None
            
            return {
                'total_wallets': total_count,
                'average_winrate': round(avg_winrate, 3) if avg_winrate else 0,
                'latest_scrape': latest_scrape.isoformat() if latest_scrape else None
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")
