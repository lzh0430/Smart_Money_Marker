#!/usr/bin/env python3
"""
FastAPI HTTPS Server for Smart Money Follower

REST API server to retrieve SOL wallet data from MongoDB.
"""

import logging
import sys
import yaml
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from database.mongo_client import MongoClientWrapper
from database.models import WalletModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("SmartMoneyServer")

class SmartMoneyServer:
    """FastAPI server for Smart Money Follower API."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the server."""
        self.config = self._load_config(config_path)
        self.mongo_client = MongoClientWrapper(config_path)
        self.wallet_model = WalletModel()
        self.app = self._create_app()
        
        logger.info("Smart Money Server initialized")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        app = FastAPI(
            title="Smart Money Follower API",
            description="REST API for retrieving SOL wallet data",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add API routes."""
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            try:
                # Test MongoDB connection
                stats = self.mongo_client.get_stats()
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "mongodb": "connected",
                    "total_wallets": stats.get('total_wallets', 0)
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail="Service unhealthy")
        
        @app.get("/wallets")
        async def get_wallets(
            min_winrate: Optional[float] = Query(None, description="Minimum winrate filter"),
            limit: Optional[int] = Query(None, description="Maximum number of results", ge=1, le=1000),
            start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
            end_date: Optional[str] = Query(None, description="End date filter (ISO format)")
        ):
            """
            Get wallets with optional filtering.
            
            Query Parameters:
            - min_winrate: Filter wallets with winrate >= this value
            - limit: Maximum number of results (1-1000)
            - start_date: Filter wallets scraped after this date (ISO format)
            - end_date: Filter wallets scraped before this date (ISO format)
            """
            try:
                # Parse date filters
                start_dt = None
                end_dt = None
                
                if start_date:
                    try:
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
                
                if end_date:
                    try:
                        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
                
                # Get wallets from MongoDB
                wallets = self.mongo_client.get_wallets(
                    min_winrate=min_winrate,
                    limit=limit,
                    start_date=start_dt,
                    end_date=end_dt
                )
                
                # Transform for API response
                api_wallets = []
                for wallet in wallets:
                    api_wallet = self.wallet_model.transform_for_api(wallet)
                    api_wallets.append(api_wallet)
                
                logger.info(f"Retrieved {len(api_wallets)} wallets")
                
                return {
                    "wallets": api_wallets,
                    "count": len(api_wallets),
                    "filters": {
                        "min_winrate": min_winrate,
                        "limit": limit,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error retrieving wallets: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @app.get("/wallets/stats")
        async def get_stats():
            """Get collection statistics."""
            try:
                stats = self.mongo_client.get_stats()
                
                logger.info("Retrieved collection statistics")
                return {
                    "statistics": stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error retrieving stats: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @app.get("/wallets/{wallet_address}")
        async def get_wallet(wallet_address: str):
            """
            Get specific wallet by address.
            
            Path Parameters:
            - wallet_address: The wallet address to retrieve
            """
            try:
                wallet = self.mongo_client.get_wallet(wallet_address)
                
                if not wallet:
                    raise HTTPException(status_code=404, detail="Wallet not found")
                
                api_wallet = self.wallet_model.transform_for_api(wallet)
                
                logger.info(f"Retrieved wallet: {wallet_address}")
                return {"wallet": api_wallet}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error retrieving wallet {wallet_address}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
    
    def run(self):
        """Run the FastAPI server."""
        try:
            server_config = self.config['server']
            
            # SSL configuration
            ssl_config = {}
            if server_config.get('ssl_certfile') and server_config.get('ssl_keyfile'):
                ssl_config = {
                    "ssl_certfile": server_config['ssl_certfile'],
                    "ssl_keyfile": server_config['ssl_keyfile']
                }
                logger.info("SSL configuration enabled")
            else:
                logger.warning("SSL configuration not provided - running without HTTPS")
            
            logger.info(f"Starting server on {server_config['host']}:{server_config['port']}")
            
            uvicorn.run(
                self.app,
                host=server_config['host'],
                port=server_config['port'],
                log_level="info",
                **ssl_config
            )
            
        except Exception as e:
            logger.error(f"Error running server: {e}")
            raise
    
    def close(self):
        """Close connections and cleanup."""
        try:
            self.mongo_client.close()
            logger.info("Server cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main entry point."""
    server = None
    try:
        server = SmartMoneyServer()
        server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        if server:
            server.close()

if __name__ == "__main__":
    main()
