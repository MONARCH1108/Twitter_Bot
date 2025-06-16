# 🤖 Twitter News Bot

An intelligent Twitter automation system that crawls BBC news, generates engaging tweets using AI, and automatically posts them to Twitter/X. This project combines web scraping, natural language processing, and social media automation into a comprehensive news-to-tweet pipeline.

## 🌟 Features

- **📰 Smart News Crawling**: Automated BBC news article discovery and extraction
- **🧠 AI-Powered Content Generation**: Uses Ollama (Llama 3.2) for tweet creation and Google Gemini for hashtag generation
- **🎯 Intelligent Tweet Optimization**: Sentiment analysis, urgency detection, and topic extraction
- **🔄 Automated Social Media Posting**: Selenium-based Twitter/X posting with multiple fallback methods
- **📊 Analytics & Insights**: Comprehensive data collection and analysis
- **⚡ Parallel Processing**: Multi-threaded crawling and processing for efficiency
- **🛡️ Robust Error Handling**: Multiple retry mechanisms and failsafes

## 🏗️ Project Structure

```
twitter-news-bot/
├── bbc_crawler.py          # BBC news crawler with AI analysis
├── tweet_generator.py      # AI-powered tweet and hashtag generation
├── twitter_bot.py          # Automated Twitter posting bot
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── output/
    ├── bbc_improved_data.json    # Crawled news data
    ├── generated_tweets.json     # Generated tweets with hashtags
    └── twitter_bot.log          # Bot execution logs
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Ollama** with Llama 3.2 model
3. **Google Gemini API Key**
4. **Chrome Browser** and ChromeDriver
5. **Twitter/X Account**

### Installation

1. **Clone the repository**
   ```bash
   https://github.com/MONARCH1108/Twitter_Bot.git
   cd twitter-news-bot
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and setup Ollama**
   ```bash
   # Install Ollama (visit https://ollama.ai for installation instructions)
   ollama pull llama3.2:latest
   ollama serve
   ```

4. **Install ChromeDriver**
   - Download from [ChromeDriver](https://chromedriver.chromium.org/)
   - Add to your system PATH or place in project directory

### Configuration

1. **Update `tweet_generator.py`**
   ```python
   GEMINI_API_KEY = "your_gemini_api_key_here"
   JSON_FILE_PATH = "path/to/bbc_improved_data.json"
   ```

2. **Update `twitter_bot.py`**
   ```python
   TWITTER_USERNAME = "your_twitter_username"
   TWITTER_PASSWORD = "your_twitter_password"
   JSON_FILE_PATH = "path/to/generated_tweets.json"
   ```

## 📖 Usage

### Step 1: Crawl BBC News
```bash
python bbc_crawler.py
```
This will:
- Discover and crawl BBC news articles
- Extract content and analyze with AI
- Save results to `bbc_improved_data.json`

### Step 2: Generate Tweets
```bash
python tweet_generator.py
```
This will:
- Load crawled news data
- Generate engaging tweets using Ollama
- Create trending hashtags using Gemini
- Save results to `generated_tweets.json`

### Step 3: Post to Twitter
```bash
python twitter_bot.py
```
This will:
- Load generated tweets
- Automatically post to Twitter/X
- Handle rate limiting and errors
- Log all activities

### All-in-One Execution
```bash
# Run the complete pipeline
python bbc_crawler.py && python tweet_generator.py && python twitter_bot.py
```

## ⚙️ Configuration Options

### BBC Crawler (`bbc_crawler.py`)
- **Model Selection**: Change Ollama model (default: `llama3.2:latest`)
- **Categories**: Customize news categories to crawl
- **Article Limits**: Set maximum articles per category
- **Parallel Processing**: Adjust thread count for crawling

### Tweet Generator (`tweet_generator.py`)
- **API Keys**: Configure Gemini API access
- **Content Filtering**: Set urgency and sentiment filters
- **Tweet Length**: Customize tweet character limits
- **Hashtag Count**: Control number of hashtags (3-5 recommended)

### Twitter Bot (`twitter_bot.py`)
- **Posting Intervals**: Time between tweets (minimum 10 seconds recommended)
- **Browser Mode**: Headless vs. visible browser
- **Retry Logic**: Configure retry attempts and timeouts
- **Content Limits**: Maximum tweets per session

## 📊 Output Examples

### Generated Tweet Structure
```json
{
  "tweet": "Breaking: New climate change report reveals alarming trends in global temperatures. Scientists call for immediate action.",
  "hashtags": ["#ClimateChange", "#BreakingNews", "#GlobalWarming", "#Science", "#Environment"],
  "article_url": "https://www.bbc.com/news/science-environment-12345678",
  "topics": ["climate change", "environment", "science"],
  "tweet_with_hashtags": "Breaking: New climate change report reveals alarming trends... #ClimateChange #BreakingNews #GlobalWarming"
}
```

### Analytics Dashboard
- **Total Articles Processed**: Real-time counting
- **Sentiment Distribution**: Positive/Negative/Neutral breakdown
- **Top Topics**: Most frequent news topics
- **Success Rates**: Crawling and posting success metrics

## 🔧 Advanced Features

### Multi-Model AI Integration
- **Ollama (Llama 3.2)**: Local tweet generation
- **Google Gemini**: Cloud-based hashtag optimization
- **BeautifulSoup**: Intelligent content extraction

### Robust Error Handling
- **Network Resilience**: Automatic retry with exponential backoff
- **Content Validation**: Quality checks for articles and tweets
- **Fallback Mechanisms**: Multiple posting strategies for Twitter

### Performance Optimization
- **Parallel Processing**: Concurrent article processing
- **Smart Caching**: Avoid duplicate content
- **Rate Limit Compliance**: Respect API and platform limits

## 📋 Requirements

### Python Dependencies
```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
google-generativeai>=0.3.0
ollama>=0.1.0
aiohttp>=3.9.0
lxml>=4.9.0
```

### System Requirements
- **RAM**: 4GB minimum (8GB recommended for Ollama)
- **Storage**: 2GB free space for models and data
- **Network**: Stable internet connection
- **OS**: Windows 10+, macOS 10.15+, or Linux

## 🛡️ Safety & Ethics

### Content Guidelines
- **News Accuracy**: Only shares content from reputable BBC sources
- **Fact Checking**: AI analysis includes sentiment and urgency validation
- **Rate Limiting**: Respects Twitter's posting limits and guidelines

### Privacy Protection
- **No Personal Data**: Only processes public news content
- **Secure Credentials**: Environment variable support for sensitive data
- **GDPR Compliance**: No user data collection or storage

### Terms of Service
- **Twitter/X ToS**: Designed to comply with platform guidelines
- **BBC Content**: Respects fair use and attribution policies
- **API Usage**: Follows rate limits and usage policies

## 🔧 Troubleshooting

### Common Issues

**1. Ollama Connection Failed**
```bash
# Check if Ollama is running
ollama list
ollama serve

# Verify model installation
ollama pull llama3.2:latest
```

**2. Twitter Login Issues**
- Verify credentials are correct
- Check for 2FA requirements
- Ensure account is not restricted

**3. Gemini API Errors**
- Verify API key is valid
- Check quota and billing status
- Ensure proper API permissions

**4. ChromeDriver Issues**
- Update Chrome browser
- Download matching ChromeDriver version
- Check PATH configuration

### Debug Mode
Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black *.py
flake8 *.py
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and personal use only. Users are responsible for:
- Complying with Twitter/X Terms of Service
- Respecting content licensing and fair use
- Following local laws and regulations
- Using the tool ethically and responsibly

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/twitter-news-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/twitter-news-bot/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/twitter-news-bot/wiki)

## 🚀 Roadmap

### Version 2.0 (Planned)
- [ ] **Multi-Platform Support**: LinkedIn, Facebook, Instagram
- [ ] **Custom News Sources**: Beyond BBC integration
- [ ] **Advanced AI Models**: GPT-4, Claude integration
- [ ] **Web Dashboard**: Real-time monitoring interface
- [ ] **Scheduled Posting**: Cron-like scheduling system
- [ ] **Analytics Dashboard**: Engagement metrics and insights

### Version 1.5 (In Progress)
- [ ] **Docker Support**: Containerized deployment
- [ ] **Cloud Deployment**: AWS/GCP integration
- [ ] **Webhook Support**: Real-time news notifications
- [ ] **Content Filtering**: Advanced topic and sentiment filters

---

**Made with ❤️ by [Your Name]**

*Don't forget to ⭐ star this repository if you found it helpful!*