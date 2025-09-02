#!/usr/bin/env python3
"""
Alternative test outputs for the beauty bot
Allows testing without posting to Twitter
"""

import os
import sys
from datetime import datetime
import requests

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import config

class TestOutputs:
    """Handle different test output methods"""
    
    def __init__(self):
        self.test_mode = getattr(config, 'TEST_MODE', 'false').lower() == 'true'
        self.output_method = getattr(config, 'TEST_OUTPUT', 'console')
    
    def output_tweet(self, tweet_content, deal_data=None):
        """Output tweet using selected method"""
        if not self.test_mode:
            return None
            
        if self.output_method == 'console':
            return self._console_output(tweet_content, deal_data)
        elif self.output_method == 'file':
            return self._file_output(tweet_content, deal_data)
        elif self.output_method == 'discord':
            return self._discord_output(tweet_content, deal_data)
        elif self.output_method == 'slack':
            return self._slack_output(tweet_content, deal_data)
        else:
            return self._console_output(tweet_content, deal_data)
    
    def _console_output(self, tweet_content, deal_data):
        """Print tweet to console"""
        print("\n" + "="*70)
        print("🧪 TEST MODE - WOULD POST TO TWITTER:")
        print("="*70)
        print(tweet_content)
        print("="*70)
        print(f"📊 Character count: {len(tweet_content)}/280")
        if deal_data:
            print(f"💰 Deal: {deal_data.get('title', 'Unknown')[:50]}...")
            print(f"🔥 Discount: {deal_data.get('discount_percent', 0)}%")
        print("="*70)
        return "TEST_CONSOLE_OUTPUT"
    
    def _file_output(self, tweet_content, deal_data):
        """Save tweet to file"""
        filename = "test_tweets.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"🧪 TEST TWEET - {timestamp}\n")
            f.write(f"{'='*70}\n")
            f.write(f"{tweet_content}\n")
            f.write(f"📊 Character count: {len(tweet_content)}/280\n")
            if deal_data:
                f.write(f"💰 Deal: {deal_data.get('title', 'Unknown')}\n")
                f.write(f"🔥 Discount: {deal_data.get('discount_percent', 0)}%\n")
            f.write(f"{'='*70}\n")
        
        print(f"💾 Tweet saved to {filename}")
        return "TEST_FILE_SAVED"
    
    def _discord_output(self, tweet_content, deal_data):
        """Post to Discord webhook"""
        webhook_url = getattr(config, 'DISCORD_WEBHOOK_URL', None)
        if not webhook_url:
            print("❌ Discord webhook URL not configured")
            return self._console_output(tweet_content, deal_data)
        
        try:
            payload = {
                "embeds": [{
                    "title": "🧪 DropDeadFrugal Test Tweet",
                    "description": f"```{tweet_content}```",
                    "color": 0x8B5A8C,
                    "fields": [
                        {
                            "name": "📊 Character Count",
                            "value": f"{len(tweet_content)}/280",
                            "inline": True
                        }
                    ],
                    "timestamp": datetime.now().isoformat()
                }]
            }
            
            if deal_data:
                payload["embeds"][0]["fields"].extend([
                    {
                        "name": "💰 Product",
                        "value": deal_data.get('title', 'Unknown')[:100],
                        "inline": False
                    },
                    {
                        "name": "🔥 Discount",
                        "value": f"{deal_data.get('discount_percent', 0)}%",
                        "inline": True
                    }
                ])
            
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 204:
                print("✅ Tweet sent to Discord")
                return f"DISCORD_SUCCESS_{response.status_code}"
            else:
                print(f"❌ Discord error: {response.status_code}")
                return self._console_output(tweet_content, deal_data)
                
        except Exception as e:
            print(f"❌ Discord error: {str(e)}")
            return self._console_output(tweet_content, deal_data)
    
    def _slack_output(self, tweet_content, deal_data):
        """Post to Slack webhook"""
        webhook_url = getattr(config, 'SLACK_WEBHOOK_URL', None)
        if not webhook_url:
            print("❌ Slack webhook URL not configured")
            return self._console_output(tweet_content, deal_data)
        
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🧪 DropDeadFrugal Test Tweet"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{tweet_content}```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📊 *{len(tweet_content)}/280 characters*"
                        }
                    ]
                }
            ]
            
            if deal_data:
                blocks.append({
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*💰 Product:*\n{deal_data.get('title', 'Unknown')[:100]}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🔥 Discount:*\n{deal_data.get('discount_percent', 0)}%"
                        }
                    ]
                })
            
            payload = {"blocks": blocks}
            
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 200:
                print("✅ Tweet sent to Slack")
                return f"SLACK_SUCCESS_{response.status_code}"
            else:
                print(f"❌ Slack error: {response.status_code}")
                return self._console_output(tweet_content, deal_data)
                
        except Exception as e:
            print(f"❌ Slack error: {str(e)}")
            return self._console_output(tweet_content, deal_data)

def test_all_outputs():
    """Test all output methods"""
    print("🧪 Testing All Output Methods")
    print("="*50)
    
    # Sample tweet and deal data
    sample_tweet = """🌟 BEAUTY BARGAIN 🌟

Fenty Beauty Pro Filt'r Foundation

🔥 Limited Time: 25% OFF
Price Drop: $39.00 ➡️ $29.25
Your Savings: $9.75

https://amazon.com/dp/B075NVR28D

#BeautyBargain #MakeupFinds #TheFrugalBeauty"""
    
    sample_deal = {
        'title': 'Fenty Beauty Pro Filt\'r Soft Matte Foundation',
        'discount_percent': 25,
        'current_price': 29.25,
        'original_price': 39.00
    }
    
    outputs = TestOutputs()
    
    # Test console output
    print("\n1️⃣ Testing Console Output:")
    outputs.output_method = 'console'
    outputs.output_tweet(sample_tweet, sample_deal)
    
    # Test file output
    print("\n2️⃣ Testing File Output:")
    outputs.output_method = 'file'
    outputs.output_tweet(sample_tweet, sample_deal)
    
    print("\n✅ Output testing complete!")
    print("💡 To use these in your bot:")
    print("   1. Set TEST_MODE=true in .env")
    print("   2. Set TEST_OUTPUT=console (or file, discord, slack)")
    print("   3. Run your bot normally")

if __name__ == "__main__":
    test_all_outputs()
