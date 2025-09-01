"""
Twitter API client for posting affiliate deals
"""
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import tweepy
from loguru import logger
from config import config


class TwitterClient:
    """Client for posting deals to Twitter"""
    
    def __init__(self):
        """Initialize Twitter client"""
        self._validate_config()
        self.logger = logger.bind(component="twitter_client")
        self.api = self._setup_api()
        
        # Rate limiting tracking
        self.tweets_posted_today = 0
        self.last_tweet_time = None
        self.min_tweet_interval = 300  # 5 minutes between tweets
        
    def _validate_config(self):
        """Validate Twitter API configuration"""
        required_vars = [
            config.TWITTER_API_KEY,
            config.TWITTER_API_SECRET, 
            config.TWITTER_ACCESS_TOKEN,
            config.TWITTER_ACCESS_TOKEN_SECRET
        ]
        
        if not all(required_vars):
            raise ValueError("Missing required Twitter API credentials")
    
    def _setup_api(self):
        """Setup Twitter API client using v2 API"""
        try:
            # Try v2 API first (works with Free tier)
            try:
                self.client_v2 = tweepy.Client(
                    consumer_key=config.TWITTER_API_KEY,
                    consumer_secret=config.TWITTER_API_SECRET,
                    access_token=config.TWITTER_ACCESS_TOKEN,
                    access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET,
                    wait_on_rate_limit=True
                )
                
                # Test v2 API
                me = self.client_v2.get_me()
                if me.data:
                    self.logger.info(f"Twitter API v2 authentication successful")
                    self.api_version = "v2"
                    return self.client_v2
                    
            except Exception as e:
                self.logger.warning(f"v2 API failed: {str(e)}, trying v1.1...")
            
            # Fallback to v1.1 API (requires Basic tier)
            auth = tweepy.OAuth1UserHandler(
                config.TWITTER_API_KEY,
                config.TWITTER_API_SECRET,
                config.TWITTER_ACCESS_TOKEN,
                config.TWITTER_ACCESS_TOKEN_SECRET
            )
            
            api = tweepy.API(auth, wait_on_rate_limit=True)
            api.verify_credentials()
            self.logger.info("Twitter API v1.1 authentication successful")
            self.api_version = "v1.1"
            return api
            
        except Exception as e:
            self.logger.error(f"Failed to setup Twitter API: {str(e)}")
            raise
    
    def can_post_tweet(self) -> bool:
        """Check if we can post a tweet based on rate limits"""
        # Check hourly limit
        if self.tweets_posted_today >= config.MAX_TWEETS_PER_HOUR:
            return False
        
        # Check minimum interval between tweets
        if self.last_tweet_time:
            time_since_last = (datetime.utcnow() - self.last_tweet_time).total_seconds()
            if time_since_last < self.min_tweet_interval:
                return False
        
        return True
    
    def post_deal(self, deal_data: Dict[str, Any]) -> Optional[str]:
        """
        Post a deal to Twitter
        
        Args:
            deal_data: Dictionary containing deal information
            
        Returns:
            Tweet ID if successful, None otherwise
        """
        if not self.can_post_tweet():
            self.logger.warning("Rate limit reached, cannot post tweet")
            return None
        
        try:
            tweet_content = self._create_tweet_content(deal_data)
            
            # Post tweet using v2 API if available, fallback to v1.1
            if hasattr(self, 'client_v2') and self.client_v2:
                response = self.client_v2.create_tweet(text=tweet_content)
                tweet_id = response.data['id']
            else:
                # Fallback to v1.1 API
                tweet = self.api.update_status(tweet_content)
                tweet_id = tweet.id
            
            # Update tracking
            self.tweets_posted_today += 1
            self.last_tweet_time = datetime.utcnow()
            
            self.logger.info(f"Tweet posted successfully: {tweet_id}")
            return str(tweet_id)
            
        except tweepy.TweepyException as e:
            self.logger.error(f"Failed to post tweet: {str(e)}")
            return None
    
    def post_beauty_deal(self, deal_data: Dict[str, Any]) -> Optional[str]:
        """
        Post a beauty deal to Twitter with beauty-specific formatting
        
        Args:
            deal_data: Dictionary containing deal information
            
        Returns:
            Tweet ID if successful, None otherwise
        """
        if not self.can_post_tweet():
            self.logger.warning("Rate limit reached, cannot post beauty tweet")
            return None
        
        try:
            tweet_content = self._create_beauty_tweet_content(deal_data)
            
            # Post tweet using v2 API if available, fallback to v1.1
            if hasattr(self, 'client_v2') and self.client_v2:
                response = self.client_v2.create_tweet(text=tweet_content)
                tweet_id = response.data['id']
            else:
                # Fallback to v1.1 API
                tweet = self.api.update_status(tweet_content)
                tweet_id = tweet.id
            
            # Update tracking
            self.tweets_posted_today += 1
            self.last_tweet_time = datetime.utcnow()
            
            self.logger.info(f"Beauty tweet posted successfully: {tweet_id}")
            return str(tweet_id)
            
        except tweepy.TweepyException as e:
            self.logger.error(f"Failed to post beauty tweet: {str(e)}")
            return None
    
    def _create_tweet_content(self, deal_data: Dict[str, Any]) -> str:
        """Create tweet content from deal data"""
        # Extract deal information
        title = self._clean_title(deal_data['title'])
        discount = int(deal_data['discount_percent'])
        original_price = deal_data['original_price']
        current_price = deal_data['current_price']
        savings = original_price - current_price
        affiliate_url = self._create_affiliate_url(deal_data['asin'])
        
        # Create engaging tweet content
        emoji_fire = "🔥"
        emoji_money = "💰"
        emoji_lightning = "⚡"
        
        # Format prices
        original_str = f"${original_price:.2f}"
        current_str = f"${current_price:.2f}"
        savings_str = f"${savings:.2f}"
        
        # Create tweet with multiple variations for variety
        variations = [
            f"{emoji_fire} {discount}% OFF DEAL!\n\n{title}\n\nWas: {original_str}\nNow: {current_str}\nSave: {savings_str}\n\n{affiliate_url}\n\n#AmazonDeals #Sale #Discount",
            
            f"{emoji_lightning} FLASH DEAL {emoji_lightning}\n\n{title}\n\n{emoji_money} {discount}% OFF ({savings_str} savings)\n{original_str} ➡️ {current_str}\n\n{affiliate_url}\n\n#Deals #Amazon #Savings",
            
            f"{emoji_fire} LIMITED TIME: {discount}% OFF!\n\n{title}\n\nPrice Drop: {original_str} ➡️ {current_str}\nYour Savings: {savings_str}\n\n{affiliate_url}\n\n#DealAlert #AmazonFinds"
        ]
        
        # Select variation based on hour to add variety
        variation_index = datetime.utcnow().hour % len(variations)
        tweet = variations[variation_index]
        
        # Ensure tweet is under character limit
        if len(tweet) > 280:
            # Truncate title if needed
            max_title_length = len(title) - (len(tweet) - 280) - 3
            if max_title_length > 20:
                title = title[:max_title_length] + "..."
                tweet = variations[variation_index].replace(deal_data['title'], title)
        
        return tweet
    
    def _create_beauty_tweet_content(self, deal_data: Dict[str, Any]) -> str:
        """Create beauty-specific tweet content from deal data"""
        # Extract deal information
        title = self._clean_title(deal_data['title'])
        discount = int(deal_data['discount_percent'])
        original_price = deal_data['original_price']
        current_price = deal_data['current_price']
        savings = original_price - current_price
        affiliate_url = self._create_affiliate_url(deal_data['asin'])
        
        # Beauty-specific emojis
        beauty_emojis = ["✨", "💄", "🌟", "💅", "🌸", "💎", "🎀", "🦋"]
        fire_emoji = "🔥"
        money_emoji = "💰"
        
        # Format prices
        original_str = f"${original_price:.2f}"
        current_str = f"${current_price:.2f}"
        savings_str = f"${savings:.2f}"
        
        # Beauty-specific tweet variations
        variations = [
            f"{beauty_emojis[0]} BEAUTY STEAL ALERT {beauty_emojis[0]}\n\n{title}\n\n{fire_emoji} {discount}% OFF\nWas: {original_str} ➡️ Now: {current_str}\nSave: {savings_str}\n\n{affiliate_url}\n\n#BeautyDeals #MakeupSale #BeautyFinds",
            
            f"{beauty_emojis[1]} GLOW UP FOR LESS {beauty_emojis[1]}\n\n{title}\n\n{money_emoji} {discount}% OFF ({savings_str} savings!)\n{original_str} ➡️ {current_str}\n\n{affiliate_url}\n\n#BeautyOnABudget #SkincareDeals #AffordableBeauty",
            
            f"{beauty_emojis[2]} BEAUTY BARGAIN {beauty_emojis[2]}\n\n{title}\n\n{fire_emoji} Limited Time: {discount}% OFF\nPrice Drop: {original_str} ➡️ {current_str}\nYour Savings: {savings_str}\n\n{affiliate_url}\n\n#BeautyBargain #MakeupFinds #TheFrugalBeauty",
            
            f"{beauty_emojis[3]} STUNNING DEAL {beauty_emojis[3]}\n\n{title}\n\n{fire_emoji} {discount}% OFF FLASH SALE\nNormal: {original_str}\nSale: {current_str}\nSave: {savings_str}\n\n{affiliate_url}\n\n#BeautyDeals #GlowForLess #BeautyFinds"
        ]
        
        # Select variation based on hour to add variety
        variation_index = datetime.utcnow().hour % len(variations)
        tweet = variations[variation_index]
        
        # Ensure tweet is under character limit
        if len(tweet) > 280:
            # Truncate title if needed
            max_title_length = len(title) - (len(tweet) - 280) - 3
            if max_title_length > 20:
                title = title[:max_title_length] + "..."
                tweet = variations[variation_index].replace(deal_data['title'], title)
        
        return tweet
    
    def _clean_title(self, title: str) -> str:
        """Clean and format product title for Twitter"""
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Remove common unwanted patterns
        title = re.sub(r'\([^)]*\)', '', title)  # Remove text in parentheses
        title = re.sub(r'\[[^\]]*\]', '', title)  # Remove text in brackets
        title = re.sub(r'Amazon\.com\s*:?\s*', '', title, flags=re.IGNORECASE)
        
        # Truncate if too long
        if len(title) > 100:
            title = title[:97] + "..."
        
        return title.strip()
    
    def _create_affiliate_url(self, asin: str) -> str:
        """Create Amazon affiliate URL"""
        base_url = f"https://amazon.com/dp/{asin}"
        if config.AMAZON_AFFILIATE_TAG:
            return f"{base_url}?tag={config.AMAZON_AFFILIATE_TAG}"
        return base_url
    
    def get_tweet_analytics(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific tweet"""
        try:
            tweet = self.api.get_status(tweet_id, include_entities=True)
            
            return {
                'tweet_id': tweet_id,
                'retweets': tweet.retweet_count,
                'likes': tweet.favorite_count,
                'replies': tweet.reply_count if hasattr(tweet, 'reply_count') else 0,
                'created_at': tweet.created_at,
                'is_retweeted': tweet.retweeted,
                'is_favorited': tweet.favorited
            }
            
        except tweepy.TweepyException as e:
            self.logger.error(f"Error getting tweet analytics for {tweet_id}: {str(e)}")
            return None
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get Twitter account information"""
        try:
            user = self.api.verify_credentials()
            
            return {
                'username': user.screen_name,
                'followers_count': user.followers_count,
                'friends_count': user.friends_count,
                'tweets_count': user.statuses_count,
                'account_created': user.created_at,
                'verified': user.verified
            }
            
        except tweepy.TweepyException as e:
            self.logger.error(f"Error getting account info: {str(e)}")
            return None
    
    def reset_daily_limits(self):
        """Reset daily tracking counters"""
        self.tweets_posted_today = 0
        self.logger.info("Daily tweet limits reset")