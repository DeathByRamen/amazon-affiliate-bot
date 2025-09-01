#!/usr/bin/env python3
"""
Demo script for Twitter posting functionality
Shows how the bot posts beauty deals to Twitter
"""

import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def demo_tweet_formats():
    """Demo different tweet formats"""
    print("🐦 Twitter Posting Demo")
    print("=" * 60)
    
    # Sample beauty deals
    beauty_deals = [
        {
            'title': 'Fenty Beauty Pro Filt\'r Soft Matte Longwear Foundation',
            'asin': 'B075NVR28D',
            'discount_percent': 25,
            'original_price': 39.00,
            'current_price': 29.25,
            'brand': 'Fenty Beauty',
            'category': 'Beauty & Personal Care',
            'rating': 4.3,
            'review_count': 2847
        },
        {
            'title': 'CeraVe Moisturizing Cream for Normal to Dry Skin',
            'asin': 'B00TTD9BRC',
            'discount_percent': 30,
            'original_price': 16.99,
            'current_price': 11.89,
            'brand': 'CeraVe',
            'category': 'Beauty & Personal Care',
            'rating': 4.5,
            'review_count': 47891
        },
        {
            'title': 'Urban Decay Naked3 Eyeshadow Palette',
            'asin': 'B00FHOF4E6',
            'discount_percent': 35,
            'original_price': 54.00,
            'current_price': 35.10,
            'brand': 'Urban Decay',
            'category': 'Beauty & Personal Care',
            'rating': 4.4,
            'review_count': 8234
        }
    ]
    
    try:
        from twitter_client import TwitterClient
        client = TwitterClient()
        
        print("💄 Beauty Tweet Examples:")
        print("=" * 60)
        
        for i, deal in enumerate(beauty_deals, 1):
            print(f"\n📋 Example {i}:")
            print(f"Product: {deal['title']}")
            print(f"Deal: {deal['discount_percent']}% off (${deal['original_price']:.2f} → ${deal['current_price']:.2f})")
            print(f"Savings: ${deal['original_price'] - deal['current_price']:.2f}")
            
            # Generate beauty tweet
            tweet_content = client._create_beauty_tweet_content(deal)
            print(f"\n🐦 Tweet Content ({len(tweet_content)}/280 chars):")
            print("-" * 50)
            print(tweet_content)
            print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating demo tweets: {str(e)}")
        return False

def demo_rate_limiting():
    """Demo rate limiting features"""
    print("\n⏱️  Rate Limiting Demo")
    print("=" * 60)
    
    try:
        from twitter_client import TwitterClient
        client = TwitterClient()
        
        print("📊 Current Rate Limiting Status:")
        print(f"   Tweets posted today: {client.tweets_posted_today}")
        print(f"   Max tweets per hour: {client.api._session.params.get('count', 'Not set')}")
        print(f"   Minimum interval: {client.min_tweet_interval} seconds ({client.min_tweet_interval/60:.1f} minutes)")
        print(f"   Can post now: {'✅ Yes' if client.can_post_tweet() else '❌ No'}")
        
        if client.last_tweet_time:
            time_since_last = (datetime.utcnow() - client.last_tweet_time).total_seconds()
            print(f"   Time since last tweet: {time_since_last:.0f} seconds")
        else:
            print(f"   Last tweet time: Never")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking rate limits: {str(e)}")
        return False

def demo_affiliate_links():
    """Demo affiliate link generation"""
    print("\n🔗 Affiliate Link Demo")
    print("=" * 60)
    
    try:
        from twitter_client import TwitterClient
        from config import config
        
        client = TwitterClient()
        
        sample_asins = [
            'B075NVR28D',  # Fenty Foundation
            'B00TTD9BRC',  # CeraVe Cream
            'B00FHOF4E6'   # Urban Decay Palette
        ]
        
        print("🔗 Generated Affiliate Links:")
        for asin in sample_asins:
            affiliate_url = client._create_affiliate_url(asin)
            print(f"   ASIN {asin}: {affiliate_url}")
        
        if config.AMAZON_AFFILIATE_TAG:
            print(f"\n✅ Using affiliate tag: {config.AMAZON_AFFILIATE_TAG}")
        else:
            print(f"\n⚠️  No affiliate tag configured - links won't generate commissions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating affiliate links: {str(e)}")
        return False

def demo_hashtags_and_emojis():
    """Demo hashtag and emoji usage"""
    print("\n#️⃣ Hashtags & Emojis Demo")
    print("=" * 60)
    
    beauty_emojis = ["✨", "💄", "🌟", "💅", "🌸", "💎", "🎀", "🦋"]
    beauty_hashtags = [
        "#BeautyDeals", "#MakeupSale", "#BeautyFinds", "#TheFrugalBeauty",
        "#BeautyOnABudget", "#SkincareDeals", "#AffordableBeauty",
        "#BeautyBargain", "#MakeupFinds", "#GlowForLess"
    ]
    
    print("💄 Beauty Emojis Used:")
    print("   " + " ".join(beauty_emojis))
    
    print("\n#️⃣ Beauty Hashtags Used:")
    for hashtag in beauty_hashtags:
        print(f"   {hashtag}")
    
    print("\n📊 Hashtag Strategy:")
    print("   • Mix general beauty terms with deal-specific terms")
    print("   • Include brand hashtag for trending brands")
    print("   • Use niche-specific tags (#TheFrugalBeauty)")
    print("   • Rotate hashtags to avoid spam detection")

def demo_posting_workflow():
    """Demo the complete posting workflow"""
    print("\n🔄 Complete Posting Workflow Demo")
    print("=" * 60)
    
    print("📋 Step-by-Step Process:")
    print("1. 🔍 Keepa finds deals → Filters by beauty keywords")
    print("2. 📊 Quality check → Rating, reviews, discount %")
    print("3. 💰 Price validation → Beauty price range ($20-$200)")
    print("4. ⏱️  Rate limit check → Max 10 tweets/hour, 5min spacing")
    print("5. ✨ Beauty tweet format → Special emojis & hashtags")
    print("6. 🔗 Affiliate link → Add Amazon affiliate tag")
    print("7. 🐦 Post to Twitter → Track engagement")
    print("8. 💾 Save to database → Analytics & history")
    
    print("\n🎯 Beauty-Specific Features:")
    print("   • Only beauty products get tweeted")
    print("   • Higher quality standards (4.0+ rating, 50+ reviews)")
    print("   • Beauty-specific price range validation")
    print("   • Beauty-themed emojis and hashtags")
    print("   • Niche-focused messaging")

def main():
    """Main demo function"""
    print("🚀 Amazon Affiliate Bot - Twitter Posting Demo")
    print("=" * 80)
    
    success_count = 0
    
    # Run all demos
    if demo_tweet_formats():
        success_count += 1
    
    if demo_rate_limiting():
        success_count += 1
    
    if demo_affiliate_links():
        success_count += 1
    
    demo_hashtags_and_emojis()  # Always succeeds
    success_count += 1
    
    demo_posting_workflow()  # Always succeeds
    success_count += 1
    
    print("\n" + "=" * 80)
    print(f"🎉 Demo Complete! ({success_count}/5 sections successful)")
    
    if success_count >= 4:
        print("✅ Twitter posting framework is ready!")
        print("\n📋 Next Steps:")
        print("1. Set up your Twitter API credentials in .env")
        print("2. Configure your Amazon affiliate tag")
        print("3. Run: python src/cli.py setup-twitter")
        print("4. Start posting: python src/cli.py run")
    else:
        print("⚠️  Some components need configuration")
        print("💡 Check your .env file and API credentials")

if __name__ == "__main__":
    main()
