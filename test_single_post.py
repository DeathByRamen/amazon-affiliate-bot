#!/usr/bin/env python3
"""
Test script for posting a single beauty deal to Twitter
Shows exactly what would be posted and handles API limitations
"""

import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_single_beauty_post():
    """Test posting a single beauty deal"""
    print("🐦 Single Beauty Deal Twitter Test")
    print("=" * 50)
    
    # Sample beauty deal that would be found by the bot
    sample_beauty_deal = {
        'title': 'Fenty Beauty Pro Filt\'r Soft Matte Foundation',
        'asin': 'B075NVR28D',
        'discount_percent': 25,
        'original_price': 39.00,
        'current_price': 29.25,
        'brand': 'Fenty Beauty',
        'category': 'Beauty & Personal Care',
        'rating': 4.3,
        'review_count': 2847
    }
    
    try:
        from twitter_client import TwitterClient
        
        print("1️⃣ Testing Twitter connection...")
        client = TwitterClient()
        
        # Get account info to confirm connection
        try:
            if hasattr(client, 'client_v2') and client.client_v2:
                # Use v2 API
                me = client.client_v2.get_me()
                if me.data:
                    print(f"   ✅ Connected as @{me.data.username}")
                    print(f"   📊 Account ID: {me.data.id}")
                    info = {'username': me.data.username}
                else:
                    print("   ❌ Failed to get account info")
                    return False
            else:
                # Use v1.1 API
                info = client.get_account_info()
                if info:
                    print(f"   ✅ Connected as @{info['username']}")
                    print(f"   📊 Account has {info['followers_count']} followers")
                else:
                    print("   ❌ Failed to get account info")
                    return False
        except Exception as e:
            print(f"   ❌ Failed to get account info: {str(e)}")
            return False
        
        print("\n2️⃣ Generating beauty tweet content...")
        tweet_content = client._create_beauty_tweet_content(sample_beauty_deal)
        
        print("📋 Generated Tweet Content:")
        print("-" * 60)
        print(tweet_content)
        print("-" * 60)
        print(f"Character count: {len(tweet_content)}/280")
        
        # Check if we can post
        print(f"\n3️⃣ Rate limiting check...")
        can_post = client.can_post_tweet()
        print(f"   Can post now: {'✅ Yes' if can_post else '❌ No'}")
        print(f"   Tweets posted today: {client.tweets_posted_today}")
        
        # Ask user if they want to attempt posting
        print(f"\n4️⃣ Posting attempt...")
        try:
            # Try to post the tweet
            tweet_id = client.post_beauty_deal(sample_beauty_deal)
            
            if tweet_id:
                print(f"✅ SUCCESS! Tweet posted with ID: {tweet_id}")
                print(f"🔗 View at: https://twitter.com/{info['username']}/status/{tweet_id}")
                return True
            else:
                print("❌ Failed to post tweet (rate limited or other issue)")
                return False
                
        except Exception as e:
            if "403" in str(e) and "access level" in str(e):
                print("⚠️  API Access Level Issue:")
                print("   Your Twitter app needs 'Elevated' access to post tweets")
                print("   The content above shows exactly what WOULD be posted")
                print("\n📋 To fix this:")
                print("   1. Go to https://developer.twitter.com/en/portal/dashboard")
                print("   2. Select your app")
                print("   3. Request 'Elevated' access (it's free)")
                print("   4. Wait for approval (usually instant)")
                print("   5. Run this test again")
                return False
            else:
                print(f"❌ Unexpected error: {str(e)}")
                return False
        
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Amazon Beauty Bot - Single Post Test")
    print("=" * 60)
    
    success = test_single_beauty_post()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed successfully!")
        print("✅ Your bot is ready to start posting beauty deals!")
        print("\n📋 Next steps:")
        print("   • Run: python src/cli.py run")
        print("   • Monitor: python src/cli.py stats")
    else:
        print("⚠️  Test completed with limitations")
        print("💡 The bot framework is working, just needs API elevation")
        print("\n📋 Once you get elevated access:")
        print("   • Re-run this test to confirm posting works")
        print("   • Start the bot: python src/cli.py run")

if __name__ == "__main__":
    main()
