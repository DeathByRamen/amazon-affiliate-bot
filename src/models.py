"""
Database models for the Amazon Affiliate Bot
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import config

Base = declarative_base()


class Product(Base):
    """Product model for tracking Amazon products"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(10), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    current_price = Column(Float)
    original_price = Column(Float)
    discount_percent = Column(Float)
    category = Column(String(100))
    brand = Column(String(100))
    image_url = Column(Text)
    product_url = Column(Text, nullable=False)
    affiliate_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Product(asin='{self.asin}', title='{self.title[:50]}...')>"


class Deal(Base):
    """Deal model for tracking detected deals"""
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(10), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    original_price = Column(Float, nullable=False)
    deal_price = Column(Float, nullable=False)
    discount_percent = Column(Float, nullable=False)
    savings_amount = Column(Float, nullable=False)
    category = Column(String(100))
    brand = Column(String(100))
    image_url = Column(Text)
    product_url = Column(Text, nullable=False)
    affiliate_url = Column(Text)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime)
    detected_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Deal(asin='{self.asin}', discount={self.discount_percent}%)>"


class Tweet(Base):
    """Tweet model for tracking posted tweets"""
    __tablename__ = "tweets"
    
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String(50), unique=True, index=True)
    deal_id = Column(Integer, nullable=False)
    asin = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    posted_at = Column(DateTime, default=datetime.utcnow)
    engagement_count = Column(Integer, default=0)
    is_successful = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Tweet(tweet_id='{self.tweet_id}', asin='{self.asin}')>"


class BotMetrics(Base):
    """Metrics model for tracking bot performance"""
    __tablename__ = "bot_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    deals_detected = Column(Integer, default=0)
    tweets_posted = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    api_calls_keepa = Column(Integer, default=0)
    api_calls_twitter = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<BotMetrics(date='{self.date}', deals={self.deals_detected})>"


# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed by caller


def init_db():
    """Initialize database with tables"""
    create_tables()
    print("Database initialized successfully")


if __name__ == "__main__":
    init_db()