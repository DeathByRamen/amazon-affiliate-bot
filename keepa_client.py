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
                  deal_threshold: int = 20,  # Research-backed 20% threshold
                  price_range: tuple = (20, 200),  # Optimal commission range
                  categories: Optional[List[int]] = None,
                  max_sales_rank: int = 50000,  # Popularity filter
                  min_review_count: int = 100,  # Trust filter
                  min_rating: float = 4.0,  # Quality filter
                  prime_only: bool = True) -> List[Dict[str, Any]]:
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
            
            # Optimized parameters for high-converting affiliate deals
            deal_parms = {
                'discountPercentGreater': deal_threshold,  # 20%+ discount for conversion
                'currentPriceMin': price_range[0] * 100,   # $20+ for meaningful commissions
                'currentPriceMax': price_range[1] * 100,   # $200 max for conversion sweet spot
                'salesRankMax': max_sales_rank,            # Top products only
                'reviewCountMin': min_review_count,        # Trust indicator
                'reviewRatingMin': int(min_rating * 10),   # Quality threshold (Keepa uses 10-50 scale)
                'isPrime': 1 if prime_only else 0,        # Prime eligibility for faster conversion
                'isFBA': 1,                                # Fulfilled by Amazon for trust
                'sortType': 15,                            # Sort by deal percentage
                'deltaPercentGreater': deal_threshold,     # Recent price drop
                'priceDropPercent': deal_threshold         # Ensure meaningful drop
            }
            
            if categories:
                deal_parms['categoryIds'] = categories
            
            deals_response = self.api.deals(deal_parms)
            
            if not deals_response or 'deals' not in deals_response:
                self.logger.warning("No deals found in response")
                return []
            
            deals = []
            for deal in deals_response['deals']:
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
        """Parse deal data from Keepa response"""
        try:
            return {
                'asin': deal.get('asin'),
                'title': deal.get('title', '').strip(),
                'current_price': deal.get('current_price', 0) / 100,  # Convert from cents
                'original_price': deal.get('avg30', 0) / 100,
                'discount_percent': deal.get('deal_pct', 0),
                'category': deal.get('category', ''),
                'brand': deal.get('brand', ''),
                'image_url': deal.get('image'),
                'sales_rank': deal.get('sales_rank'),
                'rating': deal.get('rating'),
                'review_count': deal.get('review_count'),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Error parsing deal: {str(e)}")
            return None
    
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
        """Validate if a deal meets our criteria"""
        try:
            # Check minimum discount
            if deal['discount_percent'] < config.MIN_DISCOUNT_PERCENT:
                return False
            
            # Check price range
            current_price = deal['current_price']
            if current_price < 10 or current_price > config.MAX_PRODUCT_PRICE:
                return False
            
            # Check minimum savings
            savings = deal['original_price'] - current_price
            if savings < config.MIN_PRICE_DROP:
                return False
            
            # Check title is not empty
            if not deal['title'] or len(deal['title'].strip()) < 10:
                return False
            
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