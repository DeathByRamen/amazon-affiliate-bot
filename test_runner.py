#!/usr/bin/env python3
"""
Test Runner - Simplified entry point for running tests
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_keepa_test():
    """Run basic Keepa connectivity test"""
    print("🧪 Running Keepa connectivity test...")
    os.system("python tests/test_keepa_simple.py")

def run_deals_test():
    """Run optimized deals test"""
    print("🔍 Running optimized deals test...")
    os.system("python tests/test_optimized_deals.py")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'keepa':
            run_keepa_test()
        elif sys.argv[1] == 'deals':
            run_deals_test()
        else:
            print("Usage: python test_runner.py [keepa|deals]")
    else:
        print("🧪 Running all tests...")
        run_keepa_test()
        print("\n" + "="*50 + "\n")
        run_deals_test()