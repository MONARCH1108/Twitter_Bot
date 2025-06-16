import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import random
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TwitterBot:
    def __init__(self, username: str, password: str, headless: bool = False):
        """
        Initialize the Twitter bot
        
        Args:
            username: Your Twitter username/email
            password: Your Twitter password
            headless: Run browser in headless mode (default: False for debugging)
        """
        self.username = username
        self.password = password
        self.driver = None
        self.headless = headless
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome WebDriver with optimal settings"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Add various options for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            # Remove these lines as they might interfere with Twitter functionality
            # chrome_options.add_argument("--disable-images")
            # chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Initialize the driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set implicit wait
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def login_to_twitter(self):
        """Login to Twitter account"""
        try:
            logger.info("Navigating to Twitter login page...")
            self.driver.get("https://twitter.com/i/flow/login")
            
            # Wait for and fill username
            logger.info("Waiting for username field...")
            username_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Click Next button
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[text()="Next"]'))
            )
            next_button.click()
            
            # Wait for password field
            logger.info("Waiting for password field...")
            time.sleep(2)  # Small delay to ensure page loads
            
            password_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click Login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[text()="Log in"]'))
            )
            login_button.click()
            
            # Wait for successful login (check for home timeline)
            logger.info("Waiting for login to complete...")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="primaryColumn"]'))
            )
            
            logger.info("Successfully logged into Twitter!")
            time.sleep(3)  # Additional wait to ensure full page load
            
        except TimeoutException:
            logger.error("Login timeout - please check credentials or network connection")
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    def post_tweet(self, tweet_text: str) -> bool:
        """
        Post a tweet to Twitter with multiple fallback methods
        
        Args:
            tweet_text: The text content of the tweet
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Posting tweet: {tweet_text[:50]}...")
            
            # Navigate to home if not already there
            if "home" not in self.driver.current_url:
                self.driver.get("https://twitter.com/home")
                time.sleep(3)
            
            # Method 1: Try the standard compose box
            success = self._try_compose_method_1(tweet_text)
            if success:
                return True
            
            # Method 2: Try alternative selectors
            success = self._try_compose_method_2(tweet_text)
            if success:
                return True
            
            # Method 3: Try using the "What's happening?" placeholder
            success = self._try_compose_method_3(tweet_text)
            if success:
                return True
            
            logger.error("All posting methods failed")
            return False
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return False
    
    def _try_compose_method_1(self, tweet_text: str) -> bool:
        """Method 1: Standard compose box"""
        try:
            logger.info("Trying compose method 1...")
            
            # Find and click the tweet compose area
            tweet_compose = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
            )
            tweet_compose.click()
            time.sleep(1)
            
            # Clear and type the tweet
            tweet_compose.clear()
            tweet_compose.send_keys(tweet_text)
            time.sleep(2)
            
            # Try multiple selectors for the post button
            post_button_selectors = [
                '[data-testid="tweetButtonInline"]',
                '[data-testid="tweetButton"]',
                'button[data-testid="tweetButtonInline"]',
                'button[data-testid="tweetButton"]',
                '[role="button"][data-testid="tweetButtonInline"]',
                '[role="button"][data-testid="tweetButton"]'
            ]
            
            for selector in post_button_selectors:
                try:
                    post_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    # Scroll into view and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                    time.sleep(1)
                    
                    # Try regular click first
                    try:
                        post_button.click()
                    except:
                        # If regular click fails, try JavaScript click
                        self.driver.execute_script("arguments[0].click();", post_button)
                    
                    time.sleep(3)
                    logger.info("Method 1 successful!")
                    return True
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Method 1 failed: {e}")
            return False
    
    def _try_compose_method_2(self, tweet_text: str) -> bool:
        """Method 2: Alternative selectors"""
        try:
            logger.info("Trying compose method 2...")
            
            # Try different compose area selectors
            compose_selectors = [
                '[placeholder="What is happening?!"]',
                '[placeholder="What\'s happening?"]',
                '[aria-label="Tweet text"]',
                '.public-DraftEditor-content',
                '[contenteditable="true"]'
            ]
            
            tweet_compose = None
            for selector in compose_selectors:
                try:
                    tweet_compose = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not tweet_compose:
                return False
            
            # Click and enter text
            tweet_compose.click()
            time.sleep(1)
            tweet_compose.clear()
            tweet_compose.send_keys(tweet_text)
            time.sleep(2)
            
            # Try to find and click post button
            post_selectors = [
                'button[data-testid="tweetButtonInline"]',
                'button[data-testid="tweetButton"]',
                'button:contains("Post")',
                'button:contains("Tweet")',
                '[role="button"]:contains("Post")',
                '[role="button"]:contains("Tweet")'
            ]
            
            for selector in post_selectors:
                try:
                    if ':contains(' in selector:
                        # Use XPath for text-based selectors
                        xpath_selector = selector.replace('button:contains("', '//button[contains(text(), "').replace('")', '")]')
                        xpath_selector = xpath_selector.replace('[role="button"]:contains("', '//*[@role="button" and contains(text(), "').replace('")', '")]')
                        post_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, xpath_selector))
                        )
                    else:
                        post_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Try clicking
                    try:
                        post_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", post_button)
                    
                    time.sleep(3)
                    logger.info("Method 2 successful!")
                    return True
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Method 2 failed: {e}")
            return False
    
    def _try_compose_method_3(self, tweet_text: str) -> bool:
        """Method 3: Using keyboard shortcuts"""
        try:
            logger.info("Trying compose method 3 (keyboard shortcuts)...")
            
            # Find compose area
            tweet_compose = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"], [placeholder*="What"], [contenteditable="true"]'))
            )
            
            # Click and enter text
            tweet_compose.click()
            time.sleep(1)
            tweet_compose.clear()
            tweet_compose.send_keys(tweet_text)
            time.sleep(2)
            
            # Use Ctrl+Enter to post (Twitter keyboard shortcut)
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
            
            time.sleep(3)
            logger.info("Method 3 (keyboard shortcut) successful!")
            return True
            
        except Exception as e:
            logger.error(f"Method 3 failed: {e}")
            return False
    
    def load_tweets_from_json(self, json_file_path: str) -> List[Dict]:
        """Load tweets from JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                tweets_data = json.load(file)
            
            logger.info(f"Loaded {len(tweets_data)} tweets from {json_file_path}")
            return tweets_data
            
        except Exception as e:
            logger.error(f"Failed to load tweets from JSON: {e}")
            return []
    
    def run_bot(self, json_file_path: str, post_interval: int = 10, max_tweets: int = None):
        """
        Run the Twitter bot to post tweets from JSON file
        
        Args:
            json_file_path: Path to the JSON file containing tweets
            post_interval: Interval between posts in seconds (default: 10)
            max_tweets: Maximum number of tweets to post (default: all)
        """
        try:
            # Load tweets from JSON
            tweets_data = self.load_tweets_from_json(json_file_path)
            
            if not tweets_data:
                logger.error("No tweets loaded. Exiting...")
                return
            
            # Limit tweets if specified
            if max_tweets:
                tweets_data = tweets_data[:max_tweets]
            
            # Login to Twitter
            self.login_to_twitter()
            
            # Post tweets
            successful_posts = 0
            failed_posts = 0
            
            for i, tweet_data in enumerate(tweets_data, 1):
                try:
                    # Get the complete tweet with hashtags
                    tweet_text = tweet_data.get('tweet_with_hashtags', tweet_data.get('tweet', ''))
                    
                    if not tweet_text:
                        logger.warning(f"Empty tweet at index {i}, skipping...")
                        continue
                    
                    # Check tweet length (Twitter limit is 280 characters)
                    if len(tweet_text) > 280:
                        logger.warning(f"Tweet {i} is too long ({len(tweet_text)} chars), truncating...")
                        tweet_text = tweet_text[:277] + "..."
                    
                    logger.info(f"Posting tweet {i}/{len(tweets_data)}")
                    
                    # Post the tweet
                    if self.post_tweet(tweet_text):
                        successful_posts += 1
                        logger.info(f"✅ Tweet {i} posted successfully")
                    else:
                        failed_posts += 1
                        logger.error(f"❌ Failed to post tweet {i}")
                    
                    # Wait before posting the next tweet (except for the last one)
                    if i < len(tweets_data):
                        logger.info(f"Waiting {post_interval} seconds before next tweet...")
                        time.sleep(post_interval)
                    
                except Exception as e:
                    failed_posts += 1
                    logger.error(f"Error posting tweet {i}: {e}")
                    continue
            
            # Summary
            logger.info(f"Bot completed! Successfully posted: {successful_posts}, Failed: {failed_posts}")
            
        except Exception as e:
            logger.error(f"Bot execution failed: {e}")
            
        finally:
            # Keep browser open for a few seconds before closing
            logger.info("Keeping browser open for 10 seconds...")
            time.sleep(10)
            self.quit()
    
    def quit(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    """Main function to run the Twitter bot"""
    
    # Configuration - UPDATE THESE VALUES
    TWITTER_USERNAME = "you_mail"  # Your Twitter username or email
    TWITTER_PASSWORD = "your_password"          # Your Twitter password
    JSON_FILE_PATH = r"_path_"            # Path to your tweets JSON file
    POST_INTERVAL = 10                                  # Seconds between tweets
    MAX_TWEETS = None                                   # Maximum tweets to post (None = all)
    HEADLESS = False                                    # Set to True to run without browser UI
    
    # Validate configuration
    if TWITTER_USERNAME == "your_twitter_username_or_email" or TWITTER_PASSWORD == "your_twitter_password":
        print("❌ Please update your Twitter credentials in the configuration section!")
        return
    
    # Initialize and run the bot
    bot = TwitterBot(
        username=TWITTER_USERNAME,
        password=TWITTER_PASSWORD,
        headless=HEADLESS
    )
    
    try:
        logger.info("Starting Twitter bot...")
        bot.run_bot(
            json_file_path=JSON_FILE_PATH,
            post_interval=POST_INTERVAL,
            max_tweets=MAX_TWEETS
        )
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        bot.quit()

if __name__ == "__main__":
    main()