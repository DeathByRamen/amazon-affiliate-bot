#!/usr/bin/env python3
"""
Twitter Setup and Testing Script
Helps configure and validate Twitter API integration
"""

import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_env_file():
    """Check if .env file exists and has required Twitter credentials"""
    env_path = '.env'
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        print("📋 Please copy env.example to .env and fill in your credentials:")
        print("   cp env.example .env")
        return False
    
    # Check for Twitter credentials
    required_vars = [
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET', 
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET'
    ]
    
    missing_vars = []
    with open(env_path, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=your_" in content or f"{var}=" not in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or incomplete Twitter credentials: {', '.join(missing_vars)}")
        print("📋 Please update your .env file with real Twitter API credentials")
        return False
    
    print("✅ .env file found with Twitter credentials")
    return True

def test_twitter_connection():
    """Test Twitter API connection"""
    print("\n🐦 Testing Twitter API Connection...")
    try:
        from twitter_client import TwitterClient
        
        client = TwitterClient()
        info = client.get_account_info()
        
        if info:
            print(f"✅ Connected to Twitter successfully!")
            print(f"   Username: @{info['username']}")
            print(f"   Followers: {info['followers_count']:,}")
            print(f"   Following: {info['friends_count']:,}")
            print(f"   Total Tweets: {info['tweets_count']:,}")
            print(f"   Account Created: {info['account_created']}")
            print(f"   Verified: {'Yes' if info['verified'] else 'No'}")
            return True
        else:
            print("❌ Failed to get account info")
            return False
            
    except Exception as e:
        print(f"❌ Twitter connection failed: {str(e)}")
        if "401" in str(e):
            print("💡 This usually means invalid API credentials")
        elif "403" in str(e):
            print("💡 Check that your app has 'Read and Write' permissions")
        return False

def create_sample_tweet_content():
    """Create sample tweet content for testing"""
    sample_deal = {
        'title': 'Sample Beauty Deal - Premium Skincare Serum',
        'asin': 'B07SAMPLE123',
        'discount_percent': 25,
        'original_price': 49.99,
        'current_price': 37.49,
        'brand': 'SampleBrand',
        'category': 'Beauty & Personal Care',
        'rating': 4.5,
        'review_count': 150
    }
    
    print("\n📝 Sample Tweet Content Preview:")
    print("=" * 50)
    
    try:
        from twitter_client import TwitterClient
        client = TwitterClient()
        
        # Regular tweet content
        regular_content = client._create_tweet_content(sample_deal)
        print("📄 Regular Tweet Format:")
        print(regular_content)
        print(f"   Length: {len(regular_content)}/280 characters")
        
        print("\n" + "=" * 50)
        
        # Beauty tweet content
        beauty_content = client._create_beauty_tweet_content(sample_deal)
        print("💄 Beauty Tweet Format:")
        print(beauty_content)
        print(f"   Length: {len(beauty_content)}/280 characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample content: {str(e)}")
        return False

def ask_post_test_tweet():
    """Ask user if they want to post a test tweet"""
    print("\n🧪 Test Tweet Options:")
    print("1. Preview only (recommended)")
    print("2. Post actual test tweet (will appear on your Twitter)")
    print("3. Skip test")
    
    while True:
        choice = input("\nChoose option (1-3): ").strip()
        if choice == "1":
            return "preview"
        elif choice == "2":
            return "post"
        elif choice == "3":
            return "skip"
        else:
            print("Please enter 1, 2, or 3")

def post_test_tweet():
    """Post a test tweet"""
    print("\n🚀 Posting Test Tweet...")
    
    test_deal = {
        'title': '🧪 TEST - Bot Setup Complete!',
        'asin': 'B00TEST123',
        'discount_percent': 0,
        'original_price': 1.00,
        'current_price': 1.00
    }
    
    try:
        from twitter_client import TwitterClient
        client = TwitterClient()
        
        # Create simple test tweet
        test_content = f"🤖 Bot setup test at {datetime.now().strftime('%I:%M %p')} - Delete me! #BotTest"
        
        # Post using the API directly for this test
        tweet = client.api.update_status(test_content)
        
        print(f"✅ Test tweet posted successfully!")
        print(f"   Tweet ID: {tweet.id}")
        print(f"   URL: https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
        print("\n💡 You can delete this test tweet from your Twitter account")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to post test tweet: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🚀 Twitter Setup and Testing for Amazon Affiliate Bot")
    print("=" * 60)
    
    # Step 1: Check environment file
    if not check_env_file():
        print("\n📋 Next Steps:")
        print("1. Copy env.example to .env: cp env.example .env")
        print("2. Get Twitter API credentials from https://developer.twitter.com")
        print("3. Edit .env file with your real credentials")
        print("4. Run this script again")
        return
    
    # Step 2: Test Twitter connection
    if not test_twitter_connection():
        print("\n📋 Next Steps:")
        print("1. Verify your Twitter API credentials in .env")
        print("2. Check that your Twitter app has 'Read and Write' permissions")
        print("3. Make sure your developer account is approved")
        return
    
    # Step 3: Show sample content
    if not create_sample_tweet_content():
        return
    
    # Step 4: Optional test tweet
    test_choice = ask_post_test_tweet()
    
    if test_choice == "post":
        post_test_tweet()
    elif test_choice == "preview":
        print("✅ Preview complete - no tweets posted")
    
    print("\n🎉 Twitter Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Run the bot: python src/cli.py run")
    print("2. Check stats: python src/cli.py stats")
    print("3. Monitor performance and adjust settings as needed")
    print("\n📖 For more details, see TWITTER_SETUP.md")

if __name__ == "__main__":
    main()
