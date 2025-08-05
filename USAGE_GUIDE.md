# 🚀 Amazon Affiliate Bot - Usage Guide

## Quick Commands

### 🧪 Testing
```bash
# Test Keepa API connectivity
python cli.py test-keepa

# Test deal detection system
python cli.py test --skip-twitter

# Test high-volume processing
python cli.py high-volume-test

# Run specific tests
python test_runner.py keepa     # Keepa connectivity only
python test_runner.py deals     # Deal detection only
python test_runner.py           # All tests
```

### 🏃 Running the Bot
```bash
# Initialize database (first time only)
python cli.py init

# Check bot status and configuration
python cli.py status

# Run the production bot
python cli.py run
```

### 📊 Monitoring
```bash
# View recent deals found
python cli.py deals

# View recent tweets posted
python cli.py tweets

# View bot performance metrics
python cli.py metrics

# Look up specific product
python cli.py lookup B08N5WRWNW
```

### 🛠️ Maintenance
```bash
# Clear all data (deals, tweets, metrics)
python cli.py clear

# View help for any command
python cli.py COMMAND --help
```

## 📁 File Organization

- **Need to modify bot logic?** → `src/` directory
- **Need to run tests?** → `tests/` directory or `test_runner.py`
- **Need documentation?** → `docs/` directory
- **Need to deploy?** → `scripts/` directory (Docker files)
- **Need to monitor?** → `monitoring/` directory (Grafana/Prometheus)

## 🔧 Configuration

All settings are in `src/config.py` or `.env` file:

### Key Parameters (Already Optimized)
- `MIN_DISCOUNT_PERCENT: 15%` - Minimum deal discount
- `MAX_SALES_RANK: 100,000` - Maximum sales rank filter
- `MIN_REVIEW_COUNT: 25` - Minimum review count
- `KEEPA_TOKENS_PER_MINUTE: 1200` - Your API plan rate

### Fallback Parameters (Auto-activates if no deals)
- `FALLBACK_MIN_DISCOUNT: 10%` - Lower discount threshold
- `FALLBACK_MAX_SALES_RANK: 500,000` - Broader sales rank
- `FALLBACK_MIN_REVIEW_COUNT: 10` - Lower review requirement

## 🎯 Next Steps

1. **Purchase Keepa tokens** at https://keepa.com/#!api
2. **Test connectivity**: `python cli.py test-keepa`
3. **Test deals**: `python cli.py test --skip-twitter`
4. **Configure Twitter API** in `.env` file
5. **Run production**: `python cli.py run`

## 🆘 Troubleshooting

### "No deals found"
- Check Keepa tokens: `python cli.py test-keepa`
- Try relaxed parameters: Bot automatically uses fallback

### "Import errors"
- Ensure you're in project root directory
- Check `requirements.txt` installed: `pip install -r requirements.txt`

### "Twitter errors"
- Verify Twitter API keys in `.env` file
- Test without Twitter: `python cli.py test --skip-twitter`

---
**Your production-ready affiliate marketing automation!** 🤖💰