#!/usr/bin/env python3
"""
Test script for optimized deal parameters
Tests both primary and fallback parameter sets to ensure we're getting deals
"""

import os
import sys
import time
from loguru import logger
from tabulate import tabulate

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

from keepa_client import KeepaClient
from config import config

def test_optimized_parameters():
    """Test the new optimized parameters vs old restrictive ones"""
    
    print("🧪 Testing Optimized Deal Parameters")
    print("=" * 50)
    
    try:
        # Initialize Keepa client
        keepa_client = KeepaClient()
        
        # Check API status first
        status = keepa_client.get_api_status()
        print(f"   Keepa API Status: {'✅ Healthy' if status['is_healthy'] else '❌ Unhealthy'}")
        print(f"   Tokens remaining: {status['tokens_left']}")
        print()
        
        if status['tokens_left'] is None:
            print("⚠️  Token count unavailable, but continuing test...")
        elif not status['is_healthy']:
            print("⚠️  API shows unhealthy but continuing test (tokens might still work)...")
        
        # Test results storage
        results = []
        
        # Test 1: Old restrictive parameters
        print("🔴 Test 1: OLD Restrictive Parameters")
        print("   - 20% discount, $20-200, 50k rank, 100+ reviews, 4.0+ rating")
        start_time = time.time()
        
        old_deals = keepa_client.get_deals(
            deal_threshold=20,
            price_range=(20, 200),
            max_sales_rank=50000,
            min_review_count=100,
            min_rating=4.0,
            use_fallback=False  # Don't use fallback for this test
        )
        
        old_time = time.time() - start_time
        results.append(["Old Restrictive", len(old_deals), f"{old_time:.1f}s", "20%", "$20-200", "50k", "100", "4.0"])
        print(f"   Result: {len(old_deals)} deals found in {old_time:.1f}s")
        print()
        
        # Test 2: New optimized parameters  
        print("🟡 Test 2: NEW Optimized Parameters (Primary)")
        print("   - 15% discount, $15-300, 100k rank, 25+ reviews, 3.5+ rating")
        start_time = time.time()
        
        new_deals = keepa_client.get_deals(
            deal_threshold=15,
            price_range=(15, 300),
            max_sales_rank=100000,
            min_review_count=25,
            min_rating=3.5,
            use_fallback=False  # Test primary only first
        )
        
        new_time = time.time() - start_time
        results.append(["New Primary", len(new_deals), f"{new_time:.1f}s", "15%", "$15-300", "100k", "25", "3.5"])
        print(f"   Result: {len(new_deals)} deals found in {new_time:.1f}s")
        print()
        
        # Test 3: With fallback enabled
        print("🟢 Test 3: NEW Parameters + Fallback")
        print("   - Primary + fallback to 10% discount, 500k rank, 10+ reviews")
        start_time = time.time()
        
        fallback_deals = keepa_client.get_deals(
            deal_threshold=15,
            price_range=(15, 300),
            max_sales_rank=100000,
            min_review_count=25,
            min_rating=3.5,
            use_fallback=True  # Enable fallback
        )
        
        fallback_time = time.time() - start_time
        results.append(["New + Fallback", len(fallback_deals), f"{fallback_time:.1f}s", "15%→10%", "$15-300", "100k→500k", "25→10", "3.5"])
        print(f"   Result: {len(fallback_deals)} deals found in {fallback_time:.1f}s")
        print()
        
        # Test 4: Just fallback parameters (most lenient)
        print("🔵 Test 4: Fallback Parameters Only")
        print("   - 10% discount, $15-300, 500k rank, 10+ reviews")
        start_time = time.time()
        
        lenient_deals = keepa_client.get_deals(
            deal_threshold=config.FALLBACK_MIN_DISCOUNT,
            price_range=(15, 300),
            max_sales_rank=config.FALLBACK_MAX_SALES_RANK,
            min_review_count=config.FALLBACK_MIN_REVIEW_COUNT,
            min_rating=3.0,  # Even more lenient
            use_fallback=False
        )
        
        lenient_time = time.time() - start_time
        results.append(["Fallback Only", len(lenient_deals), f"{lenient_time:.1f}s", "10%", "$15-300", "500k", "10", "3.0"])
        print(f"   Result: {len(lenient_deals)} deals found in {lenient_time:.1f}s")
        print()
        
        # Display results table
        print("📊 RESULTS SUMMARY")
        print("=" * 70)
        headers = ["Test", "Deals", "Time", "Discount", "Price", "Sales Rank", "Reviews", "Rating"]
        print(tabulate(results, headers=headers, tablefmt="grid"))
        print()
        
        # Analysis
        print("📈 ANALYSIS")
        print("-" * 30)
        
        if len(old_deals) == 0:
            print("✅ CONFIRMED: Old parameters too restrictive (0 deals)")
        else:
            print(f"⚠️  Old parameters found {len(old_deals)} deals")
            
        if len(new_deals) > len(old_deals):
            print(f"✅ IMPROVEMENT: New parameters found {len(new_deals) - len(old_deals)} more deals")
        
        if len(fallback_deals) > len(new_deals):
            print(f"✅ FALLBACK WORKING: +{len(fallback_deals) - len(new_deals)} deals with fallback")
            
        # Show sample deals if we found any
        if fallback_deals:
            print(f"\n📝 SAMPLE DEALS (showing first 3 of {len(fallback_deals)}):")
            for i, deal in enumerate(fallback_deals[:3]):
                print(f"   {i+1}. {deal.get('title', 'Unknown')[:60]}...")
                print(f"      💰 ${deal.get('current_price', 0):.2f} ({deal.get('discount_percent', 0):.0f}% off)")
                print(f"      ⭐ {deal.get('rating', 0):.1f}/5 ({deal.get('review_count', 0)} reviews)")
                print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 30)
        print("✅ Use the NEW optimized parameters as default")
        print("✅ Keep fallback system enabled for maximum deal volume")
        print("✅ Focus on 15%+ discounts for good conversion rates")
        print("✅ Expanded price range ($15-300) captures more opportunities")
        print("✅ Relaxed filters (100k rank, 25 reviews) ensure deal flow")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_optimized_parameters()