"""
Configuration management for the Amazon Affiliate Bot
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""
    
    # Keepa API
    KEEPA_API_KEY: str = os.getenv("KEEPA_API_KEY", "")
    
    # Twitter API
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_TOKEN_SECRET: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    
    # Amazon Affiliate
    AMAZON_AFFILIATE_TAG: str = os.getenv("AMAZON_AFFILIATE_TAG", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///deals.db")
    
    # Bot behavior - BALANCED for deal volume + quality
    MAX_TWEETS_PER_HOUR: int = int(os.getenv("MAX_TWEETS_PER_HOUR", "20"))  # Increased for higher throughput
    MIN_DISCOUNT_PERCENT: float = float(os.getenv("MIN_DISCOUNT_PERCENT", "15"))  # Relaxed from 20% to 15%
    MIN_PRICE_DROP: float = float(os.getenv("MIN_PRICE_DROP", "5.00"))  # Relaxed from $10 to $5
    MIN_PRODUCT_PRICE: float = float(os.getenv("MIN_PRODUCT_PRICE", "15.00"))  # Relaxed from $20 to $15
    MAX_PRODUCT_PRICE: float = float(os.getenv("MAX_PRODUCT_PRICE", "300.00"))  # Expanded from $200 to $300
    
    # Beauty-specific Twitter posting settings
    BEAUTY_ONLY_TWEETS: bool = os.getenv("BEAUTY_ONLY_TWEETS", "true").lower() == "true"
    BEAUTY_MIN_DISCOUNT: float = float(os.getenv("BEAUTY_MIN_DISCOUNT", "20"))  # Higher threshold for beauty
    BEAUTY_MIN_PRICE: float = float(os.getenv("BEAUTY_MIN_PRICE", "20.00"))  # Beauty products typically higher priced
    BEAUTY_MAX_PRICE: float = float(os.getenv("BEAUTY_MAX_PRICE", "200.00"))  # Premium but accessible beauty range
    
    # Quality filters - RELAXED for more deals
    MIN_REVIEW_COUNT: int = int(os.getenv("MIN_REVIEW_COUNT", "25"))  # Relaxed from 100 to 25
    MIN_REVIEW_RATING: float = float(os.getenv("MIN_REVIEW_RATING", "3.5"))  # Relaxed from 4.0 to 3.5
    MAX_SALES_RANK: int = int(os.getenv("MAX_SALES_RANK", "100000"))  # Relaxed from 50k to 100k
    
    # Fallback settings if primary filters return no deals
    FALLBACK_MAX_SALES_RANK: int = int(os.getenv("FALLBACK_MAX_SALES_RANK", "500000"))
    FALLBACK_MIN_REVIEW_COUNT: int = int(os.getenv("FALLBACK_MIN_REVIEW_COUNT", "10"))
    FALLBACK_MIN_DISCOUNT: float = float(os.getenv("FALLBACK_MIN_DISCOUNT", "10.0"))
    
    # High-volume plan settings
    KEEPA_TOKENS_PER_MINUTE: int = int(os.getenv("KEEPA_TOKENS_PER_MINUTE", "1200"))
    DEAL_CHECK_BATCH_SIZE: int = int(os.getenv("DEAL_CHECK_BATCH_SIZE", "50"))  # Process more deals per cycle
    
    # Monitoring
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HEALTH_CHECK_PORT: int = int(os.getenv("HEALTH_CHECK_PORT", "8080"))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present"""
        required_vars = [
            "KEEPA_API_KEY",
            "TWITTER_API_KEY", 
            "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET",
            "AMAZON_AFFILIATE_TAG"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True


# Create global config instance
config = Config()