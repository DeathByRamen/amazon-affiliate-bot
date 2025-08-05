#!/usr/bin/env python3
"""
Simple deal finder using Keepa query method
"""

import os
import sys
from dotenv import load_dotenv
import keepa

# Load environment variables
load_dotenv()

def find_deals_simple():
    """Find deals using basic Keepa query method"""
    print("🧪 Simple Deal Finder (using query method)")
    print("=" * 45)
    
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    try:
        # Initialize Keepa API
        api = keepa.Keepa(api_key)
        
        print("🔗 API Connected")
        print(f"📊 Tokens: {api.tokens_left}")
        
        # List of popular ASINs to check for deals (you can expand this)
        test_asins = [
            "B08N5WRWNW",  # Example ASIN
            "B09B8W5FW7",  # Another example
            "B07ZPKN6YR",  # Another example
        ]
        
        print(f"\n🔍 Checking {len(test_asins)} products for deals...")
        
        # Query products to see their price history
        products = api.query(test_asins, domain="US", history=True)
        
        if products:
            print(f"✅ Retrieved {len(products)} products!")
            deals_found = []
            
            for product in products:
                asin = product.get('asin', 'Unknown')
                title = product.get('title', 'No title')
                
                print(f"\n📦 Analyzing: {title[:50]}...")
                print(f"   ASIN: {asin}")
                
                # Get current price and price history
                stats = product.get('stats', {})
                
                # Try different ways to get pricing data
                current_price = 0
                avg30_price = 0
                avg90_price = 0
                
                # Method 1: stats object
                if stats:
                    if 'current' in stats and stats['current']:
                        current_price = stats['current'] / 100 if isinstance(stats['current'], (int, float)) else 0
                    if 'avg30' in stats and stats['avg30']:
                        avg30_price = stats['avg30'] / 100 if isinstance(stats['avg30'], (int, float)) else 0
                    if 'avg90' in stats and stats['avg90']:
                        avg90_price = stats['avg90'] / 100 if isinstance(stats['avg90'], (int, float)) else 0
                
                # Method 2: Direct price fields
                if current_price == 0 and 'data' in product:
                    # Try to get from CSV data (Keepa often stores price history as CSV)
                    csv_data = product['data']
                    if isinstance(csv_data, dict):
                        # Amazon price is usually index 0 (AMAZON)
                        if 0 in csv_data and csv_data[0]:
                            # Get last price (most recent)
                            prices = csv_data[0]
                            if prices and len(prices) >= 2:
                                # Prices are stored as [timestamp, price] pairs
                                current_price = prices[-1] / 100 if prices[-1] and prices[-1] > 0 else 0
                
                # Method 3: Try direct fields
                if current_price == 0:
                    for field in ['lastOffersUpdate', 'lastPriceChange']:
                        if field in product and product[field]:
                            try:
                                current_price = float(product[field]) / 100
                                break
                            except:
                                continue
                
                print(f"   Current Price: ${current_price:.2f}")
                print(f"   30-day avg: ${avg30_price:.2f}")
                print(f"   90-day avg: ${avg90_price:.2f}")
                
                # Calculate discount from 30-day average
                if avg30_price > 0 and current_price > 0:
                    discount_30 = ((avg30_price - current_price) / avg30_price * 100)
                    savings_30 = avg30_price - current_price
                    
                    print(f"   30-day discount: {discount_30:.1f}%")
                    print(f"   30-day savings: ${savings_30:.2f}")
                    
                    # Check if this is a good deal (>20% off and >$5 savings)
                    if discount_30 > 20 and savings_30 > 5:
                        print(f"   🔥 DEAL FOUND! {discount_30:.1f}% off!")
                        deals_found.append({
                            'asin': asin,
                            'title': title,
                            'current_price': current_price,
                            'avg_price': avg30_price,
                            'discount': discount_30,
                            'savings': savings_30
                        })
                    else:
                        print(f"   📊 Not a significant deal")
                else:
                    print(f"   ⚠️  Price data incomplete")
            
            # Summary
            print(f"\n📊 SUMMARY:")
            print(f"Products checked: {len(products)}")
            print(f"Deals found: {len(deals_found)}")
            
            if deals_found:
                print(f"\n🎉 DEALS FOUND:")
                for i, deal in enumerate(deals_found, 1):
                    print(f"{i}. {deal['title'][:40]}...")
                    print(f"   ${deal['avg_price']:.2f} → ${deal['current_price']:.2f}")
                    print(f"   {deal['discount']:.1f}% off (${deal['savings']:.2f} savings)")
                    print(f"   https://amazon.com/dp/{deal['asin']}")
                    print("")
            
            return len(deals_found) > 0
        else:
            print("❌ No products retrieved")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    success = find_deals_simple()
    print(f"\n{'✅ Found deals!' if success else '⚠️  No deals found'}")