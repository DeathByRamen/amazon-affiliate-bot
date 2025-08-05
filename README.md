# Amazon Affiliate Bot

A production-grade bot that automatically detects Amazon deals using Keepa API and posts them to Twitter with affiliate links.

## 🚀 Features

- **Deal Detection**: Uses Keepa API to monitor Amazon for price drops and deals
- **Smart Filtering**: Configurable filters for discount percentage, price range, and product quality
- **Twitter Integration**: Automatically posts deals to Twitter with engaging content
- **Affiliate Links**: Generates Amazon affiliate URLs for monetization
- **Database Tracking**: Tracks all deals, tweets, and performance metrics
- **Health Monitoring**: Built-in health checks and monitoring endpoints
- **Rate Limiting**: Respects API limits and implements smart rate limiting
- **Error Handling**: Comprehensive error handling and logging
- **Docker Support**: Containerized for easy deployment
- **CLI Interface**: Command-line tools for management and monitoring

## 📋 Prerequisites

1. **Keepa API Key**: Sign up at [Keepa.com](https://keepa.com) and get an API key
2. **Twitter Developer Account**: Create a Twitter app for API access
3. **Amazon Associates Account**: Get an affiliate tag from Amazon Associates
4. **Python 3.11+**: Required for running the bot
5. **Docker** (optional): For containerized deployment

## 🛠️ Step-by-Step Setup Guide

### Step 1: Get API Keys

#### Keepa API Key
1. Go to [Keepa.com](https://keepa.com)
2. Create an account and navigate to "API Access Key"
3. Purchase API access (starts at ~$19/month for 1M requests)
4. Copy your API key

#### Twitter Developer Account
1. Apply for a [Twitter Developer Account](https://developer.twitter.com)
2. Create a new app in the Developer Portal
3. Generate API keys and access tokens
4. Note down:
   - API Key
   - API Secret Key
   - Access Token
   - Access Token Secret
   - Bearer Token

#### Amazon Associates
1. Sign up for [Amazon Associates](https://affiliate-program.amazon.com)
2. Get approved for the program
3. Note your affiliate tag (e.g., "yourtag-20")

### Step 2: Environment Setup

1. **Clone and Navigate**:
   ```bash
   cd hustle/keepa
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create Environment File**:
   ```bash
   cp .env.example .env
   ```

4. **Configure Environment Variables**:
   Edit `.env` file with your credentials:
   ```env
   # Keepa API Configuration
   KEEPA_API_KEY=your_keepa_api_key_here

   # Twitter API Configuration  
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
   TWITTER_BEARER_TOKEN=your_bearer_token

   # Amazon Affiliate Configuration
   AMAZON_AFFILIATE_TAG=your_affiliate_tag

   # Bot Configuration (adjust as needed)
   MAX_TWEETS_PER_HOUR=10
   MIN_DISCOUNT_PERCENT=30
   MIN_PRICE_DROP=10.00
   MAX_PRODUCT_PRICE=500.00
   ```

### Step 3: Database Setup

1. **Initialize Database**:
   ```bash
   python cli.py init
   ```

2. **Verify Setup**:
   ```bash
   python cli.py status --check-apis
   ```

### Step 4: Testing

1. **Test Configuration**:
   ```bash
   python cli.py test
   ```

2. **Look Up a Product**:
   ```bash
   python cli.py lookup --asin B08N5WRWNW
   ```

3. **View Current Status**:
   ```bash
   python cli.py status
   ```

### Step 5: Running the Bot

#### Option A: Direct Python
```bash
python bot.py
```

#### Option B: CLI Command
```bash
python cli.py run
```

#### Option C: Docker (Recommended for Production)
```bash
# Build and start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f affiliate-bot

# Stop
docker-compose down
```

## 🔧 Configuration Options

### Bot Behavior
- `MAX_TWEETS_PER_HOUR`: Maximum tweets to post per hour
- `MIN_DISCOUNT_PERCENT`: Minimum discount percentage to consider
- `MIN_PRICE_DROP`: Minimum dollar amount savings required
- `MAX_PRODUCT_PRICE`: Maximum product price to consider

### Quality Filters
The bot automatically filters out:
- Products with poor ratings (< 3.5 stars)
- Products with few reviews (< 10)
- Adult or restricted content
- Recently posted deals (24-hour cooldown)

## 📊 Monitoring and Management

### CLI Commands

```bash
# View recent deals
python cli.py deals --count 20

# View recent tweets  
python cli.py tweets --count 20

# View performance metrics
python cli.py metrics --days 7

# Check bot status
python cli.py status --check-apis

# Clear all data
python cli.py clear
```

### Health Check Endpoints

When running, the bot exposes health check endpoints:

- `http://localhost:8080/health` - Basic health status
- `http://localhost:8080/metrics` - Performance metrics
- `http://localhost:8080/status` - Detailed status information

### Monitoring Dashboard

If using Docker Compose, you get:
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090

## 🔄 Bot Operation

### Deal Detection Cycle
1. **API Call**: Queries Keepa for current deals
2. **Filtering**: Applies quality and business rules
3. **Deduplication**: Checks against recently posted deals
4. **Twitter Posting**: Creates engaging tweets with affiliate links
5. **Database Logging**: Records all activities for tracking

### Scheduling
- **Deal Processing**: Every 30 minutes
- **Health Checks**: Every 5 minutes  
- **Daily Cleanup**: 2:00 AM
- **Weekly Reports**: Sunday 9:00 AM
- **Rate Limit Reset**: Midnight

## 🚨 Production Considerations

### Scaling
- Use PostgreSQL instead of SQLite for production
- Implement Redis for caching and rate limiting
- Consider load balancing for high-volume operations

### Security
- Use environment variables for all secrets
- Run containers as non-root user
- Implement proper firewall rules
- Regular security updates

### Monitoring
- Set up alerting for API failures
- Monitor tweet engagement rates
- Track conversion metrics
- Log analysis for optimization

### Compliance
- Follow Amazon Associates terms of service
- Respect Twitter's automation rules
- Include proper FTC disclosures
- Monitor for policy changes

## 📈 Performance Optimization

### API Efficiency
- Keepa rate limiting (1 request/second)
- Twitter rate limiting (300 tweets/15 min)
- Batch operations where possible
- Smart caching strategies

### Quality Improvements
- A/B testing on tweet formats
- Engagement rate tracking
- Category-specific filtering
- Seasonal adjustment algorithms

## 🛠️ Troubleshooting

### Common Issues

1. **"Configuration error" on startup**
   - Check all required environment variables are set
   - Verify API keys are valid and active

2. **"No deals detected"**
   - Adjust MIN_DISCOUNT_PERCENT (try lower values)
   - Check Keepa API token balance
   - Verify price ranges in config

3. **"Twitter API error"**
   - Verify all Twitter credentials
   - Check if app has write permissions
   - Ensure account is not suspended

4. **Database errors**
   - Run `python cli.py init` to recreate tables
   - Check database permissions
   - Verify SQLite file location

### Logs
Check logs in the `logs/` directory:
- `bot_YYYY-MM-DD.log`: Daily bot logs
- Docker logs: `docker-compose logs affiliate-bot`

## 📋 Legal and Compliance

### Disclosures
Always include appropriate affiliate disclosures in your tweets as required by FTC guidelines.

### Terms of Service
- Comply with Amazon Associates Operating Agreement
- Follow Twitter Developer Agreement and Policy
- Respect Keepa API terms of service

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Verify API credentials and permissions
4. Test with single cycle: `python cli.py test`

## 📄 License

This project is for educational and commercial use. Please ensure compliance with all applicable terms of service and regulations.