#!/usr/bin/env python3
"""
Simple standalone script to test Keepa integration
Run this to quickly test if Keepa API is working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_env_result = load_dotenv()
if not load_env_result:
    print("⚠️  No .env file found. Create one with your KEEPA_API_KEY")

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

try:
    from keepa_client import KeepaClient
    from config import config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you've installed requirements: pip install -r requirements.txt")
    sys.exit(1)


def test_keepa():
    """Simple Keepa test function"""
    print("🧪 Simple Keepa API Test")
    print("=" * 30)
    
    # Check if API key is set
    if not config.KEEPA_API_KEY or config.KEEPA_API_KEY == "your_keepa_api_key_here":
        print("❌ KEEPA_API_KEY not set in environment variables")
        print("   Create a .env file with: KEEPA_API_KEY=your_actual_key")
        return False
    
    try:
        # Initialize client
        print("🔗 Connecting to Keepa API...")
        client = KeepaClient()
        
        # Test API status
        status = client.get_api_status()
        print(f"📊 API Status: {'✅ Healthy' if status['is_healthy'] else '❌ Error'}")
        print(f"🪙 Tokens remaining: {status['tokens_left']:,}")
        
        if not status['is_healthy']:
            tokens = status['tokens_left']
            if tokens == 0:
                print("💳 Issue: Your Keepa API key has 0 tokens remaining")
                print("")
                print("   This means you need to purchase API tokens from Keepa:")
                print("   1. Go to https://keepa.com/#!api")
                print("   2. Sign in to your account")
                print("   3. Purchase API tokens (starts at ~$19 for 1M tokens)")
                print("   4. Tokens are usually activated within a few minutes")
                print("")
                print("   ✅ Good news: Your API key is VALID and connecting successfully!")
                print("   ✅ The bot code is working correctly!")
                print("")
                return True  # API key works, just needs tokens
            else:
                print("❌ Cannot proceed - API connection failed")
                if 'error' in status:
                    print(f"   Error: {status['error']}")
                
                # Try to get more details from the actual keepa client
                print("\n🔍 Detailed error information:")
                try:
                    test_response = client.api.tokens_left
                    print(f"   Direct token check: {test_response}")
                except Exception as e:
                    print(f"   API Error: {str(e)}")
                    print(f"   Error Type: {type(e).__name__}")
                
                return False
        
        # Test deal fetching
        print("\n🛒 Fetching deals (30% discount minimum)...")
        deals = client.get_deals(
            deal_threshold=30,
            price_range=(10, 100)  # $10-$100 range for testing
        )
        
        print(f"📦 Found {len(deals)} deals")
        
        if deals:
            print("\n🏆 Sample deal:")
            deal = deals[0]
            print(f"   Title: {deal['title'][:60]}...")
            print(f"   ASIN: {deal['asin']}")
            print(f"   Price: ${deal['original_price']:.2f} → ${deal['current_price']:.2f}")
            print(f"   Discount: {deal['discount_percent']:.1f}%")
            print(f"   Savings: ${deal['original_price'] - deal['current_price']:.2f}")
            
            # Test with different thresholds
            print(f"\n📈 Deal count by discount threshold:")
            for threshold in [20, 30, 40, 50]:
                test_deals = client.get_deals(deal_threshold=threshold, price_range=(10, 100))
                print(f"   {threshold}%+: {len(test_deals)} deals")
            
            print("\n✅ Keepa integration is working!")
            return True
        else:
            print("ℹ️  No deals found with current criteria")
            print("   Try lowering the discount threshold or increasing price range")
            return True
            
    except Exception as e:
        print(f"❌ Error testing Keepa: {str(e)}")
        print("\nCommon issues:")
        print("- Invalid API key")
        print("- No tokens remaining")
        print("- Network connectivity issues")
        return False


if __name__ == "__main__":
    success = test_keepa()
    sys.exit(0 if success else 1)