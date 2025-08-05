"""
Command Line Interface for the Amazon Affiliate Bot
"""
import click
import sys
from datetime import datetime, timedelta
from tabulate import tabulate
from loguru import logger

from config import config
from models import init_db, get_db, Deal, Tweet, BotMetrics
from bot import AmazonAffiliateBot
from deal_processor import DealProcessor
from keepa_client import KeepaClient
from twitter_client import TwitterClient


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Amazon Affiliate Bot CLI"""
    if verbose:
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")


@cli.command()
def init():
    """Initialize the database"""
    try:
        init_db()
        click.echo("✅ Database initialized successfully")
    except Exception as e:
        click.echo(f"❌ Error initializing database: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--check-apis', is_flag=True, help='Check API connectivity')
def status(check_apis):
    """Show bot status and configuration"""
    click.echo("🤖 Amazon Affiliate Bot Status")
    click.echo("=" * 40)
    
    # Configuration status
    click.echo("\n📋 Configuration:")
    try:
        config.validate()
        click.echo("✅ Configuration is valid")
    except ValueError as e:
        click.echo(f"❌ Configuration error: {str(e)}")
        return
    
    click.echo(f"   Environment: {config.ENVIRONMENT}")
    click.echo(f"   Database: {config.DATABASE_URL}")
    click.echo(f"   Max tweets/hour: {config.MAX_TWEETS_PER_HOUR}")
    click.echo(f"   Min discount: {config.MIN_DISCOUNT_PERCENT}%")
    
    # Database status
    click.echo("\n💾 Database:")
    try:
        db = get_db()
        db.execute("SELECT 1")
        db.close()
        click.echo("✅ Database connection successful")
    except Exception as e:
        click.echo(f"❌ Database error: {str(e)}")
    
    # API status
    if check_apis:
        click.echo("\n🔌 API Status:")
        
        # Keepa API
        try:
            keepa_client = KeepaClient()
            keepa_status = keepa_client.get_api_status()
            if keepa_status['is_healthy']:
                click.echo(f"✅ Keepa API: {keepa_status['tokens_left']} tokens remaining")
            else:
                click.echo("❌ Keepa API: Not healthy")
        except Exception as e:
            click.echo(f"❌ Keepa API error: {str(e)}")
        
        # Twitter API
        try:
            twitter_client = TwitterClient()
            twitter_info = twitter_client.get_account_info()
            if twitter_info:
                click.echo(f"✅ Twitter API: @{twitter_info['username']} ({twitter_info['followers_count']} followers)")
            else:
                click.echo("❌ Twitter API: Not accessible")
        except Exception as e:
            click.echo(f"❌ Twitter API error: {str(e)}")


@cli.command()
@click.option('--count', '-c', default=10, help='Number of recent deals to show')
def deals(count):
    """Show recent deals"""
    try:
        db = get_db()
        recent_deals = db.query(Deal).order_by(Deal.detected_at.desc()).limit(count).all()
        db.close()
        
        if not recent_deals:
            click.echo("No deals found")
            return
        
        # Format deals for display
        deals_data = []
        for deal in recent_deals:
            deals_data.append([
                deal.asin,
                deal.title[:50] + "..." if len(deal.title) > 50 else deal.title,
                f"${deal.original_price:.2f}",
                f"${deal.deal_price:.2f}",
                f"{deal.discount_percent:.1f}%",
                "✅" if deal.is_posted else "⏳",
                deal.detected_at.strftime("%m/%d %H:%M")
            ])
        
        headers = ["ASIN", "Title", "Original", "Deal Price", "Discount", "Posted", "Detected"]
        click.echo(tabulate(deals_data, headers=headers, tablefmt="grid"))
        
    except Exception as e:
        click.echo(f"❌ Error fetching deals: {str(e)}")


@cli.command()
@click.option('--count', '-c', default=10, help='Number of recent tweets to show')
def tweets(count):
    """Show recent tweets"""
    try:
        db = get_db()
        recent_tweets = db.query(Tweet).order_by(Tweet.posted_at.desc()).limit(count).all()
        db.close()
        
        if not recent_tweets:
            click.echo("No tweets found")
            return
        
        # Format tweets for display
        tweets_data = []
        for tweet in recent_tweets:
            tweets_data.append([
                tweet.tweet_id,
                tweet.asin,
                tweet.content[:60] + "..." if len(tweet.content) > 60 else tweet.content,
                tweet.engagement_count,
                tweet.posted_at.strftime("%m/%d %H:%M")
            ])
        
        headers = ["Tweet ID", "ASIN", "Content", "Engagement", "Posted"]
        click.echo(tabulate(tweets_data, headers=headers, tablefmt="grid"))
        
    except Exception as e:
        click.echo(f"❌ Error fetching tweets: {str(e)}")


@cli.command()
@click.option('--days', '-d', default=7, help='Number of days to analyze')
def metrics(days):
    """Show bot performance metrics"""
    try:
        processor = DealProcessor()
        stats = processor.get_processing_stats(days=days)
        
        if not stats:
            click.echo("No metrics available")
            return
        
        click.echo(f"📊 Bot Metrics (Last {days} days)")
        click.echo("=" * 40)
        click.echo(f"Deals detected: {stats['total_deals_detected']}")
        click.echo(f"Tweets posted: {stats['total_tweets_posted']}")
        click.echo(f"Success rate: {stats['success_rate']:.1f}%")
        click.echo(f"Daily avg deals: {stats['daily_average_deals']:.1f}")
        click.echo(f"Daily avg tweets: {stats['daily_average_tweets']:.1f}")
        click.echo(f"Total errors: {stats['total_errors']}")
        click.echo(f"Keepa API calls: {stats['total_keepa_calls']}")
        click.echo(f"Twitter API calls: {stats['total_twitter_calls']}")
        
    except Exception as e:
        click.echo(f"❌ Error fetching metrics: {str(e)}")


@cli.command()
@click.option('--skip-twitter', is_flag=True, help='Skip Twitter posting, only test deal detection')
def test(skip_twitter):
    """Run a single deal detection cycle for testing"""
    if skip_twitter:
        click.echo("🧪 Running Keepa-only test (no Twitter posting)...")
    else:
        click.echo("🧪 Running full test cycle...")
    
    try:
        if skip_twitter:
            # Test only Keepa functionality
            keepa_client = KeepaClient()
            
            click.echo("🔍 Testing Keepa API connection...")
            status = keepa_client.get_api_status()
            click.echo(f"   Tokens remaining: {status['tokens_left']}")
            click.echo(f"   API healthy: {'✅' if status['is_healthy'] else '❌'}")
            
            if not status['is_healthy']:
                click.echo("❌ Keepa API is not healthy, cannot proceed")
                return
            
            click.echo("\n🛒 Fetching deals from Keepa...")
            deals = keepa_client.get_deals(
                deal_threshold=config.MIN_DISCOUNT_PERCENT,
                price_range=(10, config.MAX_PRODUCT_PRICE)
            )
            
            click.echo(f"📦 Raw deals found: {len(deals)}")
            
            if deals:
                click.echo("\n🏆 Top 5 Deals Found:")
                click.echo("-" * 80)
                for i, deal in enumerate(deals[:5], 1):
                    click.echo(f"{i}. {deal['title'][:60]}...")
                    click.echo(f"   ASIN: {deal['asin']}")
                    click.echo(f"   Price: ${deal['original_price']:.2f} → ${deal['current_price']:.2f}")
                    click.echo(f"   Discount: {deal['discount_percent']:.1f}%")
                    click.echo(f"   Savings: ${deal['original_price'] - deal['current_price']:.2f}")
                    click.echo(f"   Category: {deal.get('category', 'N/A')}")
                    click.echo("")
                
                click.echo("✅ Keepa integration working correctly!")
                
                # Test quality filtering
                processor = DealProcessor()
                quality_deals = [deal for deal in deals if processor._meets_quality_criteria(deal)]
                click.echo(f"📊 Deals passing quality filters: {len(quality_deals)}/{len(deals)}")
            else:
                click.echo("ℹ️  No deals found. Try adjusting MIN_DISCOUNT_PERCENT or price ranges.")
        else:
            # Run full test with Twitter
            bot = AmazonAffiliateBot()
            stats = bot.run_single_cycle()
            
            click.echo("\n📈 Test Results:")
            click.echo(f"Deals detected: {stats['deals_detected']}")
            click.echo(f"Deals filtered: {stats['deals_filtered']}")
            click.echo(f"Tweets posted: {stats['tweets_posted']}")
            click.echo(f"Errors: {stats['errors']}")
            
            if stats['tweets_posted'] > 0:
                click.echo("✅ Test completed successfully")
            elif stats['deals_detected'] > 0:
                click.echo("⚠️  Deals detected but none posted (check filters)")
            else:
                click.echo("ℹ️  No deals detected in this cycle")
                
    except Exception as e:
        click.echo(f"❌ Test failed: {str(e)}")


@cli.command("test-keepa")
def test_keepa():
    """Test Keepa API integration only"""
    click.echo("🧪 Testing Keepa API Integration")
    click.echo("=" * 40)
    
    try:
        # Initialize Keepa client
        keepa_client = KeepaClient()
        
        # Test API status
        click.echo("1️⃣ Testing API connection...")
        status = keepa_client.get_api_status()
        click.echo(f"   Status: {'✅ Healthy' if status['is_healthy'] else '❌ Unhealthy'}")
        click.echo(f"   Tokens remaining: {status['tokens_left']}")
        
        if not status['is_healthy']:
            click.echo("❌ Cannot proceed - API is not healthy")
            return
        
        # Test deal fetching with different thresholds
        click.echo("\n2️⃣ Testing deal detection...")
        
        thresholds = [20, 30, 40, 50]
        for threshold in thresholds:
            click.echo(f"   Testing {threshold}% discount threshold...")
            deals = keepa_client.get_deals(
                deal_threshold=threshold,
                price_range=(10, 200)  # Smaller range for testing
            )
            click.echo(f"   Found: {len(deals)} deals")
            
            if deals and threshold == 30:  # Show details for 30% threshold
                click.echo(f"\n   📋 Sample deal at {threshold}% threshold:")
                deal = deals[0]
                click.echo(f"      Title: {deal['title'][:70]}...")
                click.echo(f"      ASIN: {deal['asin']}")
                click.echo(f"      Price: ${deal['original_price']:.2f} → ${deal['current_price']:.2f}")
                click.echo(f"      Discount: {deal['discount_percent']:.1f}%")
        
        # Test specific product lookup
        click.echo("\n3️⃣ Testing product lookup...")
        test_asin = "B08N5WRWNW"  # Example ASIN
        product = keepa_client.get_product_details(test_asin)
        
        if product:
            click.echo(f"   ✅ Product lookup successful for {test_asin}")
            click.echo(f"   Title: {product['title'][:50]}...")
            click.echo(f"   Price: ${product['current_price']:.2f}")
        else:
            click.echo(f"   ⚠️  Product lookup failed for {test_asin} (may not exist)")
        
        click.echo("\n✅ Keepa integration test completed!")
        
    except Exception as e:
        click.echo(f"❌ Keepa test failed: {str(e)}")
        import traceback
        if '--verbose' in sys.argv:
            click.echo(f"Full error: {traceback.format_exc()}")


@cli.command()
def run():
    """Start the bot"""
    click.echo("🚀 Starting Amazon Affiliate Bot...")
    
    try:
        bot = AmazonAffiliateBot()
        bot.start()
    except KeyboardInterrupt:
        click.echo("\n👋 Bot stopped by user")
    except Exception as e:
        click.echo(f"❌ Bot error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--asin', required=True, help='Amazon ASIN to lookup')
def lookup(asin):
    """Look up a specific product by ASIN"""
    try:
        keepa_client = KeepaClient()
        product = keepa_client.get_product_details(asin)
        
        if not product:
            click.echo(f"❌ Product not found: {asin}")
            return
        
        click.echo(f"📦 Product Details for {asin}")
        click.echo("=" * 40)
        click.echo(f"Title: {product['title']}")
        click.echo(f"Current Price: ${product['current_price']:.2f}")
        click.echo(f"Brand: {product['brand']}")
        click.echo(f"Category: {product['category']}")
        click.echo(f"Sales Rank: {product['sales_rank']}")
        click.echo(f"Rating: {product['rating']}")
        click.echo(f"Reviews: {product['review_count']}")
        
    except Exception as e:
        click.echo(f"❌ Error looking up product: {str(e)}")


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear all data?')
def clear():
    """Clear all bot data (deals, tweets, metrics)"""
    try:
        db = get_db()
        
        # Clear all tables
        db.query(Tweet).delete()
        db.query(Deal).delete()
        db.query(BotMetrics).delete()
        
        db.commit()
        db.close()
        
        click.echo("✅ All data cleared successfully")
        
    except Exception as e:
        click.echo(f"❌ Error clearing data: {str(e)}")


if __name__ == '__main__':
    cli()