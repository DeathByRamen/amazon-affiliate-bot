#!/usr/bin/env python3
"""
Test actual Keepa API calls to understand the correct interface
"""

import os
import sys
from dotenv import load_dotenv
import keepa

# Load environment variables
load_dotenv()

def test_keepa_api():
    """Test the raw Keepa API to understand correct parameters"""
    print("🧪 Testing Raw Keepa API")
    print("=" * 30)
    
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    try:
        # Initialize raw Keepa API
        api = keepa.Keepa(api_key)
        
        print("🔗 Testing API connection...")
        tokens = api.tokens_left
        print(f"📊 Tokens left: {tokens}")
        
        # Try to see what methods are available
        print("\n📋 Available methods:")
        methods = [method for method in dir(api) if not method.startswith('_')]
        for method in methods[:10]:  # Show first 10
            print(f"   - {method}")
        
        # Test the deals method signature
        print(f"\n🔍 Testing deals method...")
        
        # Try with minimal parameters first
        try:
            deals_result = api.deals()
            print(f"✅ Basic deals() call worked: {type(deals_result)}")
            if hasattr(deals_result, 'get'):
                print(f"   Keys: {list(deals_result.keys()) if deals_result else 'None'}")
        except Exception as e:
            print(f"❌ Basic deals() failed: {e}")
        
        # Try to find products with query method instead
        print(f"\n🔍 Testing query method for a specific product...")
        try:
            # Test with a known ASIN
            test_asin = "B08N5WRWNW"  # Example ASIN
            product_result = api.query(test_asin, domain="US", history=False)
            
            if product_result:
                print(f"✅ Product query worked! Found {len(product_result)} products")
                product = product_result[0]
                title = product.get('title', 'No title')
                print(f"   Example product: {title[:50]}...")
            else:
                print("⚠️  Product query returned empty")
                
        except Exception as e:
            print(f"❌ Product query failed: {e}")
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        print(f"   Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_keepa_api()