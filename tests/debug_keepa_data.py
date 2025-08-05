#!/usr/bin/env python3
"""
Debug Keepa data structure to understand the format
"""

import os
import sys
from dotenv import load_dotenv
import keepa
import json

# Load environment variables
load_dotenv()

def debug_keepa_data():
    """Debug the actual Keepa data structure"""
    print("🔍 Debugging Keepa Data Structure")
    print("=" * 35)
    
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    try:
        # Initialize Keepa API
        api = keepa.Keepa(api_key)
        
        print("🔗 API Connected")
        print(f"📊 Tokens: {api.tokens_left}")
        
        # Query a single product to see the data structure
        test_asin = "B08N5WRWNW"
        print(f"\n🔍 Debugging product: {test_asin}")
        
        products = api.query(test_asin, domain="US", history=True, stats=True)
        
        if products and len(products) > 0:
            product = products[0]
            
            print(f"✅ Product retrieved successfully!")
            print(f"📦 Title: {product.get('title', 'No title')}")
            
            # Show the main keys in the product data
            print(f"\n📋 Main data keys:")
            main_keys = list(product.keys())
            for i, key in enumerate(main_keys):
                value = product[key]
                value_type = type(value).__name__
                
                if isinstance(value, (list, dict)):
                    length = len(value) if hasattr(value, '__len__') else 'N/A'
                    print(f"   {key}: {value_type} (length: {length})")
                else:
                    print(f"   {key}: {value_type} = {str(value)[:50]}...")
            
            # Focus on stats if it exists
            if 'stats' in product:
                print(f"\n📊 Stats structure:")
                stats = product['stats']
                print(f"   Stats type: {type(stats)}")
                if isinstance(stats, dict):
                    for key, value in stats.items():
                        print(f"   {key}: {type(value).__name__} = {str(value)[:100]}...")
            
            # Focus on data if it exists
            if 'data' in product:
                print(f"\n💾 Data structure:")
                data = product['data']
                print(f"   Data type: {type(data)}")
                if isinstance(data, dict):
                    print(f"   Data keys: {list(data.keys())}")
                    # Look at the first few entries
                    for key, value in list(data.items())[:3]:
                        print(f"   {key}: {type(value).__name__} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                        if isinstance(value, list) and len(value) > 0:
                            print(f"      First few items: {value[:6]}...")
            
            # Try to find price information
            print(f"\n💰 Looking for price information:")
            price_fields = ['price', 'current', 'amazon', 'lastOffersUpdate', 'lastPriceChange']
            for field in price_fields:
                if field in product:
                    print(f"   {field}: {product[field]}")
            
            # Look in CSV data for prices (if exists)
            if 'csv' in product:
                print(f"\n📊 CSV data structure:")
                csv_data = product['csv']
                print(f"   CSV type: {type(csv_data)}")
                if isinstance(csv_data, dict):
                    for key, value in csv_data.items():
                        print(f"   {key}: {str(value)[:100]}...")
            
            return True
        else:
            print("❌ No products retrieved")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    debug_keepa_data()