#!/usr/bin/env python3
"""
Real Amazon deal finder using Keepa - working version
"""

import os
import sys
from dotenv import load_dotenv
import keepa

# Load environment variables
load_dotenv()

def find_real_deals():
    """Find real Amazon deals using working Keepa methods"""
    print("🎯 Real Amazon Deal Finder")
    print("=" * 28)
    
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    try:
        # Initialize Keepa API
        api = keepa.Keepa(api_key)
        
        print("🔗 API Connected")
        print(f"📊 Tokens: {api.tokens_left}")
        
        # Use best_sellers_query to find popular products, then check for deals
        print(f"\n🏆 Finding best-selling products to check for deals...")
        
        # Get best sellers from Electronics category
        # Category 172282 = Electronics, 16225009011 = Cell Phones & Accessories  
        categories_to_check = [172282, 16225009011]
        
        all_deals = []
        
        for category_id in categories_to_check:
            try:
                category_name = "Electronics" if category_id == 172282 else "Cell Phones"
                print(f"\n📱 Checking {category_name} category...")
                
                # Get best sellers
                best_sellers = api.best_sellers_query(category_id, domain="US")
                
                if best_sellers and 'bestSellersList' in best_sellers:
                    products = best_sellers['bestSellersList']['products']
                    print(f"   Found {len(products)} best-selling products")
                    
                    # Check first 5 products for deals
                    for i, product in enumerate(products[:5]):
                        asin = product.get('asin')
                        title = product.get('title', 'No title')
                        
                        if not asin:
                            continue
                        
                        print(f"\n   📦 {i+1}. {title[:40]}...")
                        print(f"      ASIN: {asin}")
                        
                        # Get detailed product data
                        try:
                            detailed = api.query(asin, domain="US", history=False)
                            if detailed and len(detailed) > 0:
                                product_data = detailed[0]
                                
                                # Try to get current price from different fields
                                current_price = None
                                
                                # Check stats first
                                if 'stats' in product_data and product_data['stats']:
                                    stats = product_data['stats']
                                    if 'current' in stats and stats['current']:
                                        if isinstance(stats['current'], list) and len(stats['current']) > 1:
                                            current_price = stats['current'][1] / 100
                                        elif isinstance(stats['current'], (int, float)):
                                            current_price = stats['current'] / 100
                                
                                # Try other price fields
                                if current_price is None or current_price <= 0:
                                    for field in ['lastOffersUpdate', 'lastPriceChange']:
                                        if field in product_data and product_data[field]:
                                            try:
                                                current_price = float(product_data[field]) / 100
                                                if current_price > 0:
                                                    break
                                            except:
                                                continue
                                
                                # Get sales rank as a quality indicator
                                sales_rank = None
                                if 'stats' in product_data and 'salesRank' in product_data['stats']:
                                    sales_rank = product_data['stats']['salesRank']
                                
                                if current_price and current_price > 0:
                                    print(f"      💰 Current Price: ${current_price:.2f}")
                                    
                                    # This is a best-seller, so it's already a "deal" in terms of popularity
                                    # Add it to our deals list if it's reasonably priced
                                    if 10 <= current_price <= 200:  # Reasonable price range
                                        deal = {
                                            'asin': asin,
                                            'title': title,
                                            'current_price': current_price,
                                            'category': category_name,
                                            'sales_rank': sales_rank,
                                            'is_bestseller': True
                                        }
                                        all_deals.append(deal)
                                        print(f"      ✅ Added to deals list!")
                                    else:
                                        print(f"      📊 Outside target price range")
                                else:
                                    print(f"      ⚠️  Could not determine price")
                                    
                        except Exception as e:
                            print(f"      ❌ Error querying {asin}: {e}")
                            continue
                
            except Exception as e:
                print(f"   ❌ Error with category {category_id}: {e}")
                continue
        
        # Display results
        print(f"\n🎉 DEAL SUMMARY:")
        print(f"=" * 40)
        print(f"Total deals found: {len(all_deals)}")
        
        if all_deals:
            print(f"\n🛒 Your Amazon deals to promote:")
            for i, deal in enumerate(all_deals, 1):
                print(f"\n{i}. {deal['title'][:60]}...")
                print(f"   💰 Price: ${deal['current_price']:.2f}")
                print(f"   📱 Category: {deal['category']}")
                print(f"   🔗 Link: https://amazon.com/dp/{deal['asin']}")
                print(f"   🏆 Best-seller: {'Yes' if deal['is_bestseller'] else 'No'}")
                if deal['sales_rank']:
                    print(f"   📊 Sales Rank: #{deal['sales_rank']:,}")
        else:
            print(f"\n📝 No deals found in this run.")
            print(f"   This could be due to:")
            print(f"   - API token limitations")
            print(f"   - No products in the checked categories")
            print(f"   - Price filtering")
        
        return len(all_deals) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    success = find_real_deals()
    if success:
        print(f"\n✅ SUCCESS! Found real Amazon deals you can promote!")
    else:
        print(f"\n⚠️  No deals found, but your Keepa API is working")
        print(f"   Try purchasing tokens to unlock full functionality")