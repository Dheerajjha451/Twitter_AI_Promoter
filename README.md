# Salesly Twitter Promotion Bot

An intelligent Twitter bot that automatically promotes Salesly on relevant Twitter threads. The bot uses AI to identify suitable tweets about websites, business growth, customer support, and other relevant topics, then generates contextual responses that naturally introduce Salesly.

## 🎯 Key Features

- **Smart Tweet Analysis**: Uses AI to identify tweets suitable for Salesly promotion
- **Contextual Responses**: Generates natural, helpful responses tailored to each tweet
- **Built-in Safety**: Avoids spam, self-promotion, and irrelevant content
- **Performance Tracking**: Real-time metrics and analytics
- **Rate Limiting**: Respects Twitter's limits and maintains natural engagement patterns

## 🚀 What is Salesly?

Salesly is a powerful tool that transforms your website into an engagement hub by:
- Providing instant answers to visitor questions
- Delivering deep insights into what visitors are looking for
- Perfect for SaaS, freelancers, e-commerce, and growing businesses

Visit: [salesly.live](https://salesly.live)

## 📋 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run the Bot**
   ```bash
   python3 twitter_bot.py
   ```

## 🔧 Requirements

- Python 3.8+
- Chrome browser
- Twitter account
- Google Gemini API key
- Required packages (see requirements.txt):
  - selenium==4.15.2
  - webdriver-manager==4.0.1
  - python-dotenv==1.0.0
  - google-generativeai==0.3.1

## ⚙️ Configuration

The bot looks for tweets containing these target keywords:
- **Website**: website, site, web, landing page, homepage
- **Business**: business, startup, entrepreneur, founder, growth, scale
- **SaaS**: saas, software, app, platform, tool
- **Support**: customer support, help, assistance, questions
- **Freelance**: freelancer, freelance, portfolio, client
- **E-commerce**: ecommerce, shop, store, online business
- **Analytics**: insights, data, tracking, optimization

And avoids these topics:
- Spam indicators: "buy now", "click here", "limited time"
- Self-promotion: "follow me", "dm me", "link in bio"
- Unrelated topics: crypto, NFT, forex, trading

## 📊 Analytics

The bot tracks:
- Tweets analyzed
- Relevant tweets found
- Successful promotions sent
- Success rates and performance metrics

## 🛡️ Safety Features

- **Rate Limiting**: Maximum 6 promotions per hour
- **Human-like Delays**: Random 15-30 second delays between actions
- **Content Filtering**: Avoids inappropriate or irrelevant tweets
- **Duplicate Prevention**: Tracks processed tweets to avoid repeat promotions
- **Smart Targeting**: Only promotes on genuinely relevant conversations

---

**Powered by Salesly** - Transform your website with instant answers and deep visitor insights!

🌐 Website: [salesly.live](https://salesly.live)# Twitter_AI_Promoter
# Twitter_AI_Promoter
