# Twitter Setup Guide for Amazon Affiliate Bot

This guide will walk you through setting up Twitter API access and configuring your bot to post deals to Twitter.

## 🐦 Step 1: Create Twitter Developer Account

1. **Go to Twitter Developer Portal**: https://developer.twitter.com/en/portal/dashboard
2. **Apply for Developer Access**:
   - Click "Apply for a developer account"
   - Select "Making a bot" as your use case
   - Describe your bot: "Automated bot that posts Amazon deals and discounts with affiliate links to help users find savings"
   - Complete the application process

3. **Wait for Approval**: This can take a few hours to a few days

## 🔑 Step 2: Create Twitter App

Once your developer account is approved:

1. **Create New Project/App**:
   - Go to your Developer Dashboard
   - Click "Create Project" or "Create App"
   - Choose "Production" environment
   - Name your app (e.g., "TheFrugalBeautyBot")

2. **Configure App Settings**:
   - **App Name**: Your bot name (e.g., "TheFrugalBeautyBot")
   - **Description**: "Bot that finds and shares Amazon beauty deals with affiliate links"
   - **Website URL**: Your website or GitHub repo URL
   - **Terms of Service**: Link to your terms (if you have one)
   - **Privacy Policy**: Link to your privacy policy (if you have one)

## 📋 Step 3: Get API Credentials

1. **Generate API Keys**:
   - In your app dashboard, go to "Keys and Tokens"
   - Generate/Copy these 4 credentials:
     - **API Key** (Consumer Key)
     - **API Secret Key** (Consumer Secret)
     - **Access Token**
     - **Access Token Secret**

2. **Set Permissions**:
   - Go to "App Permissions"
   - Set to "Read and Write" (needed to post tweets)
   - Save changes

## ⚙️ Step 4: Configure Bot Environment

1. **Copy Environment Template**:
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file** with your credentials:
   ```bash
   # Twitter API Configuration
   TWITTER_API_KEY=your_api_key_here
   TWITTER_API_SECRET=your_api_secret_here  
   TWITTER_ACCESS_TOKEN=your_access_token_here
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
   
   # Amazon Affiliate Tag (get from Amazon Associates)
   AMAZON_AFFILIATE_TAG=your_affiliate_tag
   
   # Beauty-focused settings
   BEAUTY_ONLY_TWEETS=true
   BEAUTY_MIN_DISCOUNT=20.0
   BEAUTY_MIN_PRICE=20.0
   BEAUTY_MAX_PRICE=200.0
   ```

## 🧪 Step 5: Test Twitter Connection

Run the Twitter connection test:

```bash
python -c "
import sys
sys.path.append('src')
from twitter_client import TwitterClient
try:
    client = TwitterClient()
    info = client.get_account_info()
    print(f'✅ Connected to Twitter as @{info[\"username\"]}')
    print(f'📊 Followers: {info[\"followers_count\"]}')
    print(f'🐦 Tweets: {info[\"tweets_count\"]}')
except Exception as e:
    print(f'❌ Twitter connection failed: {e}')
"
```

## 📱 Step 6: Test Posting a Deal

Test posting (this will post a real tweet!):

```bash
python -c "
import sys
sys.path.append('src')
from twitter_client import TwitterClient

client = TwitterClient()
test_deal = {
    'title': 'Test Beauty Deal - Maybelline Mascara',
    'asin': 'B07XXXTEST',
    'discount_percent': 25,
    'original_price': 12.99,
    'current_price': 9.99
}

tweet_id = client.post_beauty_deal(test_deal)
if tweet_id:
    print(f'✅ Test tweet posted! ID: {tweet_id}')
else:
    print('❌ Failed to post test tweet')
"
```

## 🚀 Step 7: Run the Bot

Start the bot to begin finding and posting deals:

```bash
# Run once to find and post current deals
python src/cli.py run

# Or run continuously (checks every hour)
python src/cli.py run --continuous
```

## 📊 Monitor Performance

Check bot statistics:

```bash
python src/cli.py stats
```

View recent tweets and engagement:

```bash
python -c "
import sys
sys.path.append('src')
from twitter_client import TwitterClient
from database import DatabaseManager

client = TwitterClient()
db = DatabaseManager()

# Get recent tweets from database
recent_tweets = db.get_recent_tweets(limit=5)
for tweet in recent_tweets:
    analytics = client.get_tweet_analytics(tweet.tweet_id)
    if analytics:
        print(f'Tweet: {tweet.content[:50]}...')
        print(f'  Likes: {analytics[\"likes\"]} | Retweets: {analytics[\"retweets\"]}')
        print()
"
```

## ⚡ Production Setup

For continuous operation, consider:

1. **Use Docker**:
   ```bash
   docker-compose up -d
   ```

2. **Set up Cron Job** (Linux/Mac):
   ```bash
   # Add to crontab to run every hour
   0 * * * * cd /path/to/bot && python src/cli.py run
   ```

3. **Use Task Scheduler** (Windows):
   - Open Task Scheduler
   - Create Basic Task
   - Set to run hourly
   - Action: Start Program
   - Program: `python`
   - Arguments: `src/cli.py run`
   - Start in: Bot directory path

## 🎯 Beauty-Focused Features

The bot is configured for beauty deals with:

- **Beauty-Only Tweets**: Only beauty products get tweeted
- **Beauty-Specific Emojis**: ✨💄🌟💅🌸💎🎀🦋
- **Beauty Hashtags**: #BeautyDeals #MakeupSale #BeautyFinds #TheFrugalBeauty
- **Higher Quality Standards**: 20% minimum discount, $20-$200 price range
- **Beauty Keywords Detection**: Makeup, skincare, haircare, fragrance products

## 🛡️ Rate Limiting & Best Practices

The bot includes built-in protection:

- **Hourly Limit**: Max 10 tweets per hour (configurable)
- **Time Spacing**: 5 minutes minimum between tweets
- **Quality Filters**: Only posts high-quality deals
- **Duplicate Prevention**: Won't post the same deal twice

## 🔧 Troubleshooting

**Common Issues**:

1. **401 Unauthorized**: Check API credentials in `.env`
2. **403 Forbidden**: Verify app permissions are "Read and Write"
3. **429 Rate Limited**: Bot will automatically wait and retry
4. **No deals found**: Check Keepa API key and token balance

**Need Help?**
- Check the logs in the console output
- Run `python src/cli.py test` to validate all configurations
- Review the error messages for specific issues

## 💡 Pro Tips

1. **Test First**: Always test with a test account before going live
2. **Monitor Engagement**: Track which types of deals get the most engagement
3. **Adjust Settings**: Fine-tune discount thresholds based on performance
4. **Schedule Wisely**: Consider your audience's timezone for optimal posting times
5. **Stay Compliant**: Follow Twitter's automation rules and Amazon's affiliate guidelines

---

🎉 **You're all set!** Your bot will now automatically find beauty deals and post them to Twitter with your affiliate links.
