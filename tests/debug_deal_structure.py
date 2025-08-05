#!/usr/bin/env python3
"""
Debug script to check the actual data structure of Keepa deals
"""

import os
import sys
import json
from loguru import logger

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from keepa_client import KeepaClient

def debug_deal_structure():
    """Debug the actual structure of deal data from Keepa"""
    
    print("🔍 Debugging Keepa Deal Data Structure")
    print("=" * 50)
    
    try:
        keepa_client = KeepaClient()
        
        # Get minimal deals
        minimal_params = {
            'page': 0,
            'domainId': 1,
            'sortType': 15
        }
        
        response = keepa_client.api.deals(minimal_params)
        
        if response and 'dr' in response:
            deals_count = len(response['dr'])
            print(f"✅ Found {deals_count} deals from API")
            
            if deals_count > 0:
                # Look at first deal structure
                first_deal = response['dr'][0]
                print(f"\n📊 First Deal Structure:")
                print(f"   Keys: {list(first_deal.keys())}")
                
                # Check specific fields that are causing errors
                problematic_fields = ['current', 'avg', 'rating', 'salesRank', 'reviewCount']
                
                for field in problematic_fields:
                    if field in first_deal:
                        value = first_deal[field]
                        print(f"   {field}: {type(value).__name__} = {value}")
                        
                        if isinstance(value, list):
                            print(f"      └─ List length: {len(value)}")
                            if len(value) > 0:
                                print(f"      └─ First item type: {type(value[0]).__name__}")
                                print(f"      └─ Last item type: {type(value[-1]).__name__}")
                    else:
                        print(f"   {field}: NOT FOUND")
                
                print(f"\n🔍 Full first deal (truncated):")
                # Show full structure but limit output
                deal_str = json.dumps(first_deal, indent=2, default=str)[:1000]
                print(deal_str)
                if len(deal_str) >= 1000:
                    print("... (truncated)")
                    
        else:
            print("❌ No deals in response")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_deal_structure()