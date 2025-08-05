"""
High-volume deal processor optimized for 1200 tokens/minute Keepa plan
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from loguru import logger

from models import Deal, Tweet, Product, BotMetrics, get_db
from keepa_client import KeepaClient
from twitter_client import TwitterClient
from config import config


class HighVolumeDealProcessor:
    """High-volume deal processor for premium Keepa plans"""
    
    def __init__(self, twitter_enabled=True):
        """Initialize high-volume processor"""
        self.keepa_client = KeepaClient()
        self.twitter_enabled = twitter_enabled
        
        if twitter_enabled:
            try:
                self.twitter_client = TwitterClient()
            except Exception as e:
                self.logger.warning(f"Twitter client initialization failed: {e}")
                self.twitter_client = None
                self.twitter_enabled = False
        else:
            self.twitter_client = None
            
        self.logger = logger.bind(component="high_volume_processor")
        
        # High-converting affiliate categories (optimized for commission rates)
        self.target_categories = [
            11055981,   # Luxury Beauty & Personal Care (10% commission)
            1055398,    # Home & Kitchen (3.5-4.5% commission)
            7141123011, # Clothing, Shoes & Jewelry - Women's Fashion (4% commission)
            7147441011, # Clothing, Shoes & Jewelry - Men's Fashion (4% commission) 
            16310101,   # Amazon Devices & Accessories (4% commission)
            165796011,  # Toys & Games (3% commission)
            172282,     # Electronics (2-4% commission, high ticket)
            468642,     # Video Games (3% commission)
            2335752011, # Fashion Accessories (4% commission)
            3375251     # Beauty Tools & Accessories (10% commission)
        ]
        
        # Commission rates for tracking (for prioritization)
        self.category_commissions = {
            11055981: 10.0,   # Beauty
            3375251: 10.0,    # Beauty Tools  
            1055398: 4.0,     # Home & Kitchen
            7141123011: 4.0,  # Women's Fashion
            7147441011: 4.0,  # Men's Fashion
            16310101: 4.0,    # Amazon Devices
            2335752011: 4.0,  # Fashion Accessories
            165796011: 3.0,   # Toys
            468642: 3.0,      # Video Games
            172282: 3.0       # Electronics
        }
        
    def process_high_volume_deals(self) -> Dict[str, int]:
        """
        Process deals using multiple categories and parallel processing
        
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'categories_checked': 0,
            'products_analyzed': 0,
            'deals_detected': 0,
            'deals_filtered': 0,
            'tweets_posted': 0,
            'errors': 0
        }
        
        try:
            self.logger.info("Starting high-volume deal processing")
            start_time = time.time()
            
            # Process multiple categories in parallel
            all_deals = []
            
            # Sort categories by commission rate (highest first)
            sorted_categories = sorted(
                self.target_categories, 
                key=lambda cat: self.category_commissions.get(cat, 0), 
                reverse=True
            )
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit high-commission category processing tasks first
                future_to_category = {
                    executor.submit(self._process_category, cat_id): cat_id 
                    for cat_id in sorted_categories[:5]  # Process top 5 highest-commission categories
                }
                
                # Collect results
                for future in as_completed(future_to_category):
                    category_id = future_to_category[future]
                    try:
                        category_deals = future.result()
                        all_deals.extend(category_deals)
                        stats['categories_checked'] += 1
                        self.logger.info(f"Category {category_id}: {len(category_deals)} deals")
                    except Exception as e:
                        self.logger.error(f"Error processing category {category_id}: {e}")
                        stats['errors'] += 1
            
            stats['deals_detected'] = len(all_deals)
            
            # Filter and process the best deals
            db = get_db()
            try:
                # Sort by commission potential (commission_rate * discount_percent)
                for deal in all_deals:
                    category_id = deal.get('category_id', 0)
                    commission_rate = self.category_commissions.get(category_id, 2.0)
                    deal['commission_score'] = commission_rate * deal.get('discount_percent', 0)
                
                all_deals.sort(key=lambda x: x.get('commission_score', 0), reverse=True)
                top_deals = all_deals[:config.DEAL_CHECK_BATCH_SIZE]
                
                for deal_data in top_deals:
                    stats['products_analyzed'] += 1
                    
                    if self._should_process_deal(deal_data, db):
                        success = self._process_single_deal(deal_data, db)
                        if success:
                            stats['tweets_posted'] += 1
                        else:
                            stats['errors'] += 1
                    else:
                        stats['deals_filtered'] += 1
                        
                    # Check rate limits (only if Twitter is enabled)
                    if self.twitter_enabled and self.twitter_client and not self.twitter_client.can_post_tweet():
                        self.logger.info("Twitter rate limit reached, stopping for this cycle")
                        break
                
                db.commit()
                
            finally:
                db.close()
            
            # Update metrics
            self._update_metrics(stats)
            
            elapsed_time = time.time() - start_time
            self.logger.info(
                f"High-volume processing completed in {elapsed_time:.1f}s: "
                f"Categories: {stats['categories_checked']}, "
                f"Products: {stats['products_analyzed']}, "
                f"Deals: {stats['deals_detected']}, "
                f"Posted: {stats['tweets_posted']}"
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in high-volume processing: {str(e)}")
            stats['errors'] += 1
            return stats
    
    def _process_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Process a single category for deals"""
        try:
            self.logger.debug(f"Processing category {category_id}")
            
            # Use best sellers as a starting point (high-quality products)
            best_sellers = self.keepa_client.api.best_sellers_query(category_id, domain="US")
            
            deals = []
            if best_sellers and 'bestSellersList' in best_sellers:
                products = best_sellers['bestSellersList']['products'][:20]  # Top 20
                
                for product in products:
                    asin = product.get('asin')
                    if not asin:
                        continue
                    
                    # Get detailed product info with optimized filters
                    try:
                        detailed = self.keepa_client.get_deals(
                            domain="US",
                            deal_threshold=config.MIN_DISCOUNT_PERCENT,
                            price_range=(config.MIN_PRODUCT_PRICE, config.MAX_PRODUCT_PRICE),
                            categories=[category_id],
                            max_sales_rank=config.MAX_SALES_RANK,
                            min_review_count=config.MIN_REVIEW_COUNT,
                            min_rating=config.MIN_REVIEW_RATING,
                            prime_only=True
                        )
                        
                        for deal in detailed:
                            deal_data = self._parse_keepa_deal(deal, category_id)
                            if deal_data and self._is_valid_deal(deal_data):
                                deals.append(deal_data)
                                
                    except Exception as e:
                        self.logger.warning(f"Error querying {asin}: {e}")
                        continue
                        
                    # Respect rate limits even in parallel processing
                    time.sleep(0.1)  # Small delay between requests
            
            return deals
            
        except Exception as e:
            self.logger.error(f"Error processing category {category_id}: {e}")
            return []
    
    def _parse_keepa_deal(self, deal: Dict, category_id: int) -> Optional[Dict[str, Any]]:
        """Parse deal data from Keepa deals response"""
        try:
            asin = deal.get('asin')
            title = deal.get('title', '')
            
            if not asin or not title:
                return None
            
            # Extract pricing from Keepa deal format
            current_price = deal.get('current_price', 0)
            original_price = deal.get('original_price', 0)
            discount_percent = deal.get('discount_percent', 0)
            
            # Get quality metrics
            sales_rank = deal.get('sales_rank', 999999)
            rating = deal.get('rating')
            review_count = deal.get('review_count')
            
            # Add commission tracking
            commission_rate = self.category_commissions.get(category_id, 2.0)
            
            return {
                'asin': asin,
                'title': title,
                'current_price': current_price,
                'original_price': original_price,
                'discount_percent': discount_percent,
                'category_id': category_id,
                'commission_rate': commission_rate,
                'sales_rank': sales_rank,
                'rating': rating,
                'review_count': review_count,
                'is_prime': deal.get('is_prime', False),
                'is_fba': deal.get('is_fba', False),
                'image_url': deal.get('image_url', ''),
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing Keepa deal: {e}")
            return None
    
    def _extract_deal_data(self, product: Dict, category_id: int) -> Optional[Dict[str, Any]]:
        """Extract deal data from Keepa product response"""
        try:
            asin = product.get('asin')
            title = product.get('title', '')
            
            if not asin or not title:
                return None
            
            # Extract pricing information
            current_price = 0
            avg_price = 0
            
            # Try to get price from stats
            stats = product.get('stats', {})
            if stats:
                if 'current' in stats and stats['current']:
                    if isinstance(stats['current'], list) and len(stats['current']) > 1:
                        current_price = stats['current'][1] / 100
                    elif isinstance(stats['current'], (int, float)):
                        current_price = stats['current'] / 100
                
                # Get average price for comparison
                if 'avg30' in stats and stats['avg30']:
                    if isinstance(stats['avg30'], list) and len(stats['avg30']) > 1:
                        avg_price = stats['avg30'][1] / 100
                    elif isinstance(stats['avg30'], (int, float)):
                        avg_price = stats['avg30'] / 100
            
            # Calculate discount
            discount_percent = 0
            if avg_price > 0 and current_price > 0:
                discount_percent = ((avg_price - current_price) / avg_price * 100)
            
            # Get additional quality indicators
            sales_rank = stats.get('salesRank', 999999) if stats else 999999
            rating = stats.get('rating') if stats else None
            review_count = stats.get('reviewCount') if stats else None
            
            return {
                'asin': asin,
                'title': title,
                'current_price': current_price,
                'original_price': avg_price,
                'discount_percent': discount_percent,
                'category_id': category_id,
                'sales_rank': sales_rank,
                'rating': rating,
                'review_count': review_count,
                'image_url': product.get('image', ''),
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting deal data: {e}")
            return None
    
    def _is_valid_deal(self, deal_data: Dict[str, Any]) -> bool:
        """Enhanced deal validation based on affiliate conversion research"""
        try:
            # Research-backed 20% minimum discount for conversion trigger
            if deal_data['discount_percent'] < config.MIN_DISCOUNT_PERCENT:
                return False
                
            # Optimal price range for commission vs conversion balance
            current_price = deal_data['current_price']
            if current_price < config.MIN_PRODUCT_PRICE or current_price > config.MAX_PRODUCT_PRICE:
                return False
            
            # Meaningful savings amount
            savings = deal_data['original_price'] - current_price
            if savings < config.MIN_PRICE_DROP:
                return False
            
            # Title quality for trust and SEO
            title = deal_data['title']
            if len(title.strip()) < 20:  # Descriptive titles perform better
                return False
            
            # Sales rank - top 1-5% for proven demand
            sales_rank = deal_data.get('sales_rank', 999999)
            if sales_rank > config.MAX_SALES_RANK:
                return False
            
            # Review-based trust indicators
            rating = deal_data.get('rating')
            if rating is not None and rating < config.MIN_REVIEW_RATING:
                return False
            
            review_count = deal_data.get('review_count')
            if review_count is not None and review_count < config.MIN_REVIEW_COUNT:
                return False
            
            # Prime eligibility for conversion boost
            if not deal_data.get('is_prime', False):
                # Allow non-Prime for very high-commission categories
                commission_rate = deal_data.get('commission_rate', 0)
                if commission_rate < 8.0:  # Beauty/luxury categories get exception
                    return False
            
            # FBA for trust and fast shipping
            if not deal_data.get('is_fba', True):  # Default True for backward compatibility
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating deal: {e}")
            return False
    
    def _should_process_deal(self, deal_data: Dict[str, Any], db) -> bool:
        """Check if deal should be processed (same as regular processor)"""
        asin = deal_data.get('asin')
        if not asin:
            return False
        
        # Check for recent posts
        recent_cutoff = datetime.utcnow() - timedelta(hours=12)  # Shorter cooldown for high-volume
        existing_deal = db.query(Deal).filter(
            Deal.asin == asin,
            Deal.is_posted == True,
            Deal.posted_at > recent_cutoff
        ).first()
        
        if existing_deal:
            return False
        
        # Check Twitter rate limits (only if Twitter is enabled)
        if self.twitter_enabled and self.twitter_client:
            return self.twitter_client.can_post_tweet()
        else:
            return True  # Allow processing without Twitter for testing
    
    def _process_single_deal(self, deal_data: Dict[str, Any], db) -> bool:
        """Process a single deal (same as regular processor but optimized)"""
        try:
            asin = deal_data['asin']
            
            # Create deal record
            deal = Deal(
                asin=asin,
                title=deal_data['title'],
                original_price=deal_data['original_price'],
                deal_price=deal_data['current_price'],
                discount_percent=deal_data['discount_percent'],
                savings_amount=deal_data['original_price'] - deal_data['current_price'],
                category=f"Category_{deal_data.get('category_id', 'Unknown')}",
                brand=deal_data.get('brand', ''),
                image_url=deal_data.get('image_url', ''),
                product_url=f"https://amazon.com/dp/{asin}",
                affiliate_url=self._create_affiliate_url(asin),
                detected_at=datetime.utcnow()
            )
            
            db.add(deal)
            db.flush()
            
            # Post to Twitter (if enabled)
            if self.twitter_enabled and self.twitter_client:
                tweet_id = self.twitter_client.post_deal(deal_data)
                
                if tweet_id:
                    deal.is_posted = True
                    deal.posted_at = datetime.utcnow()
                    
                    # Create tweet record
                    tweet = Tweet(
                        tweet_id=tweet_id,
                        deal_id=deal.id,
                        asin=asin,
                        content=self.twitter_client._create_tweet_content(deal_data),
                        posted_at=datetime.utcnow()
                    )
                    
                    db.add(tweet)
                    
                    self.logger.info(f"Posted high-volume deal for {asin}: {deal_data['discount_percent']:.1f}% off")
                    return True
                else:
                    return False
            else:
                # Just mark as detected without posting (testing mode)
                self.logger.info(f"Detected high-volume deal for {asin}: {deal_data['discount_percent']:.1f}% off (Twitter disabled)")
                return True
                
        except Exception as e:
            self.logger.error(f"Error processing deal: {e}")
            return False
    
    def _create_affiliate_url(self, asin: str) -> str:
        """Create Amazon affiliate URL"""
        base_url = f"https://amazon.com/dp/{asin}"
        if config.AMAZON_AFFILIATE_TAG:
            return f"{base_url}?tag={config.AMAZON_AFFILIATE_TAG}"
        return base_url
    
    def _update_metrics(self, stats: Dict[str, int]):
        """Update bot metrics in database"""
        try:
            db = get_db()
            try:
                today = datetime.utcnow().date()
                existing_metrics = db.query(BotMetrics).filter(
                    BotMetrics.date >= datetime.combine(today, datetime.min.time())
                ).first()
                
                if existing_metrics:
                    existing_metrics.deals_detected += stats['deals_detected']
                    existing_metrics.tweets_posted += stats['tweets_posted']
                    existing_metrics.errors_count += stats['errors']
                    existing_metrics.api_calls_keepa += stats['categories_checked'] + stats['products_analyzed']
                    existing_metrics.api_calls_twitter += stats['tweets_posted']
                else:
                    metrics = BotMetrics(
                        date=datetime.utcnow(),
                        deals_detected=stats['deals_detected'],
                        tweets_posted=stats['tweets_posted'],
                        errors_count=stats['errors'],
                        api_calls_keepa=stats['categories_checked'] + stats['products_analyzed'],
                        api_calls_twitter=stats['tweets_posted']
                    )
                    db.add(metrics)
                
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")