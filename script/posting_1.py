import json
import time
import logging
import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import List, Dict, Optional
import random

# Configure logging with UTF-8 encoding to fix Windows Unicode issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_bot.log', encoding='utf-8'),
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
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def setup_browser(self):
        """Setup Playwright browser with optimal settings"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with options
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--disable-plugins"
                ]
            )
            
            # Create context with realistic user agent and viewport
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Add script to remove webdriver property
            await self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set default timeout
            self.page.set_default_timeout(30000)  # 30 seconds
            
            logger.info("Playwright browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def login_to_twitter(self):
        """Login to Twitter account"""
        try:
            logger.info("Navigating to Twitter login page...")
            await self.page.goto("https://twitter.com/i/flow/login")
            
            # Wait for and fill username
            logger.info("Waiting for username field...")
            await self.page.wait_for_selector('input[autocomplete="username"]', timeout=20000)
            username_field = self.page.locator('input[autocomplete="username"]')
            await username_field.clear()
            await username_field.fill(self.username)
            
            # Click Next button
            next_button = self.page.locator('xpath=//span[text()="Next"]')
            await next_button.click()
            
            # Wait for password field
            logger.info("Waiting for password field...")
            await asyncio.sleep(2)  # Small delay to ensure page loads
            
            await self.page.wait_for_selector('input[name="password"]', timeout=20000)
            password_field = self.page.locator('input[name="password"]')
            await password_field.clear()
            await password_field.fill(self.password)
            
            # Click Login button
            login_button = self.page.locator('xpath=//span[text()="Log in"]')
            await login_button.click()
            
            # Wait for successful login (check for home timeline)
            logger.info("Waiting for login to complete...")
            await self.page.wait_for_selector('[data-testid="primaryColumn"]', timeout=30000)
            
            logger.info("Successfully logged into Twitter!")
            await asyncio.sleep(3)  # Additional wait to ensure full page load
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    async def post_tweet(self, tweet_text: str) -> bool:
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
            if "home" not in self.page.url:
                await self.page.goto("https://twitter.com/home")
                await asyncio.sleep(3)
            
            # Method 1: Try the standard compose box
            success = await self._try_compose_method_1(tweet_text)
            if success:
                return True
            
            # Method 2: Try alternative selectors
            success = await self._try_compose_method_2(tweet_text)
            if success:
                return True
            
            # Method 3: Try using keyboard shortcuts
            success = await self._try_compose_method_3(tweet_text)
            if success:
                return True
            
            logger.error("All posting methods failed")
            return False
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return False
    
    async def _try_compose_method_1(self, tweet_text: str) -> bool:
        """Method 1: Standard compose box"""
        try:
            logger.info("Trying compose method 1...")
            
            # Find and click the tweet compose area
            tweet_compose = self.page.locator('[data-testid="tweetTextarea_0"]')
            await tweet_compose.wait_for(timeout=10000)
            await tweet_compose.click()
            await asyncio.sleep(1)
            
            # Clear and type the tweet
            await tweet_compose.clear()
            await tweet_compose.fill(tweet_text)
            await asyncio.sleep(2)
            
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
                    post_button = self.page.locator(selector)
                    await post_button.wait_for(timeout=5000)
                    
                    # Scroll into view and click
                    await post_button.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    
                    # Try regular click first
                    try:
                        await post_button.click()
                    except:
                        # If regular click fails, try force click
                        await post_button.click(force=True)
                    
                    await asyncio.sleep(3)
                    logger.info("Method 1 successful!")
                    return True
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Method 1 failed: {e}")
            return False
    
    async def _try_compose_method_2(self, tweet_text: str) -> bool:
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
                    tweet_compose = self.page.locator(selector)
                    await tweet_compose.wait_for(timeout=5000)
                    break
                except:
                    continue
            
            if not tweet_compose:
                return False
            
            # Click and enter text
            await tweet_compose.click()
            await asyncio.sleep(1)
            await tweet_compose.clear()
            await tweet_compose.fill(tweet_text)
            await asyncio.sleep(2)
            
            # Try to find and click post button
            post_selectors = [
                'button[data-testid="tweetButtonInline"]',
                'button[data-testid="tweetButton"]',
                'xpath=//button[contains(text(), "Post")]',
                'xpath=//button[contains(text(), "Tweet")]',
                'xpath=//*[@role="button" and contains(text(), "Post")]',
                'xpath=//*[@role="button" and contains(text(), "Tweet")]'
            ]
            
            for selector in post_selectors:
                try:
                    post_button = self.page.locator(selector)
                    await post_button.wait_for(timeout=5000)
                    
                    # Try clicking
                    try:
                        await post_button.click()
                    except:
                        await post_button.click(force=True)
                    
                    await asyncio.sleep(3)
                    logger.info("Method 2 successful!")
                    return True
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Method 2 failed: {e}")
            return False
    
    async def _try_compose_method_3(self, tweet_text: str) -> bool:
        """Method 3: Using keyboard shortcuts"""
        try:
            logger.info("Trying compose method 3 (keyboard shortcuts)...")
            
            # Find compose area with multiple selectors
            compose_selectors = [
                '[data-testid="tweetTextarea_0"]',
                '[placeholder*="What"]',
                '[contenteditable="true"]'
            ]
            
            tweet_compose = None
            for selector in compose_selectors:
                try:
                    tweet_compose = self.page.locator(selector)
                    await tweet_compose.wait_for(timeout=5000)
                    break
                except:
                    continue
            
            if not tweet_compose:
                return False
            
            # Click and enter text
            await tweet_compose.click()
            await asyncio.sleep(1)
            await tweet_compose.clear()
            await tweet_compose.fill(tweet_text)
            await asyncio.sleep(2)
            
            # Use Ctrl+Enter to post (Twitter keyboard shortcut)
            await self.page.keyboard.press("Control+Enter")
            
            await asyncio.sleep(3)
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
    
    async def run_bot(self, json_file_path: str, post_interval: int = 10, max_tweets: int = None):
        """
        Run the Twitter bot to post tweets from JSON file
        
        Args:
            json_file_path: Path to the JSON file containing tweets
            post_interval: Interval between posts in seconds (default: 10)
            max_tweets: Maximum number of tweets to post (default: all)
        """
        try:
            # Setup browser
            await self.setup_browser()
            
            # Load tweets from JSON
            tweets_data = self.load_tweets_from_json(json_file_path)
            
            if not tweets_data:
                logger.error("No tweets loaded. Exiting...")
                return
            
            # Limit tweets if specified
            if max_tweets:
                tweets_data = tweets_data[:max_tweets]
            
            # Login to Twitter
            await self.login_to_twitter()
            
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
                    if await self.post_tweet(tweet_text):
                        successful_posts += 1
                        logger.info(f"✅ Tweet {i} posted successfully")
                    else:
                        failed_posts += 1
                        logger.error(f"❌ Failed to post tweet {i}")
                    
                    # Wait before posting the next tweet (except for the last one)
                    if i < len(tweets_data):
                        logger.info(f"Waiting {post_interval} seconds before next tweet...")
                        await asyncio.sleep(post_interval)
                    
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
            await asyncio.sleep(10)
            await self.quit()
    
    async def quit(self):
        """Close the browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

async def main():
    """Main function to run the Twitter bot"""
    
    # Configuration - UPDATE THESE VALUES
    TWITTER_USERNAME = "@abhay_emani"  # Your Twitter username or email
    TWITTER_PASSWORD = "monarch@8125887355"             # Your Twitter password
    JSON_FILE_PATH = r"C:\Users\ABHAYEYSVS\Desktop\Automation\generated_tweets.json"            # Path to your tweets JSON file
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
        await bot.run_bot(
            json_file_path=JSON_FILE_PATH,
            post_interval=POST_INTERVAL,
            max_tweets=MAX_TWEETS
        )
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        await bot.quit()

if __name__ == "__main__":
    # First, check if browsers are installed
    import subprocess
    import sys
    
    print("Checking Playwright browser installation...")
    try:
        result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully!")
        else:
            print("⚠️ There might be an issue with browser installation, but continuing...")
    except subprocess.TimeoutExpired:
        print("⚠️ Browser installation is taking longer than expected, but continuing...")
    except Exception as e:
        print(f"⚠️ Could not install browsers automatically: {e}")
        print("Please run manually: playwright install chromium")
    
    asyncio.run(main())