"""
Keepa API client for detecting Amazon deals
"""
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import keepa
from loguru import logger
from config import config


class KeepaClient:
    """Client for interacting with Keepa API"""
    
    def __init__(self):
        """Initialize Keepa client"""
        if not config.KEEPA_API_KEY:
            raise ValueError("KEEPA_API_KEY is required")
        
        self.api = keepa.Keepa(config.KEEPA_API_KEY)
        self.logger = logger.bind(component="keepa_client")
        
        # Rate limiting - optimized for 1200 tokens/minute plan
        self.last_request_time = 0
        self.min_request_interval = 0.05  # 0.05 seconds = 1200 requests/minute max
        self.tokens_per_minute = 1200
        self.requests_this_minute = 0
        self.minute_start_time = time.time()
        
    def _rate_limit(self):
        """Implement advanced rate limiting for 1200 tokens/minute plan"""
        current_time = time.time()
        
        # Reset counter if a new minute has started
        if current_time - self.minute_start_time >= 60:
            self.requests_this_minute = 0
            self.minute_start_time = current_time
        
        # Check if we're approaching the per-minute limit
        if self.requests_this_minute >= self.tokens_per_minute - 10:  # Leave 10 token buffer
            sleep_until_next_minute = 60 - (current_time - self.minute_start_time)
            if sleep_until_next_minute > 0:
                self.logger.info(f"Rate limit reached, sleeping {sleep_until_next_minute:.1f}s until next minute")
                time.sleep(sleep_until_next_minute)
                self.requests_this_minute = 0
                self.minute_start_time = time.time()
        
        # Minimum interval between requests (still respect this for API stability)
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.requests_this_minute += 1
    
    def get_deals(self, 
                  domain: str = "US", 
                  deal_threshold: int = 15,  # Balanced 15% threshold
                  price_range: tuple = (15, 300),  # Expanded range
                  categories: Optional[List[int]] = None,
                  max_sales_rank: int = 100000,  # Relaxed filter
                  min_review_count: int = 25,  # More accessible threshold
                  min_rating: float = 3.5,  # Balanced quality filter
                  prime_only: bool = True,
                  use_fallback: bool = True) -> List[Dict[str, Any]]:
        """
        Get current deals from Keepa
        
        Args:
            domain: Amazon domain (US, UK, DE, etc.)
            deal_threshold: Minimum discount percentage
            price_range: (min_price, max_price) tuple
            categories: List of category IDs to filter by
            
        Returns:
            List of deal dictionaries
        """
        self._rate_limit()
        
        try:
            self.logger.info(f"Fetching deals with {deal_threshold}% discount threshold")
            
            # Primary parameters - PROGRESSIVE approach (start with most important)
            deal_parms = {
                'page': 0,                                   # Start with first page
                'domainId': 1,                               # US domain
                'deltaPercentRange': [deal_threshold, 100],  # Discount percentage range
                'currentRange': [price_range[0] * 100, price_range[1] * 100],  # Price in cents
                'sortType': 15                               # Sort by deal percentage
            }
            
            # Add optional filters only if we want to be restrictive
            if max_sales_rank < 500000:  # Only add if reasonably restrictive
                deal_parms['salesRankRange'] = [1, max_sales_rank]
            if min_rating > 3.0:  # Only add if above average
                deal_parms['minRating'] = int(min_rating * 10)
            
            if categories:
                deal_parms['categoryIds'] = categories
            
            deals_response = self.api.deals(deal_parms)
            
            # Check if we got deals, if not try fallback parameters
            if (not deals_response or 'dr' not in deals_response or 
                len(deals_response.get('dr', [])) == 0) and use_fallback:
                
                self.logger.info("No deals with primary parameters, trying fallback...")
                
                # Import config for fallback values
                from config import config
                
                # Fallback parameters - MINIMAL restrictions (get deals, filter later)
                fallback_parms = {
                    'page': 0,                                                 # Start with first page  
                    'domainId': 1,                                             # US domain
                    'deltaPercentRange': [config.FALLBACK_MIN_DISCOUNT, 100], # 10-100% discount
                    'currentRange': [price_range[0] * 100, price_range[1] * 100],  # Price in cents
                    'sortType': 15                                             # Sort by deal percentage
                }
                
                if categories:
                    fallback_parms['categoryIds'] = categories
                
                deals_response = self.api.deals(fallback_parms)
                self.logger.info("Using fallback parameters for broader deal search")
            
            if not deals_response or 'dr' not in deals_response:
                self.logger.warning("No deals found even with fallback parameters")
                return []
            
            deals = []
            for deal in deals_response.get('dr', []):
                deal_data = self._parse_deal(deal)
                if deal_data and self._is_valid_deal(deal_data):
                    deals.append(deal_data)
            
            self.logger.info(f"Found {len(deals)} valid deals")
            return deals
            
        except Exception as e:
            self.logger.error(f"Error fetching deals: {str(e)}")
            return []
    
    def get_product_details(self, asin: str, domain: str = "US") -> Optional[Dict[str, Any]]:
        """
        Get detailed product information for a specific ASIN
        
        Args:
            asin: Amazon ASIN
            domain: Amazon domain
            
        Returns:
            Product details dictionary or None
        """
        self._rate_limit()
        
        try:
            self.logger.debug(f"Fetching product details for ASIN: {asin}")
            
            products = self.api.query(asin, domain=domain, history=False)
            
            if not products or len(products) == 0:
                self.logger.warning(f"No product found for ASIN: {asin}")
                return None
            
            product = products[0]
            return self._parse_product(product)
            
        except Exception as e:
            self.logger.error(f"Error fetching product details for {asin}: {str(e)}")
            return None
    
    def _parse_deal(self, deal: Dict) -> Optional[Dict[str, Any]]:
        """Parse deal data from Keepa response (using correct field names)"""
        try:
            # Get current price (first non-negative value from list)
            current_price_raw = deal.get('current', [])
            current_price = 0
            if isinstance(current_price_raw, list) and len(current_price_raw) > 0:
                # Find first valid price (positive value) in the list
                for price in current_price_raw:
                    if isinstance(price, (int, float)) and price > 0:
                        current_price = price / 100  # Convert from cents to dollars
                        break
            elif isinstance(current_price_raw, (int, float)) and current_price_raw > 0:
                current_price = current_price_raw / 100  # Convert from cents
            
            # Skip deals with invalid prices
            if current_price <= 0:
                return None
            
            # Get average price for discount calculation (avg is list of lists)
            avg_price_raw = deal.get('avg', [])  
            avg_price = current_price  # Default to current price
            
            if isinstance(avg_price_raw, list) and len(avg_price_raw) > 0:
                # avg is a list of lists, find first valid price in any of the lists
                for avg_list in avg_price_raw:
                    if isinstance(avg_list, list) and len(avg_list) > 0:
                        for price in avg_list:
                            if isinstance(price, (int, float)) and price > 0:
                                avg_price = price / 100  # Convert from cents to dollars
                                break
                        if avg_price != current_price:  # Found a valid avg price
                            break
            
            # Calculate discount percentage
            discount_percent = 0
            if avg_price > 0 and current_price > 0:
                discount_percent = ((avg_price - current_price) / avg_price) * 100
                
            return {
                'asin': deal.get('asin', ''),
                'title': deal.get('title', '').strip(),
                'current_price': current_price,
                'original_price': avg_price,
                'discount_percent': discount_percent,
                'category': deal.get('categories', [None])[0] if deal.get('categories') else '',
                'brand': deal.get('brand', ''),
                'image_url': deal.get('imagesCSV', '').split(',')[0] if deal.get('imagesCSV') else '',
                'sales_rank': self._safe_get_value(deal, 'salesRank', 999999),
                'rating': max(self._safe_get_value(deal, 'rating', 0) / 10, 0) if self._safe_get_value(deal, 'rating', 0) > 0 else 0,  # Keepa uses 10-50 scale
                'review_count': self._safe_get_value(deal, 'reviewCount', 0),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Error parsing deal: {str(e)}")
            return None
    
    def _safe_get_value(self, data: Dict, key: str, default_value) -> Any:
        """Safely extract value from data, handling arrays and single values"""
        value = data.get(key, default_value)
        if isinstance(value, list):
            if len(value) > 0:
                return value[-1]  # Return last value from array
            else:
                return default_value
        elif value is None or value == -1:  # Keepa uses -1 for missing data
            return default_value
        else:
            return value
    
    def _parse_product(self, product: Dict) -> Optional[Dict[str, Any]]:
        """Parse product data from Keepa response"""
        try:
            return {
                'asin': product.get('asin'),
                'title': product.get('title', '').strip(),
                'current_price': product.get('stats', {}).get('current', [None, 0])[1] / 100,
                'category': product.get('categoryTree', [{}])[-1].get('name', ''),
                'brand': product.get('brand', ''),
                'image_url': product.get('imagesCSV', '').split(',')[0] if product.get('imagesCSV') else '',
                'sales_rank': product.get('stats', {}).get('salesRankCurrent'),
                'rating': product.get('stats', {}).get('rating'),
                'review_count': product.get('stats', {}).get('reviewCount'),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Error parsing product: {str(e)}")
            return None
    
    def _is_valid_deal(self, deal: Dict[str, Any]) -> bool:
        """Validate if a deal meets our criteria (deals endpoint optimized)"""
        try:
            # Basic discount check (more lenient for testing)
            discount = deal.get('discount_percent', 0)
            if discount < 1.0:  # At least 1% discount
                return False
            
            # Price range check
            current_price = deal.get('current_price', 0)
            if current_price < 5 or current_price > config.MAX_PRODUCT_PRICE:  # $5 minimum
                return False
            
            # Minimum savings check (more lenient)
            original_price = deal.get('original_price', current_price)
            savings = original_price - current_price
            if savings < 0.50:  # At least $0.50 savings
                return False
            
            # Title quality check
            title = deal.get('title', '')
            if not title or len(title.strip()) < 10:
                return False
            
            # Skip quality filters for deals endpoint (data not available)
            # The deals endpoint doesn't provide sales rank, rating, or review count
            # Quality filtering will be done during Twitter posting if needed
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating deal: {str(e)}")
            return False
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get API status and remaining tokens"""
        try:
            status = self.api.tokens_left
            return {
                'tokens_left': status,
                'is_healthy': status > 0,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Error getting API status: {str(e)}")
            return {
                'tokens_left': 0,
                'is_healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow()
            }