# Testing Keepa Integration Only

This guide helps you test just the Keepa API integration without requiring Twitter setup.

## Quick Setup for Keepa Testing

### 1. Install Dependencies
```bash
cd hustle/keepa
pip install -r requirements.txt
```

### 2. Create Environment File
Create a `.env` file with minimal configuration:

```env
# Keepa API Configuration (REQUIRED - get from keepa.com)
KEEPA_API_KEY=your_actual_keepa_api_key_here

# Bot Configuration for testing (adjust as needed)
MIN_DISCOUNT_PERCENT=20
MIN_PRICE_DROP=5.00
MAX_PRODUCT_PRICE=200.00

# Database (SQLite for testing)
DATABASE_URL=sqlite:///test_deals.db

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=testing

# Dummy Twitter credentials (required by config but not used)
TWITTER_API_KEY=dummy
TWITTER_API_SECRET=dummy
TWITTER_ACCESS_TOKEN=dummy
TWITTER_ACCESS_TOKEN_SECRET=dummy
AMAZON_AFFILIATE_TAG=dummy-tag
```

### 3. Initialize Database
```bash
python cli.py init
```

### 4. Test Keepa Integration

#### Option A: Quick Keepa Test
```bash
python cli.py test-keepa
```
This runs a comprehensive test of:
- API connection and token status
- Deal detection with different discount thresholds
- Product lookup functionality

#### Option B: Deal Detection Test (No Twitter)
```bash
python cli.py test --skip-twitter
```
This tests:
- Keepa API connection
- Deal fetching with your configured filters
- Quality filtering logic
- Shows actual deals found

#### Option C: Check Configuration
```bash
python cli.py status --check-apis
```

## What You'll See

### Successful Keepa Test Output:
```
🧪 Testing Keepa API Integration
========================================
1️⃣ Testing API connection...
   Status: ✅ Healthy
   Tokens remaining: 1000000

2️⃣ Testing deal detection...
   Testing 20% discount threshold...
   Found: 15 deals
   Testing 30% discount threshold...
   Found: 8 deals
   
   📋 Sample deal at 30% threshold:
      Title: Example Product Name...
      ASIN: B123456789
      Price: $49.99 → $29.99
      Discount: 40.0%

3️⃣ Testing product lookup...
   ✅ Product lookup successful for B08N5WRWNW

✅ Keepa integration test completed!
```

### Deal Detection Test Output:
```
🧪 Running Keepa-only test (no Twitter posting)...
🔍 Testing Keepa API connection...
   Tokens remaining: 1000000
   API healthy: ✅

🛒 Fetching deals from Keepa...
📦 Raw deals found: 12

🏆 Top 5 Deals Found:
--------------------------------------------------------------------------------
1. Amazing Product That's On Sale Today...
   ASIN: B0123456789
   Price: $79.99 → $39.99
   Discount: 50.0%
   Savings: $40.00
   Category: Electronics

[... more deals ...]

✅ Keepa integration working correctly!
📊 Deals passing quality filters: 8/12
```

## Troubleshooting

### "Configuration error" 
Make sure you have a valid Keepa API key in your `.env` file.

### "API is not healthy"
- Check your Keepa API key is correct
- Verify you have remaining token balance
- Check internet connectivity

### "No deals found"
- Try lowering `MIN_DISCOUNT_PERCENT` (e.g., 15 or 20)
- Increase `MAX_PRODUCT_PRICE` (e.g., 500)
- Adjust price range in the test

### Want to see more details?
Add the verbose flag:
```bash
python cli.py -v test-keepa
```

## Next Steps

Once Keepa is working correctly:
1. Set up Twitter API credentials
2. Test with `python cli.py test` (full integration)
3. Run the full bot with `python cli.py run`

## Testing with Different Parameters

You can temporarily modify the test parameters in the CLI commands:
- Edit `deal_threshold` values in `test-keepa` command
- Adjust `price_range` for different product price ranges
- Modify discount thresholds to see more/fewer deals