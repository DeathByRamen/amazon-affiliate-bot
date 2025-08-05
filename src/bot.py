"""
Main Amazon Affiliate Bot
"""
import time
import schedule
from datetime import datetime
from typing import Dict, Any
import signal
import sys
from loguru import logger

from config import config
from models import init_db
from deal_processor import DealProcessor
from high_volume_processor import HighVolumeDealProcessor
from twitter_client import TwitterClient
from keepa_client import KeepaClient


class AmazonAffiliateBot:
    """Main bot class that orchestrates the affiliate marketing operations"""
    
    def __init__(self):
        """Initialize the bot"""
        self.setup_logging()
        self.logger = logger.bind(component="main_bot")
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            self.logger.error(f"Configuration error: {str(e)}")
            sys.exit(1)
        
        # Initialize components
        self.deal_processor = DealProcessor()
        self.high_volume_processor = HighVolumeDealProcessor()
        self.twitter_client = TwitterClient()
        self.keepa_client = KeepaClient()
        
        # Use high-volume processor if we have premium token plan
        self.use_high_volume = config.KEEPA_TOKENS_PER_MINUTE >= 1000
        
        # Bot state
        self.is_running = False
        self.cycle_count = 0
        
        self.logger.info("Amazon Affiliate Bot initialized successfully")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[component]}</cyan> | "
            "<white>{message}</white>"
        )
        
        # Remove default logger
        logger.remove()
        
        # Add console logger
        logger.add(
            sys.stdout,
            format=log_format,
            level=config.LOG_LEVEL,
            colorize=True
        )
        
        # Add file logger
        logger.add(
            "logs/bot_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="DEBUG",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
    
    def start(self):
        """Start the bot with scheduled operations"""
        self.logger.info("Starting Amazon Affiliate Bot")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize database
        init_db()
        
        # Setup scheduled jobs
        self._setup_schedule()
        
        # Start main loop
        self.is_running = True
        self._run_main_loop()
    
    def _setup_schedule(self):
        """Setup scheduled jobs"""
        # Main deal processing - every 15 minutes (optimized for 1200 tokens/minute)
        schedule.every(15).minutes.do(self._run_deal_cycle)
        
        # Health check - every 5 minutes
        schedule.every(5).minutes.do(self._health_check)
        
        # Daily cleanup - at 2 AM
        schedule.every().day.at("02:00").do(self._daily_cleanup)
        
        # Weekly report - Sunday at 9 AM
        schedule.every().sunday.at("09:00").do(self._weekly_report)
        
        # Reset Twitter daily limits - at midnight
        schedule.every().day.at("00:00").do(self._reset_daily_limits)
        
        self.logger.info("Scheduled jobs configured")
    
    def _run_main_loop(self):
        """Main bot loop"""
        self.logger.info("Bot main loop started")
        
        # Run initial deal cycle
        self._run_deal_cycle()
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def _run_deal_cycle(self):
        """Run a complete deal detection and posting cycle"""
        self.cycle_count += 1
        processor_type = "high-volume" if self.use_high_volume else "standard"
        self.logger.info(f"Starting {processor_type} deal cycle #{self.cycle_count}")
        
        try:
            start_time = time.time()
            
            # Choose processor based on token plan
            if self.use_high_volume:
                stats = self.high_volume_processor.process_high_volume_deals()
            else:
                stats = self.deal_processor.process_deals()
            
            # Log results
            elapsed_time = time.time() - start_time
            self.logger.info(
                f"{processor_type.title()} deal cycle #{self.cycle_count} completed in {elapsed_time:.2f}s: "
                f"Detected: {stats['deals_detected']}, "
                f"Posted: {stats['tweets_posted']}, "
                f"Errors: {stats['errors']}"
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in deal cycle: {str(e)}")
            return {'deals_detected': 0, 'tweets_posted': 0, 'errors': 1}
    
    def _health_check(self):
        """Perform health check on all components"""
        try:
            health_status = {
                'timestamp': datetime.utcnow().isoformat(),
                'bot_running': self.is_running,
                'cycle_count': self.cycle_count
            }
            
            # Check Keepa API status
            keepa_status = self.keepa_client.get_api_status()
            health_status['keepa_healthy'] = keepa_status.get('is_healthy', False)
            health_status['keepa_tokens'] = keepa_status.get('tokens_left', 0)
            
            # Check Twitter API status
            twitter_info = self.twitter_client.get_account_info()
            health_status['twitter_healthy'] = twitter_info is not None
            
            # Check if we can post tweets
            health_status['can_post_tweets'] = self.twitter_client.can_post_tweet()
            
            self.logger.debug(f"Health check: {health_status}")
            
            # Alert if any critical issues
            if not keepa_status.get('is_healthy', False):
                self.logger.warning("Keepa API is not healthy")
            
            if twitter_info is None:
                self.logger.warning("Twitter API is not accessible")
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
    
    def _daily_cleanup(self):
        """Perform daily cleanup tasks"""
        try:
            self.logger.info("Starting daily cleanup")
            
            # Reset Twitter rate limits
            self.twitter_client.reset_daily_limits()
            
            # TODO: Add database cleanup (remove old records, optimize)
            # TODO: Add log rotation
            
            self.logger.info("Daily cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error in daily cleanup: {str(e)}")
    
    def _weekly_report(self):
        """Generate and log weekly performance report"""
        try:
            self.logger.info("Generating weekly report")
            
            # Get statistics for the last 7 days
            stats = self.deal_processor.get_processing_stats(days=7)
            
            if stats:
                report = (
                    f"Weekly Report (Last 7 days):\n"
                    f"- Deals detected: {stats['total_deals_detected']}\n"
                    f"- Tweets posted: {stats['total_tweets_posted']}\n"
                    f"- Success rate: {stats['success_rate']:.1f}%\n"
                    f"- Daily average deals: {stats['daily_average_deals']:.1f}\n"
                    f"- Daily average tweets: {stats['daily_average_tweets']:.1f}\n"
                    f"- Total errors: {stats['total_errors']}"
                )
                
                self.logger.info(report)
            
        except Exception as e:
            self.logger.error(f"Error generating weekly report: {str(e)}")
    
    def _reset_daily_limits(self):
        """Reset daily rate limits"""
        try:
            self.twitter_client.reset_daily_limits()
            self.logger.info("Daily limits reset")
        except Exception as e:
            self.logger.error(f"Error resetting daily limits: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def stop(self):
        """Stop the bot gracefully"""
        self.is_running = False
        self.logger.info("Bot stopped")
    
    def run_single_cycle(self) -> Dict[str, Any]:
        """Run a single deal processing cycle (useful for testing)"""
        return self._run_deal_cycle()


def main():
    """Main entry point"""
    bot = AmazonAffiliateBot()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        # Run single cycle for testing
        stats = bot.run_single_cycle()
        print(f"Single cycle results: {stats}")
    else:
        # Run continuously
        bot.start()


if __name__ == "__main__":
    main()