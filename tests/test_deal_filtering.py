#!/usr/bin/env python3
"""
Test to see if deals are being parsed but then filtered out
"""

import os
import sys
from loguru import logger

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from keepa_client import KeepaClient

def test_deal_filtering():
    """Test if deals are being parsed but filtered out"""
    
    print("🔍 Testing Deal Parsing vs Filtering")
    print("=" * 50)
    
    try:
        keepa_client = KeepaClient()
        
        # Get minimal deals (no filters except price range)
        deal_parms = {
            'page': 0,
            'domainId': 1,
            'deltaPercentRange': [10, 100],  # 10-100% discount
            'currentRange': [1000, 30000],   # $10-300 price range
            'sortType': 15
        }
        
        print(f"📊 Testing with parameters: {deal_parms}")
        
        deals_response = keepa_client.api.deals(deal_parms)
        
        if not deals_response or 'dr' not in deals_response:
            print("❌ No response from API")
            return
            
        raw_deals = deals_response.get('dr', [])
        print(f"✅ Got {len(raw_deals)} raw deals from API")
        
        if len(raw_deals) == 0:
            print("❌ No raw deals returned")
            return
            
        # Test parsing
        parsed_count = 0
        valid_count = 0
        examples = []
        
        for i, deal in enumerate(raw_deals[:10]):  # Test first 10 deals
            parsed_deal = keepa_client._parse_deal(deal)
            
            if parsed_deal:
                parsed_count += 1
                is_valid = keepa_client._is_valid_deal(parsed_deal)
                
                if is_valid:
                    valid_count += 1
                
                # Keep first 3 examples for display
                if len(examples) < 3:
                    examples.append({
                        'index': i,
                        'parsed': parsed_deal,
                        'valid': is_valid
                    })
        
        print(f"\n📈 Results from first 10 deals:")
        print(f"   Raw deals: 10")
        print(f"   Successfully parsed: {parsed_count}")
        print(f"   Passed validation: {valid_count}")
        
        print(f"\n📋 Examples:")
        for example in examples:
            deal = example['parsed']
            print(f"\n   Deal {example['index']} ({'✅ VALID' if example['valid'] else '❌ INVALID'}):")
            print(f"      ASIN: {deal['asin']}")
            print(f"      Title: {deal['title'][:50]}...")
            print(f"      Current: ${deal['current_price']:.2f}")
            print(f"      Original: ${deal['original_price']:.2f}")
            print(f"      Discount: {deal['discount_percent']:.1f}%")
            print(f"      Sales Rank: {deal['sales_rank']}")
            print(f"      Rating: {deal['rating']}")
            print(f"      Reviews: {deal['review_count']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deal_filtering()