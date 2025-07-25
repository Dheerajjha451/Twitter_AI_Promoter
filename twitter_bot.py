import os
import json
import time
import random
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import google.generativeai as genai

load_dotenv()

SALESLY_CONFIG = {
    'website_url': 'salesly.live',
    'max_promotions_per_hour': 6,
    'min_delay_between_promotions': 15,
    'max_delay_between_promotions': 30
}

class TwitterBot:
    def __init__(self):
        self.username = os.getenv('TWITTER_USERNAME')
        self.password = os.getenv('TWITTER_PASSWORD')
        self.cookies_file = os.getenv('COOKIES_FILE')
        self.chrome_profile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chrome_profile')
        
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=gemini_api_key)
        
        model_names = [
            'models/gemini-1.5-flash',
            'models/gemini-2.0-flash',
            'gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'gemini-1.5-pro'
        ]
        self.model = None
        self.ai_available = False
        
        for model_name in model_names:
            try:
                test_model = genai.GenerativeModel(model_name)
                test_response = test_model.generate_content("Test")
                self.model = test_model
                self.ai_available = True
                print(f"✓ AI model initialized: {model_name}")
                break
            except Exception as e:
                error_str = str(e).lower()
                if "404" in error_str or "not found" in error_str:
                    continue
                elif "429" in error_str or "quota" in error_str:
                    continue
                else:
                    continue
        
        if not self.model:
            self.ai_available = False
            print("⚠ AI unavailable - using keyword-based filtering")
        
        self.setup_driver()

    def setup_driver(self):
        """Initialize the Chrome WebDriver with appropriate options"""
        try:
            os.makedirs(self.chrome_profile, exist_ok=True)
            
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'--user-data-dir={self.chrome_profile}')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            self.driver.get("https://twitter.com")
            print("Browser initialized and Twitter opened")
                
        except Exception as e:
            print(f"X Browser setup failed: {str(e)}")
            if hasattr(self, 'driver'):
                self.driver.quit()
            raise e

    def save_cookies(self):
        """Save cookies to file"""
        with open(self.cookies_file, 'w') as f:
            json.dump(self.driver.get_cookies(), f)

    def load_cookies(self):
        """Load cookies from file if exists"""
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            return True
        except FileNotFoundError:
            return False

    def login(self):
        """Login to Twitter using credentials"""
        try:
            print("Starting login process...")
            self.driver.get('https://x.com/i/flow/login')
            time.sleep(5)
            
            if not self.load_cookies():
                print("Entering credentials...")
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
                )
                username_input.clear()
                for char in self.username:
                    username_input.send_keys(char)
                    time.sleep(0.1)
                time.sleep(1)
                username_input.send_keys(Keys.RETURN)
                time.sleep(2)
                
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
                )
                password_input.clear()
                for char in self.password:
                    password_input.send_keys(char)
                    time.sleep(0.1)
                time.sleep(1)
                password_input.send_keys(Keys.RETURN)
                
                time.sleep(10)
                self.save_cookies()
                print("Login successful - cookies saved")
            else:
                print("Using saved cookies")
            
            self.driver.get('https://x.com/home')
            time.sleep(5)
            
            if "home" in self.driver.current_url.lower():
                print("Successfully navigated to home feed")
                return True
            else:
                print("Login verification failed")
                return False
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def get_feed_tweets(self):
        """Get tweets from the home feed"""
        try:
            tweets = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
            return tweets
        except Exception:
            return []

    def get_tweet_text(self, tweet_element):
        """Extract text content from a tweet"""
        try:
            text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
            return text_element.text
        except NoSuchElementException:
            return None
        except Exception as e:
            return None

    def get_tweet_id(self, tweet_element):
        """Extract unique identifier for a tweet"""
        try:
            time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
            tweet_link = time_element.find_element(By.XPATH, '..').get_attribute('href')
            
            try:
                author_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                author_name = author_element.text.split('\n')[0]
                return f"{author_name}_{tweet_link}"
            except:
                return tweet_link
        except NoSuchElementException:
            return None

    def get_tweet_timestamp(self, tweet_element):
        """Extract timestamp from a tweet"""
        try:
            time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
            timestamp = time_element.get_attribute('datetime')
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        except (NoSuchElementException, ValueError):
            return None

    def is_within_24_hours(self, tweet_element):
        """Check if tweet is within the last 24 hours"""
        tweet_time = self.get_tweet_timestamp(tweet_element)
        if tweet_time:
            current_time = datetime.utcnow()
            time_difference = current_time - tweet_time
            return time_difference <= timedelta(hours=24)
        return False

    def is_own_tweet(self, tweet_element):
        """Check if the tweet is from our own account"""
        try:
            username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
            username_text = username_element.text.lower()
            our_username = os.getenv('TWITTER_USERNAME', '').lower()
            
            return our_username in username_text
        except Exception:
            return True

    def is_reply_tweet(self, tweet_element):
        """Check if the tweet is a reply"""
        try:
            reply_indicators = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid="socialContext"]')
            if reply_indicators:
                return True

            replying_to = tweet_element.find_elements(By.XPATH, './/*[contains(text(), "Replying to")]')
            if replying_to:
                return True

            return False
        except Exception:
            return True

    def should_promote_on_tweet(self, tweet_text):
        """Determine if this tweet is suitable for Salesly promotion using AI analysis"""
        if not tweet_text:
            return False
        
        if not self.ai_available or not self.model:
            print("Using keyword-based filtering")
            return self._keyword_based_filtering(tweet_text)
            
        try:
            analysis_prompt = f"""
            Analyze this tweet and determine if it's suitable for promoting Salesly (a website visitor engagement tool).
            
            Salesly helps websites provide instant answers to visitors and gives insights into visitor behavior.
            
            Only return "YES" if the tweet is about:
            1. Website development, design, or optimization
            2. Customer support challenges on websites
            3. SaaS/software businesses looking to improve user experience
            4. E-commerce sites wanting to reduce cart abandonment
            5. Entrepreneurs/startups building web platforms
            6. Web analytics, visitor behavior, or conversion optimization
            7. Freelancers/agencies building websites for clients
            8. Technical discussions about improving website engagement
            
            Return "NO" if the tweet is about:
            - Agriculture, farming, food, recipes
            - Sports, entertainment, personal life
            - Politics, news, social issues
            - Physical products (not digital/web-related)
            - Health, fitness, medical topics
            - Travel, lifestyle, fashion
            - Cryptocurrency, NFTs, financial trading
            - Generic motivational content without tech context
            - Spam or promotional content
            
            Tweet: "{tweet_text}"
            
            Response (YES or NO only):"""
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(analysis_prompt)
                    ai_decision = response.text.strip().upper()
                    break
                except Exception as api_error:
                    error_str = str(api_error).lower()
                    if "404" in error_str or "not found" in error_str:
                        self.ai_available = False
                        return self._keyword_based_filtering(tweet_text)
                    elif "429" in error_str or "quota" in error_str:
                        wait_time = (attempt + 1) * 10
                        time.sleep(wait_time)
                        if attempt == max_retries - 1:
                            return self._keyword_based_filtering(tweet_text)
                    elif "503" in error_str or "overloaded" in error_str:
                        wait_time = (attempt + 1) * 5
                        time.sleep(wait_time)
                        if attempt == max_retries - 1:
                            return self._keyword_based_filtering(tweet_text)
                    else:
                        if attempt == max_retries - 1:
                            return self._keyword_based_filtering(tweet_text)
                        time.sleep(2)
            
            return self._validate_ai_decision_with_keywords(ai_decision, tweet_text)
            
        except Exception:
            return self._keyword_based_filtering(tweet_text)
    
    def _keyword_based_filtering(self, tweet_text):
        """Fallback keyword-based filtering when AI is not available"""
        tweet_lower = tweet_text.lower()
        
        tech_keywords = [
            'website', 'web', 'site', 'app', 'software', 'saas', 'platform',
            'user experience', 'ux', 'ui', 'conversion', 'analytics',
            'customer support', 'chatbot', 'engagement', 'visitors',
            'landing page', 'e-commerce', 'online store', 'digital',
            'startup', 'tech', 'developer', 'programming', 'code'
        ]
        
        non_tech_keywords = [
            'agriculture', 'farming', 'crops', 'harvest', 'farm', 'livestock',
            'recipe', 'cooking', 'food', 'restaurant', 'meal',
            'sports', 'football', 'basketball', 'soccer', 'game',
            'politics', 'election', 'government', 'policy',
            'health', 'medical', 'doctor', 'hospital', 'medicine',
            'travel', 'vacation', 'trip', 'tourism', 'hotel'
        ]
        
        has_tech_keywords = any(keyword in tweet_lower for keyword in tech_keywords)
        has_non_tech_keywords = any(keyword in tweet_lower for keyword in non_tech_keywords)
        
        return has_tech_keywords and not has_non_tech_keywords
    
    def _validate_ai_decision_with_keywords(self, ai_decision, tweet_text):
        """Validate AI decision with keyword check for extra safety"""
        tweet_lower = tweet_text.lower()
        
        tech_keywords = [
            'website', 'web', 'site', 'app', 'software', 'saas', 'platform',
            'user experience', 'ux', 'ui', 'conversion', 'analytics',
            'customer support', 'chatbot', 'engagement', 'visitors',
            'landing page', 'e-commerce', 'online store', 'digital',
            'startup', 'tech', 'developer', 'programming', 'code'
        ]
        
        non_tech_keywords = [
            'agriculture', 'farming', 'crops', 'harvest', 'farm', 'livestock',
            'recipe', 'cooking', 'food', 'restaurant', 'meal',
            'sports', 'football', 'basketball', 'soccer', 'game',
            'politics', 'election', 'government', 'policy',
            'health', 'medical', 'doctor', 'hospital', 'medicine',
            'travel', 'vacation', 'trip', 'tourism', 'hotel'
        ]
        
        has_tech_keywords = any(keyword in tweet_lower for keyword in tech_keywords)
        has_non_tech_keywords = any(keyword in tweet_lower for keyword in non_tech_keywords)
        
        is_suitable = (ai_decision == "YES" and has_tech_keywords and not has_non_tech_keywords)
        
        return is_suitable

    def generate_salesly_promotion(self, tweet_text):
        """Generate a highly contextual and creative response that naturally promotes Salesly"""
        
        if not self.ai_available or not self.model:
            print("Using fallback response generation")
            return self._generate_fallback_response(tweet_text)
        
        try:
            creative_prompt = f"""
            You are a helpful tech professional who genuinely wants to help others. Someone has posted this tweet, and you want to share a solution that could help them.
            
            Your tool, Salesly, is a website engagement platform that:
            - Provides instant answers to website visitors' questions
            - Gives website owners insights into what visitors are really looking for
            - Helps reduce bounce rates and improve conversions
            - Perfect for SaaS, e-commerce, portfolios, and business websites
            
            Create a natural, helpful response that:
            1. First acknowledges their specific situation or challenge
            2. Naturally transitions to how Salesly could help with their exact problem
            3. Sounds like genuine advice from a peer, not a sales pitch
            4. Uses conversational language and feels authentic
            5. Is EXACTLY 250 characters or less including "salesly.live"
            6. Doesn't use generic templates - be creative and specific to their tweet
            7. Use only basic text - NO markdown formatting, NO asterisks, NO special symbols
            8. Write complete sentences with proper punctuation
            9. Make sure the message ends properly with the URL
            
            FORMATTING RULES:
            - NO *asterisks* around words
            - NO markdown formatting 
            - Use plain text only
            - Complete all sentences properly
            - Always end with the URL
            
            Examples of good responses:
            - For website performance: "I had the same issue with my site! What really helped was understanding what visitors were actually looking for. Salesly gives you those insights while helping them instantly. Game changer: salesly.live"
            - For customer support: "Been there! The key is catching questions before they become support tickets. Salesly does exactly that - answers visitors instantly while showing you what they need: salesly.live"
            
            Tweet: "{tweet_text}"
            
            Your helpful, contextual response:"""
            
            max_retries = 3
            ai_reply = None
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(creative_prompt)
                    ai_reply = response.text.strip().strip('"')
                    break
                except Exception as api_error:
                    error_str = str(api_error).lower()
                    if "404" in error_str or "not found" in error_str:
                        self.ai_available = False
                        return self._generate_fallback_response(tweet_text)
                    elif "429" in error_str or "quota" in error_str:
                        wait_time = (attempt + 1) * 10
                        time.sleep(wait_time)
                        if attempt == max_retries - 1:
                            return self._generate_fallback_response(tweet_text)
                    elif "503" in error_str or "overloaded" in error_str:
                        wait_time = (attempt + 1) * 5
                        time.sleep(wait_time)
                        if attempt == max_retries - 1:
                            return self._generate_fallback_response(tweet_text)
                    else:
                        if attempt == max_retries - 1:
                            return self._generate_fallback_response(tweet_text)
                        time.sleep(2)
            
            if not ai_reply:
                return self._generate_fallback_response(tweet_text)
            
            ai_reply = self.clean_text(ai_reply)
            ai_reply = ai_reply.replace('*', '').replace('_', '').replace('`', '')
            
            if SALESLY_CONFIG['website_url'].lower() not in ai_reply.lower():
                available_space = 270 - len(ai_reply)
                if available_space > 20:
                    ai_reply += f" Check out {SALESLY_CONFIG['website_url']}"
                else:
                    sentences = ai_reply.split('.')
                    if len(sentences) > 1:
                        complete_sentences = []
                        total_length = 0
                        for sentence in sentences[:-1]:
                            sentence = sentence.strip()
                            if sentence and total_length + len(sentence) + 20 < 250:
                                complete_sentences.append(sentence)
                                total_length += len(sentence) + 2
                        
                        if complete_sentences:
                            ai_reply = '. '.join(complete_sentences) + f". {SALESLY_CONFIG['website_url']}"
                        else:
                            ai_reply = ai_reply[:220].rsplit(' ', 1)[0] + f" {SALESLY_CONFIG['website_url']}"
                    else:
                        ai_reply = ai_reply[:220].rsplit(' ', 1)[0] + f" {SALESLY_CONFIG['website_url']}"
            
            if len(ai_reply) > 270:
                max_content_length = 250
                if SALESLY_CONFIG['website_url'] in ai_reply:
                    if len(ai_reply) > 270:
                        truncated = ai_reply[:270].rsplit(' ', 1)[0]
                        ai_reply = truncated
                else:
                    content_without_url = ai_reply.replace(SALESLY_CONFIG['website_url'], '').strip()
                    if len(content_without_url) > max_content_length:
                        sentences = content_without_url.split('.')
                        complete_content = ""
                        for sentence in sentences:
                            sentence = sentence.strip()
                            if sentence and len(complete_content + sentence + ". ") <= max_content_length:
                                complete_content += sentence + ". "
                        
                        ai_reply = complete_content.strip() + f" {SALESLY_CONFIG['website_url']}"
            
            return ai_reply
            
        except Exception:
            return self._generate_fallback_response(tweet_text)
    
    def _generate_fallback_response(self, tweet_text):
        """Generate a smart fallback response based on tweet content"""
        tweet_lower = tweet_text.lower()
        
        if any(word in tweet_lower for word in ['website', 'site', 'web']):
            fallback = f"Same challenge here! Understanding what website visitors really need makes a huge difference. Try {SALESLY_CONFIG['website_url']} for visitor insights!"
        elif any(word in tweet_lower for word in ['support', 'help', 'customer']):
            fallback = f"Been there! Catching visitor questions early is key. {SALESLY_CONFIG['website_url']} helps with instant answers and insights."
        elif any(word in tweet_lower for word in ['startup', 'business', 'growth']):
            fallback = f"As a fellow builder, visitor insights are crucial! {SALESLY_CONFIG['website_url']} shows what people really want on your site."
        elif any(word in tweet_lower for word in ['saas', 'app', 'software']):
            fallback = f"User experience is everything! {SALESLY_CONFIG['website_url']} helps understand what users need while helping them instantly."
        else:
            fallback = f"Great point! You might find {SALESLY_CONFIG['website_url']} useful for understanding what your website visitors are really looking for."
        
        return fallback

    def clean_text(self, text):
        """Clean text to ensure it only contains supported characters and proper formatting"""
        if not text:
            return text
        
        text = text.replace('*', '').replace('_', '').replace('`', '').replace('#', '')
        text = text.replace('[', '').replace(']', '').replace('**', '').replace('__', '')
        
        import re
        cleaned = re.sub(r'[^\w\s.,!?:;()\-\'\"@/.]', '', text)
        cleaned = ' '.join(cleaned.split())
        
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            if not cleaned.lower().endswith(('salesly.live', '.com', '.io', '.net', '.org')):
                cleaned += '.'
        
        return cleaned or "Great point!"

    def find_element_with_retry(self, by, value, max_attempts=3, check_interactable=False):
        """Find an element with retry logic for stale elements"""
        for attempt in range(max_attempts):
            try:
                if check_interactable:
                    element = self.wait.until(
                        EC.element_to_be_clickable((by, value))
                    )
                else:
                    element = self.wait.until(
                        EC.presence_of_element_located((by, value))
                    )
                    if not element.is_displayed():
                        raise Exception("Element is not visible")
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                
                return element
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                time.sleep(1)
        return None

    def reply_to_tweet(self, tweet_element):
        """Reply to a specific tweet with an AI-generated response"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", tweet_element)
            time.sleep(2)

            tweet_link = self.get_tweet_id(tweet_element)
            if not tweet_link:
                return False

            try:
                text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_text = text_element.text if text_element else None
            except Exception:
                tweet_text = None

            if not tweet_text:
                return False
            else:
                if not self.should_promote_on_tweet(tweet_text):
                    return False
                    
                reply_text = self.generate_salesly_promotion(tweet_text)
            
            reply_text = self.clean_text(reply_text)
            
            try:
                reply_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
                if not reply_button.is_displayed():
                    return False
            except Exception:
                return False

            try:
                reply_button.click()
            except:
                try:
                    self.driver.execute_script("arguments[0].click();", reply_button)
                except Exception:
                    return False
            time.sleep(2)

            try:
                reply_box = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
                )
                if not reply_box.is_displayed():
                    return False
            except Exception:
                return False

            try:
                reply_box.clear()
                reply_box.send_keys(reply_text)
            except Exception:
                try:
                    reply_box.clear()
                    for char in reply_text:
                        reply_box.send_keys(char)
                        time.sleep(0.05)
                except Exception:
                    return False

            try:
                submit_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButton"]'))
                )
                submit_button.click()
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", submit_button)
                except:
                    return False

            time.sleep(3)
            return True

        except Exception:
            return False

    def scroll_to_top(self):
        """Scroll to the top of the feed"""
        try:
            self.driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(2)
        except Exception:
            pass

    def scroll_feed(self, scroll_count=3):
        """Scroll the feed to load more tweets"""
        try:
            for _ in range(scroll_count):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
        except Exception:
            pass

    def get_recent_tweets(self, max_tweets=20):
        """Get the most recent tweets from the feed"""
        try:
            self.scroll_to_top()
            time.sleep(2)
            
            self.scroll_feed(scroll_count=3)
            
            tweets = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
            
            if not tweets:
                return []

            fresh_tweets = []
            processed_count = 0
            
            for tweet in tweets:
                try:
                    if not tweet.is_displayed() or not self.get_tweet_id(tweet):
                        continue
                        
                    if self.is_own_tweet(tweet):
                        continue
                        
                    if self.is_reply_tweet(tweet):
                        continue
                        
                    fresh_tweets.append(tweet)
                    processed_count += 1
                    
                    if processed_count >= max_tweets:
                        break
                        
                except Exception:
                    continue
            
            return fresh_tweets
        except Exception as e:
            print(f"Error getting tweets: {str(e)}")
            return []

    def monitor_feed(self, interval=10):
        """Monitor the home feed and promote Salesly on relevant tweets"""
        if not self.login():
            print("Failed to login. Please check your credentials.")
            return

        processed_tweets = set()
        print("Starting Salesly promotion bot...")
        print("Looking for relevant tweets to promote Salesly...")
        
        while True:
            try:
                print(f"\nRefreshing feed... (processed {len(processed_tweets)} tweets so far)")
                self.driver.refresh()
                time.sleep(5)
                
                tweets = self.get_recent_tweets(max_tweets=20)
                print(f"Found {len(tweets)} tweets to analyze")
                
                tweets_processed_this_round = 0
                
                for tweet in tweets:
                    try:
                        tweet_id = self.get_tweet_id(tweet)
                        if not tweet_id:
                            continue
                            
                        if tweet_id in processed_tweets:
                            continue
                        
                        metrics = self.get_salesly_metrics()
                        metrics['tweets_analyzed'] += 1
                        
                        tweet_text = self.get_tweet_text(tweet)
                        if not tweet_text or not self.should_promote_on_tweet(tweet_text):
                            continue
                        
                        metrics['relevant_tweets_found'] += 1
                        print(f"Found relevant tweet: {tweet_text[:60]}...")
                        
                        if self.reply_to_tweet(tweet):
                            processed_tweets.add(tweet_id)
                            tweets_processed_this_round += 1
                            metrics['promotions_sent'] += 1
                            print(f"Successfully promoted Salesly!")
                            time.sleep(random.uniform(
                                SALESLY_CONFIG['min_delay_between_promotions'], 
                                SALESLY_CONFIG['max_delay_between_promotions']
                            ))
                        else:
                            print("Failed to reply to tweet")
                    except Exception as e:
                        print(f"Error processing tweet: {str(e)}")
                        continue
                
                print(f"Processed {tweets_processed_this_round} new tweets this round")
                
                if hasattr(self, '_rounds_count'):
                    self._rounds_count += 1
                else:
                    self._rounds_count = 1
                
                if self._rounds_count % 5 == 0:
                    self.log_salesly_metrics()
                
                if len(processed_tweets) > 100:
                    print("Cleaning up processed tweets list...")
                    processed_list = list(processed_tweets)
                    processed_tweets = set(processed_list[-100:])
                
                print(f"Waiting {interval} seconds before next refresh...")
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in feed monitoring: {str(e)}")
                try:
                    self.driver.refresh()
                except:
                    pass
                time.sleep(interval)

    def get_salesly_metrics(self):
        """Track promotion metrics"""
        if not hasattr(self, '_salesly_metrics'):
            self._salesly_metrics = {
                'tweets_analyzed': 0,
                'promotions_sent': 0,
                'relevant_tweets_found': 0,
                'start_time': datetime.now()
            }
        return self._salesly_metrics
    
    def log_salesly_metrics(self):
        """Log current promotion metrics"""
        metrics = self.get_salesly_metrics()
        runtime = datetime.now() - metrics['start_time']
        
        print(f"\n=== Salesly Promotion Metrics ===")
        print(f"Runtime: {runtime}")
        print(f"Tweets analyzed: {metrics['tweets_analyzed']}")
        print(f"Relevant tweets found: {metrics['relevant_tweets_found']}")
        print(f"Salesly promotions sent: {metrics['promotions_sent']}")
        if metrics['relevant_tweets_found'] > 0:
            success_rate = (metrics['promotions_sent'] / metrics['relevant_tweets_found']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        print("=" * 35)

    def cleanup(self):
        """Close the browser and clean up"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    print("=== Salesly Twitter Promotion Bot ===")
    print("This bot will automatically promote Salesly on relevant Twitter threads")
    print("Looking for tweets about websites, business growth, customer support, etc.")
    print("Press Ctrl+C to stop the bot")
    print("=" * 50)
    
    bot = TwitterBot()
    try:
        bot.monitor_feed(interval=10)
    except KeyboardInterrupt:
        print("\nStopping Salesly promotion bot...")
    finally:
        print("Cleaning up...")
        bot.cleanup()
        print("Bot stopped successfully!")

if __name__ == "__main__":
    main()
