#!/usr/bin/env python3
"""
Direct test of Keepa deal fetching - bypasses token check
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from keepa_client import KeepaClient
    from config import config
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_deals_direct():
    """Test deal fetching directly, ignoring token count"""
    print("🧪 Direct Keepa Deal Test (bypassing token check)")
    print("=" * 50)
    
    # Check if API key is set
    if not config.KEEPA_API_KEY or config.KEEPA_API_KEY == "your_keepa_api_key_here":
        print("❌ KEEPA_API_KEY not set")
        return False
    
    try:
        # Initialize client
        print("🔗 Connecting to Keepa API...")
        client = KeepaClient()
        
        # Try to fetch deals directly (ignore token check)
        print("🛒 Attempting to fetch deals...")
        print("   (This will show if you actually have usable tokens)")
        
        deals = client.get_deals(
            deal_threshold=20,  # Lower threshold to find more deals
            price_range=(5, 100)  # Smaller price range for testing
        )
        
        print(f"📦 Result: Found {len(deals)} deals")
        
        if deals:
            print("\n🎉 SUCCESS! Your Keepa tokens are working!")
            print("\n🏆 Sample deals found:")
            print("-" * 60)
            
            for i, deal in enumerate(deals[:3], 1):  # Show top 3
                print(f"{i}. {deal['title'][:50]}...")
                print(f"   ASIN: {deal['asin']}")
                print(f"   Price: ${deal['original_price']:.2f} → ${deal['current_price']:.2f}")
                print(f"   Discount: {deal['discount_percent']:.1f}%")
                print(f"   Savings: ${deal['original_price'] - deal['current_price']:.2f}")
                print(f"   Category: {deal.get('category', 'N/A')}")
                if deal.get('brand'):
                    print(f"   Brand: {deal['brand']}")
                print("")
            
            return True
        else:
            print("ℹ️  No deals found with current criteria")
            print("   This could mean:")
            print("   - No deals matching the 20% discount + $5-$100 price range")
            print("   - Try different thresholds or price ranges")
            print("   - But your API tokens ARE working!")
            return True
            
    except Exception as e:
        error_msg = str(e).lower()
        
        if "token" in error_msg or "credit" in error_msg or "limit" in error_msg:
            print(f"❌ Token/Credit Error: {str(e)}")
            print("   Your API key works but tokens may not be available yet")
        elif "auth" in error_msg or "key" in error_msg:
            print(f"❌ Authentication Error: {str(e)}")
            print("   Check your API key is correct")
        else:
            print(f"❌ API Error: {str(e)}")
            print(f"   Error Type: {type(e).__name__}")
        
        return False


if __name__ == "__main__":
    success = test_deals_direct()
    print(f"\n{'✅ Test completed' if success else '❌ Test failed'}")