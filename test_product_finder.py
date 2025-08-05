#!/usr/bin/env python3
"""
Test Keepa product_finder method for finding deals
"""

import os
import sys
from dotenv import load_dotenv
import keepa

# Load environment variables
load_dotenv()

def test_product_finder():
    """Test using product_finder to find deals"""
    print("🧪 Testing Keepa Product Finder for Deals")
    print("=" * 40)
    
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    try:
        # Initialize Keepa API
        api = keepa.Keepa(api_key)
        
        print("🔗 API Connected")
        print(f"📊 Tokens: {api.tokens_left}")
        
        # Use product_finder to search for products with deals
        print(f"\n🔍 Searching for products with price drops...")
        
        selection = {
            'discountPercent': [30, 100],  # 30% to 100% discount
            'current': [500, 5000],        # $5 to $50 (in cents)
            'salesRank': [1, 10000],       # Good sales rank
        }
        
        # Search in Electronics category (id: 172282) 
        result = api.product_finder(selection, categories=[172282])
        
        if result and hasattr(result, 'get'):
            products = result.get('products', [])
            print(f"📦 Found {len(products)} products with deals!")
            
            if products:
                print(f"\n🏆 Top deals found:")
                print("-" * 60)
                
                for i, product in enumerate(products[:5], 1):  # Show top 5
                    title = product.get('title', 'No title')
                    asin = product.get('asin', 'No ASIN')
                    
                    # Get current price (index 1 is current price)
                    current_price = 0
                    if 'stats' in product and 'current' in product['stats']:
                        current_price = product['stats']['current'][1] / 100 if product['stats']['current'][1] else 0
                    
                    print(f"{i}. {title[:50]}...")
                    print(f"   ASIN: {asin}")
                    print(f"   Current Price: ${current_price:.2f}")
                    
                    # Try to get discount info
                    if 'stats' in product:
                        stats = product['stats']
                        if 'avg30' in stats and stats['avg30'][1]:
                            avg_price = stats['avg30'][1] / 100
                            discount = ((avg_price - current_price) / avg_price * 100) if avg_price > 0 else 0
                            print(f"   30-day avg: ${avg_price:.2f}")
                            print(f"   Discount: {discount:.1f}%")
                    
                    print("")
                
                return True
            else:
                print("   No products found with current criteria")
        else:
            print(f"⚠️  Unexpected result format: {type(result)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        
        # Show more details if it's a specific error
        if "token" in str(e).lower():
            print("   This looks like a token/credit issue")
        elif "auth" in str(e).lower():
            print("   This looks like an authentication issue")
    
    return False


if __name__ == "__main__":
    success = test_product_finder()
    print(f"\n{'✅ Test completed' if success else '❌ Test failed'}")