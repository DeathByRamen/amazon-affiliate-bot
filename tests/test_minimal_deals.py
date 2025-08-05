#!/usr/bin/env python3
"""
Test the deals endpoint with absolute minimal parameters to verify it can return deals
"""

import os
import sys
from loguru import logger

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from keepa_client import KeepaClient

def test_minimal_deals():
    """Test deals endpoint with absolute minimal parameters"""
    
    print("🧪 Testing Deals Endpoint - Minimal Parameters")
    print("=" * 55)
    
    try:
        keepa_client = KeepaClient()
        
        # Test 1: Absolutely minimal parameters
        print("🔍 Test 1: Absolute minimal parameters")
        print("   - No filters, just get ANY deals")
        
        minimal_params = {
            'page': 0,
            'domainId': 1,
            'sortType': 15
        }
        
        response = keepa_client.api.deals(minimal_params)
        
        if response and 'dr' in response:
            deals_count = len(response['dr'])
            print(f"   ✅ Found {deals_count} deals with minimal parameters!")
            
            if deals_count > 0:
                # Show first deal
                first_deal = response['dr'][0]
                title = first_deal.get('title', 'Unknown')[:60] + "..."
                print(f"   📦 Sample deal: {title}")
                
                # Check what fields are available
                available_fields = list(first_deal.keys())
                print(f"   📊 Available fields: {', '.join(available_fields[:10])}...")
                
            return True
        else:
            print("   ❌ No response or no 'dr' field in response")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_deals_with_single_filter():
    """Test with single filters to see what breaks"""
    
    print("\n🔍 Test 2: Single filter tests")
    print("   Testing each filter individually...")
    
    try:
        keepa_client = KeepaClient()
        
        # Test individual filters
        filters_to_test = [
            ({'page': 0, 'domainId': 1, 'sortType': 15, 'deltaPercentRange': [10, 100]}, "10%+ discount"),
            ({'page': 0, 'domainId': 1, 'sortType': 15, 'currentRange': [1000, 50000]}, "$10-500 price"),
            ({'page': 0, 'domainId': 1, 'sortType': 15, 'salesRankRange': [1, 100000]}, "Sales rank 1-100k"),
            ({'page': 0, 'domainId': 1, 'sortType': 15, 'minRating': 30}, "3.0+ rating"),
        ]
        
        for params, description in filters_to_test:
            try:
                response = keepa_client.api.deals(params)
                deals_count = len(response.get('dr', [])) if response else 0
                print(f"   - {description}: {deals_count} deals")
            except Exception as e:
                print(f"   - {description}: ERROR - {str(e)}")
                
    except Exception as e:
        print(f"   ❌ Test setup failed: {str(e)}")

if __name__ == "__main__":
    print("Testing if deals endpoint can return ANY deals at all...\n")
    
    success = test_minimal_deals()
    
    if success:
        test_deals_with_single_filter()
        print("\n✅ Deals endpoint is working! Issue is with parameter restrictions.")
        print("💡 Try relaxing filters further or check current market conditions.")
    else:
        print("\n❌ Deals endpoint access issue. May require premium plan.")