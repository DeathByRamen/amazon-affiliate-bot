"""
Deal processing logic for detecting and filtering Amazon deals
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger

from models import Deal, Tweet, Product, BotMetrics, get_db
from keepa_client import KeepaClient
from twitter_client import TwitterClient
from config import config


class DealProcessor:
    """Main class for processing Amazon deals"""
    
    def __init__(self):
        """Initialize deal processor"""
        self.keepa_client = KeepaClient()
        self.twitter_client = TwitterClient()
        self.logger = logger.bind(component="deal_processor")
        
    def process_deals(self) -> Dict[str, int]:
        """
        Main method to detect and process deals
        
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'deals_detected': 0,
            'deals_filtered': 0,
            'tweets_posted': 0,
            'errors': 0
        }
        
        try:
            self.logger.info("Starting deal processing cycle")
            
            # Get deals from Keepa
            deals = self.keepa_client.get_deals(
                deal_threshold=config.MIN_DISCOUNT_PERCENT,
                price_range=(10, config.MAX_PRODUCT_PRICE)
            )
            
            stats['deals_detected'] = len(deals)
            self.logger.info(f"Detected {len(deals)} potential deals")
            
            if not deals:
                return stats
            
            # Process each deal
            db = get_db()
            try:
                for deal_data in deals:
                    if self._should_process_deal(deal_data, db):
                        success = self._process_single_deal(deal_data, db)
                        if success:
                            stats['tweets_posted'] += 1
                        else:
                            stats['errors'] += 1
                    else:
                        stats['deals_filtered'] += 1
                
                # Commit all changes
                db.commit()
                
            finally:
                db.close()
            
            # Update metrics
            self._update_metrics(stats)
            
            self.logger.info(f"Deal processing completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in deal processing: {str(e)}")
            stats['errors'] += 1
            return stats
    
    def _should_process_deal(self, deal_data: Dict[str, Any], db: Session) -> bool:
        """
        Check if a deal should be processed
        
        Args:
            deal_data: Deal information from Keepa
            db: Database session
            
        Returns:
            True if deal should be processed
        """
        asin = deal_data.get('asin')
        if not asin:
            return False
        
        # Check if deal was already posted recently (within 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        existing_deal = db.query(Deal).filter(
            Deal.asin == asin,
            Deal.is_posted == True,
            Deal.posted_at > recent_cutoff
        ).first()
        
        if existing_deal:
            self.logger.debug(f"Deal for {asin} already posted recently")
            return False
        
        # Check minimum quality criteria
        if not self._meets_quality_criteria(deal_data):
            return False
        
        # Check Twitter rate limits
        if not self.twitter_client.can_post_tweet():
            self.logger.warning("Twitter rate limit reached")
            return False
        
        return True
    
    def _meets_quality_criteria(self, deal_data: Dict[str, Any]) -> bool:
        """Check if deal meets quality criteria"""
        try:
            # Minimum discount percentage
            if deal_data.get('discount_percent', 0) < config.MIN_DISCOUNT_PERCENT:
                return False
            
            # Price range check
            current_price = deal_data.get('current_price', 0)
            if current_price < 10 or current_price > config.MAX_PRODUCT_PRICE:
                return False
            
            # Minimum savings amount
            original_price = deal_data.get('original_price', 0)
            savings = original_price - current_price
            if savings < config.MIN_PRICE_DROP:
                return False
            
            # Title quality check
            title = deal_data.get('title', '')
            if len(title.strip()) < 10:
                return False
            
            # Avoid adult content or restricted categories
            title_lower = title.lower()
            restricted_keywords = [
                'adult', 'sexual', 'intimate', 'lingerie', 'erotic',
                'tobacco', 'alcohol', 'weapon', 'drug'
            ]
            
            if any(keyword in title_lower for keyword in restricted_keywords):
                return False
            
            # Check for valid rating and review count (if available)
            rating = deal_data.get('rating')
            review_count = deal_data.get('review_count')
            
            if rating is not None and rating < 3.5:
                return False
            
            if review_count is not None and review_count < 10:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking quality criteria: {str(e)}")
            return False
    
    def _process_single_deal(self, deal_data: Dict[str, Any], db: Session) -> bool:
        """
        Process a single deal
        
        Args:
            deal_data: Deal information
            db: Database session
            
        Returns:
            True if successfully processed
        """
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
                category=deal_data.get('category', ''),
                brand=deal_data.get('brand', ''),
                image_url=deal_data.get('image_url', ''),
                product_url=f"https://amazon.com/dp/{asin}",
                affiliate_url=self._create_affiliate_url(asin),
                detected_at=datetime.utcnow()
            )
            
            db.add(deal)
            db.flush()  # Get the deal ID
            
            # Post to Twitter
            tweet_id = self.twitter_client.post_deal(deal_data)
            
            if tweet_id:
                # Update deal as posted
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
                
                self.logger.info(f"Successfully processed deal for {asin}")
                return True
            else:
                self.logger.error(f"Failed to post tweet for deal {asin}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing deal: {str(e)}")
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
                # Check if metrics for today already exist
                today = datetime.utcnow().date()
                existing_metrics = db.query(BotMetrics).filter(
                    BotMetrics.date >= datetime.combine(today, datetime.min.time())
                ).first()
                
                if existing_metrics:
                    # Update existing metrics
                    existing_metrics.deals_detected += stats['deals_detected']
                    existing_metrics.tweets_posted += stats['tweets_posted']
                    existing_metrics.errors_count += stats['errors']
                    existing_metrics.api_calls_keepa += 1
                    existing_metrics.api_calls_twitter += stats['tweets_posted']
                else:
                    # Create new metrics record
                    metrics = BotMetrics(
                        date=datetime.utcnow(),
                        deals_detected=stats['deals_detected'],
                        tweets_posted=stats['tweets_posted'],
                        errors_count=stats['errors'],
                        api_calls_keepa=1,
                        api_calls_twitter=stats['tweets_posted']
                    )
                    db.add(metrics)
                
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error updating metrics: {str(e)}")
    
    def get_processing_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get processing statistics for the last N days"""
        try:
            db = get_db()
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                metrics = db.query(BotMetrics).filter(
                    BotMetrics.date >= cutoff_date
                ).all()
                
                total_deals = sum(m.deals_detected for m in metrics)
                total_tweets = sum(m.tweets_posted for m in metrics)
                total_errors = sum(m.errors_count for m in metrics)
                total_keepa_calls = sum(m.api_calls_keepa for m in metrics)
                total_twitter_calls = sum(m.api_calls_twitter for m in metrics)
                
                return {
                    'period_days': days,
                    'total_deals_detected': total_deals,
                    'total_tweets_posted': total_tweets,
                    'total_errors': total_errors,
                    'total_keepa_calls': total_keepa_calls,
                    'total_twitter_calls': total_twitter_calls,
                    'success_rate': (total_tweets / total_deals * 100) if total_deals > 0 else 0,
                    'daily_average_deals': total_deals / days,
                    'daily_average_tweets': total_tweets / days
                }
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error getting processing stats: {str(e)}")
            return {}