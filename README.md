# 🔍 Trend Scout

**High-Performance Viral Content Discovery for Web Design & UI/UX**

A Python-based Instagram analysis tool designed for **Studio Pixelens** to scientifically identify viral content opportunities in the high-end Web Design and UI/UX niche.

## 🎯 Philosophy

**Quality over Quantity.** We hunt for "Outliers" — posts that statistically outperform their creator's average engagement — not just posts with many likes.

## ✨ Features

- 🧬 **Scientific Viral Algorithm**: Multi-stage filtering based on age, follower count, and engagement rate
- 🛡️ **Safety First**: Intelligent rate limiting with random delays (15-45s) to avoid IP bans
- 💾 **Session Persistence**: Smart authentication caching to minimize logins
- 📊 **Semantic Output**: LLM-optimized JSON format with virality scores
- 🎨 **Niche Targeting**: Pre-configured for Web Design, UI/UX, and Creative Agency content
- 📈 **Detailed Analytics**: Comprehensive statistics and progress logging

## 🏗️ Architecture

```
pixelens-trend-scout/
├── main.py              # Main application & TrendScout class
├── config.py            # Configuration & environment management
├── safety_manager.py    # Rate limiting & error handling
├── data_processor.py    # Data extraction & formatting
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to project directory
cd pixelens-trend-scout

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

**Optional**: Edit `.env` to set custom thresholds or credentials:

```env
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
ER_THRESHOLD=0.03        # 3% engagement rate
MIN_FOLLOWERS=1000
MAX_FOLLOWERS=500000
POST_AGE_DAYS=45
```

> **Note**: If credentials are not in `.env`, the app will prompt you securely at runtime.

### 3. Run

**Test Mode** (recommended for first run):
```bash
python main.py --test-mode --limit 10
```

**Full Production Run**:
```bash
python main.py
```

## 📋 How It Works

### The Viral Algorithm

The application implements a strict 3-stage filter pipeline:

#### **Stage 1: Age Filter**
- Only analyzes posts **< 45 days old**
- Ensures trends are current and actionable

#### **Stage 2: Follower Filter**
- Accounts must have **1,000 - 500,000 followers**
- Too small = unreliable data
- Too large = generic content, not outliers

#### **Stage 3: Engagement Rate Filter**
- Calculates: `ER = (Likes + Comments) / Followers`
- Threshold: **ER > 3%** (configurable)
- Only saves posts that significantly outperform average

### Virality Score Calculation

Each viral post receives a score (0-10) based on:
- **Base Score** (0-5): Engagement rate percentage
- **Engagement Bonus** (0-3): Absolute engagement volume
- **Follower Bonus** (0-2): Optimal follower range (5k-50k sweet spot)

## 📤 Output Format

Results are saved to `viral_trends.json` in a semantic structure optimized for LLM analysis:

```json
[
  {
    "trend_id": "C1aBcDeFgHi",
    "analysis": {
      "virality_score": 7.25,
      "type": "Carousel",
      "engagement_rate": 4.8,
      "posted_date": "2025-11-28"
    },
    "content": {
      "hook_preview": "5 UI mistakes that make your portfolio look...",
      "full_caption": "Complete caption with all text...",
      "tags": ["#webdesign", "#uidesign", "#designtips"]
    },
    "resource": "https://instagram.com/path/to/image.jpg",
    "post_url": "https://www.instagram.com/p/C1aBcDeFgHi/",
    "creator": {
      "username": "creative_designer",
      "followers": 12500
    },
    "metrics": {
      "likes": 650,
      "comments": 42
    }
  }
]
```

Posts are **sorted by virality score** (highest first) for easy prioritization.

## 🎨 Target Niche

Pre-configured hashtags for **Studio Pixelens**:
- `#webdesign`
- `#uidesign`
- `#astrobuild`
- `#webdevelopment`
- `#creativeagency`
- `#designtips`
- `#uiux`

**To customize**: Edit `TARGET_HASHTAGS` in `config.py`.

## 🛡️ Safety Features

### Rate Limit Protection
- **Random Delays**: 15-45 seconds between requests (mimics human behavior)
- **Exponential Backoff**: Automatic pause when rate limits detected
- **Retry Logic**: Intelligent retry for network errors

### Error Handling
- Comprehensive try-except blocks around all Instagram API calls
- Session persistence to minimize login frequency
- Detailed logging to `trend_scout.log`

### Best Practices
- Start with `--test-mode` to verify functionality
- Monitor `trend_scout.log` for rate limit warnings
- Run during off-peak hours for better performance
- Use VPN if concerned about IP bans

## 📊 CLI Options

```bash
python main.py [OPTIONS]

Options:
  --test-mode    Run in test mode with limited posts
  --limit N      Analyze only N posts per hashtag (default: 10 in test mode)
```

**Examples**:
```bash
# Test with 5 posts per hashtag
python main.py --test-mode --limit 5

# Full production run
python main.py
```

## 🔧 Troubleshooting

### "Login failed"
- Verify your Instagram credentials in `.env`
- Check if Instagram requires 2FA (may need app-specific password)
- Delete `session_data` file and try again

### "Rate limit detected"
- This is normal for prolonged usage
- The app will automatically pause and retry
- Consider reducing hashtag count or running in test mode

### "No viral posts found"
- Your filters might be too strict
- Try lowering `ER_THRESHOLD` in `.env`
- Increase `MAX_FOLLOWERS` or decrease `MIN_FOLLOWERS`

### Connection errors
- Check your internet connection
- Instagram may be experiencing downtime
- Try again after a few minutes

## ⚠️ Legal & Ethical Considerations

- **Terms of Service**: Ensure your usage complies with Instagram's ToS
- **Rate Limiting**: This tool respects Instagram's infrastructure with delays
- **Privacy**: Only analyzes public posts and accounts
- **Purpose**: Designed for competitive analysis and trend research

**Use responsibly.** This tool is for professional market research, not spam or harassment.

## 📈 Next Steps

After running Trend Scout:

1. **Review** `viral_trends.json` for high-scoring posts
2. **Analyze** content patterns, hooks, and formats
3. **Feed to LLM**: Use the semantic JSON for AI-powered content generation
4. **Create**: Develop Studio Pixelens branded content inspired by trends

## 🤝 Support

For issues or questions:
- Check `trend_scout.log` for detailed error messages
- Review this README's Troubleshooting section
- Verify your configuration in `.env`

## 📝 Version

**Version**: 1.0.0
**Last Updated**: December 2025
**Author**: Studio Pixelens

---

**Built with ❤️ for high-performance trend analysis.**
