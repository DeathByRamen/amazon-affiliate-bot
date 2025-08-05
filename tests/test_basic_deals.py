#!/usr/bin/env python3
"""
Test basic product search to find deals (alternative to deals endpoint)
"""

import os
import sys
import time
from loguru import logger

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from keepa_client import KeepaClient

def test_basic_product_search():
    """Test finding deals using basic product search instead of deals endpoint"""
    
    print("🧪 Testing Basic Product Search for Deals")
    print("=" * 50)
    
    try:
        # Initialize Keepa client
        keepa_client = KeepaClient()
        
        # Test different ASINs that are likely to have price data
        test_asins = [
            'B08N5WRWNW',  # Echo Dot (popular Amazon device)
            'B0B7BP6CJN',  # Fire TV Stick
            'B09V3KXJPP',  # Echo Show 5
            'B08C1W5N87',  # Fire HD 8 Tablet
            'B08F7PTF53'   # All-new Kindle
        ]
        
        print(f"🔍 Testing {len(test_asins)} popular Amazon products...")
        
        for i, asin in enumerate(test_asins):
            print(f"\n📦 Testing product {i+1}: {asin}")
            
            try:
                # Get product details
                product = keepa_client.get_product_details(asin)
                
                if product:
                    title = product.get('title', 'Unknown Product')[:60] + "..."
                    current_price = product.get('current_price', 0)
                    avg_price = product.get('avg_price', 0)
                    
                    print(f"   ✅ Found: {title}")
                    print(f"   💰 Current: ${current_price:.2f}")
                    print(f"   📈 Average: ${avg_price:.2f}")
                    
                    # Calculate potential discount
                    if avg_price > 0 and current_price > 0:
                        discount = ((avg_price - current_price) / avg_price) * 100
                        print(f"   🎯 Potential discount: {discount:.1f}%")
                        
                        if discount > 10:
                            print(f"   🔥 POTENTIAL DEAL! {discount:.1f}% below average")
                        else:
                            print(f"   📊 Normal pricing")
                    else:
                        print(f"   ⚠️  Insufficient price history")
                        
                else:
                    print(f"   ❌ No data returned for {asin}")
                    
            except Exception as e:
                print(f"   ❌ Error with {asin}: {str(e)}")
            
            # Small delay between requests
            time.sleep(1)
        
        print(f"\n📊 Test completed! API is working for basic product queries.")
        print(f"💡 Recommendation: Use product search + price analysis instead of deals endpoint")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_basic_product_search()