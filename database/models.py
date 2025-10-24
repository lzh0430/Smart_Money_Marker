from datetime import datetime
from typing import Dict, Any, Optional
import logging

class WalletModel:
    """Data model for wallet documents."""
    
    def __init__(self):
        self.logger = logging.getLogger("WalletModel")
    
    def enrich_wallet_data(self, raw_wallet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich raw wallet data from gmgn API with additional fields.
        
        Args:
            raw_wallet_data: Raw wallet data from getTrendingWallets API
            
        Returns:
            Enriched wallet data dictionary
        """
        try:
            # Create a copy of the raw data
            enriched_data = raw_wallet_data.copy()
            
            # Add scrapeTimestamp
            enriched_data['scrapeTimestamp'] = datetime.utcnow()
            
            # Validate required fields
            if not self._validate_wallet_data(enriched_data):
                self.logger.warning(f"Invalid wallet data: {enriched_data.get('wallet_address', 'unknown')}")
                return None
            
            return enriched_data
            
        except Exception as e:
            self.logger.error(f"Error enriching wallet data: {e}")
            return None
    
    def _validate_wallet_data(self, wallet_data: Dict[str, Any]) -> bool:
        """
        Validate wallet data has required fields.
        
        Args:
            wallet_data: Wallet data dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['wallet_address']
        
        for field in required_fields:
            if field not in wallet_data or not wallet_data[field]:
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    def filter_by_winrate(self, wallets: list, min_winrate: float) -> list:
        """
        Filter wallets by minimum winrate.
        
        Args:
            wallets: List of wallet dictionaries
            min_winrate: Minimum winrate threshold
            
        Returns:
            Filtered list of wallets
        """
        try:
            filtered_wallets = []
            
            for wallet in wallets:
                winrate = wallet.get('winrate_7d', 0)
                if winrate is not None and winrate >= min_winrate:
                    filtered_wallets.append(wallet)
                else:
                    self.logger.debug(f"Filtered out wallet {wallet.get('wallet_address', 'unknown')} - winrate: {winrate}")
            
            self.logger.info(f"Filtered {len(filtered_wallets)} wallets from {len(wallets)} total (min_winrate: {min_winrate})")
            return filtered_wallets
            
        except Exception as e:
            self.logger.error(f"Error filtering wallets by winrate: {e}")
            return []
    
    def transform_for_api(self, wallet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform wallet data for API response.
        
        Args:
            wallet_data: Raw wallet data from database
            
        Returns:
            Transformed data suitable for API response
        """
        try:
            # Create a clean copy for API response
            api_data = {
                'wallet_address': wallet_data.get('wallet_address'),
                'realized_profit': wallet_data.get('realized_profit', 0),
                'winrate_7d': wallet_data.get('winrate_7d', 0),
                'buy': wallet_data.get('buy', 0),
                'sell': wallet_data.get('sell', 0),
                'last_active': wallet_data.get('last_active', 0),
                'scrapeTimestamp': wallet_data.get('scrapeTimestamp'),
                'risk': wallet_data.get('risk', {}),
                'pnl_7d': wallet_data.get('pnl_7d', 0),
                'pnl_30d': wallet_data.get('pnl_30d', 0)
            }
            
            # Convert datetime to ISO string for JSON serialization
            if api_data['scrapeTimestamp'] and isinstance(api_data['scrapeTimestamp'], datetime):
                api_data['scrapeTimestamp'] = api_data['scrapeTimestamp'].isoformat()
            
            return api_data
            
        except Exception as e:
            self.logger.error(f"Error transforming wallet data for API: {e}")
            return wallet_data
    
    def get_wallet_summary(self, wallet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of wallet data for logging/stats.
        
        Args:
            wallet_data: Wallet data dictionary
            
        Returns:
            Summary dictionary
        """
        try:
            return {
                'wallet_address': wallet_data.get('wallet_address', 'unknown'),
                'winrate_7d': wallet_data.get('winrate_7d', 0),
                'realized_profit': wallet_data.get('realized_profit', 0),
                'buy_count': wallet_data.get('buy', 0),
                'sell_count': wallet_data.get('sell', 0),
                'scrapeTimestamp': wallet_data.get('scrapeTimestamp')
            }
        except Exception as e:
            self.logger.error(f"Error creating wallet summary: {e}")
            return {}
