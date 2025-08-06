import json
import requests
import google.generativeai as genai
from typing import List, Dict, Optional
import time
import logging
from dataclasses import dataclass
import asyncio
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """Data class for news articles"""
    url: str
    title: str
    content: str
    summary: str
    topics: List[str]
    sentiment: str
    urgency: str
    word_count: int
    category: str

@dataclass
class TweetWithHashtags:
    """Data class for generated tweet with hashtags"""
    tweet: str
    hashtags: List[str]
    article_url: str
    topics: List[str]

class NewsProcessor:
    """Main class to process news and generate tweets with hashtags"""
    
    def __init__(self, gemini_api_key: str, ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize the processor
        
        Args:
            gemini_api_key: Your Gemini API key
            ollama_base_url: Ollama server URL (default: localhost:11434)
        """
        self.gemini_api_key = gemini_api_key
        self.ollama_base_url = ollama_base_url
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Ollama configuration
        self.ollama_model = "llama3.2:latest"
        
    def load_news_data(self, json_file_path: str) -> List[NewsArticle]:
        """Load and parse news data from JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            articles = []
            for category_name, category_data in data.get('categories', {}).items():
                for article_data in category_data.get('articles', []):
                    try:
                        article = NewsArticle(
                            url=article_data.get('url', ''),
                            title=article_data.get('title', ''),
                            content=article_data.get('content', ''),
                            summary=article_data.get('summary', ''),
                            topics=article_data.get('topics', []),
                            sentiment=article_data.get('sentiment', 'neutral'),
                            urgency=article_data.get('urgency', 'medium'),
                            word_count=article_data.get('word_count', 0),
                            category=article_data.get('category', category_name)
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.warning(f"Error parsing article: {e}")
                        continue
            
            logger.info(f"Loaded {len(articles)} articles from {json_file_path}")
            return articles
            
        except Exception as e:
            logger.error(f"Error loading news data: {e}")
            return []
    
    def generate_tweet_with_ollama(self, article: NewsArticle) -> Optional[str]:
        """Generate tweet using Ollama Llama3.2 model"""
        try:
            # Create a focused prompt for tweet generation
            prompt = f"""
            Create a compelling Twitter/X tweet based on this news article. Keep it under 280 characters, engaging, and informative.

            Title: {article.title}
            Summary: {article.summary}
            Topics: {', '.join(article.topics)}
            Sentiment: {article.sentiment}
            Urgency: {article.urgency}

            Requirements:
            - Keep under 150 characters
            - Make it engaging and shareable
            - Include key information
            - Match the sentiment ({article.sentiment})
            - Don't include hashtags (they will be added separately)
            - Make it sound natural and newsworthy

            Tweet:
            """
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 100,
                        "top_p": 0.9
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                tweet = result.get('response', '').strip()
                
                # Clean up the tweet
                tweet = self._clean_tweet(tweet)
                
                logger.info(f"Generated tweet: {tweet[:50]}...")
                return tweet
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating tweet with Ollama: {e}")
            return None
    
    def generate_hashtags_with_gemini(self, tweet: str, article: NewsArticle) -> List[str]:
        """Generate trending hashtags using Gemini API"""
        try:
            prompt = f"""
            Generate 3-5 trending and relevant hashtags for this tweet about a news article.

            Tweet: {tweet}
            Article Topics: {', '.join(article.topics)}
            Category: {article.category}
            Sentiment: {article.sentiment}
            Urgency: {article.urgency}

            Requirements:
            - Generate 3-5 hashtags maximum
            - Make them trending and relevant to current events
            - Include mix of specific and general hashtags
            - Consider the article category and topics
            - Make them likely to trend on social media
            - Return only the hashtags, one per line, with # symbol
            - No explanations or additional text

            Example format:
            #BreakingNews
            #Politics
            #UK
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            if response.text:
                # Parse hashtags from response
                hashtags = []
                for line in response.text.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('#') and len(line) > 1:
                        hashtags.append(line)
                
                # Limit to 5 hashtags maximum
                hashtags = hashtags[:5]
                
                logger.info(f"Generated hashtags: {', '.join(hashtags)}")
                return hashtags
            else:
                logger.warning("No hashtags generated by Gemini")
                return []
                
        except Exception as e:
            logger.error(f"Error generating hashtags with Gemini: {e}")
            return []
    
    def _clean_tweet(self, tweet: str) -> str:
        """Clean and format the generated tweet"""
        # Remove common prefixes
        prefixes_to_remove = [
            "Tweet:", "Here's a tweet:", "Here's the tweet:",
            "Tweet text:", "Generated tweet:", "Social media post:"
        ]
        
        for prefix in prefixes_to_remove:
            if tweet.lower().startswith(prefix.lower()):
                tweet = tweet[len(prefix):].strip()
        
        # Remove quotes if the entire tweet is wrapped in them
        if tweet.startswith('"') and tweet.endswith('"'):
            tweet = tweet[1:-1].strip()
        
        # Ensure tweet length
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
        
        return tweet
    
    def process_articles(self, articles: List[NewsArticle], max_articles: int = 10) -> List[TweetWithHashtags]:
        """Process articles and generate tweets with hashtags"""
        results = []
        
        # Sort articles by urgency and limit processing
        urgent_articles = [a for a in articles if a.urgency == 'high']
        medium_articles = [a for a in articles if a.urgency == 'medium']
        low_articles = [a for a in articles if a.urgency == 'low']
        
        # Process high urgency first, then medium, then low
        sorted_articles = (urgent_articles + medium_articles + low_articles)[:max_articles]
        
        for i, article in enumerate(sorted_articles, 1):
            logger.info(f"Processing article {i}/{len(sorted_articles)}: {article.title[:50]}...")
            
            # Skip articles with insufficient content
            if not article.summary and not article.content:
                logger.warning(f"Skipping article with no content: {article.title}")
                continue
            
            # Generate tweet with Ollama
            tweet = self.generate_tweet_with_ollama(article)
            if not tweet:
                logger.warning(f"Failed to generate tweet for: {article.title}")
                continue
            
            # Generate hashtags with Gemini
            hashtags = self.generate_hashtags_with_gemini(tweet, article)
            
            # Create result
            result = TweetWithHashtags(
                tweet=tweet,
                hashtags=hashtags,
                article_url=article.url,
                topics=article.topics
            )
            
            results.append(result)
            
            # Small delay to avoid rate limiting
            time.sleep(1)
        
        logger.info(f"Successfully processed {len(results)} articles")
        return results
    
    def save_results(self, results: List[TweetWithHashtags], output_file: str = "generated_tweets.json"):
        """Save results to JSON file"""
        try:
            output_data = []
            for result in results:
                output_data.append({
                    "tweet": result.tweet,
                    "hashtags": result.hashtags,
                    "article_url": result.article_url,
                    "topics": result.topics,
                    "tweet_with_hashtags": f"{result.tweet} {' '.join(result.hashtags)}"
                })
            
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(output_data, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def print_results(self, results: List[TweetWithHashtags]):
        """Print results in a formatted way"""
        print("\n" + "="*80)
        print("GENERATED TWEETS WITH HASHTAGS")
        print("="*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Tweet {i} ---")
            print(f"Tweet: {result.tweet}")
            print(f"Hashtags: {' '.join(result.hashtags)}")
            print(f"Topics: {', '.join(result.topics)}")
            print(f"URL: {result.article_url}")
            print(f"Complete Tweet: {result.tweet} {' '.join(result.hashtags)}")
            print("-" * 60)

def main():
    """Main function to run the news tweet generator"""
    
    # Configuration - UPDATE THESE VALUES
    GEMINI_API_KEY = "AIzaSyBUSkqLOPRWK_viAAJ-tSlSB7NKGDtXU-U"  # Replace with your actual Gemini API key
    JSON_FILE_PATH = r"C:\Users\ABHAYEYSVS\Desktop\Automation\bbc_improved_data.json"  # Path to your JSON file
    OLLAMA_URL = "http://localhost:11434"  # Ollama server URL
    MAX_ARTICLES = 100  # Number of articles to process
    
    # Initialize processor
    processor = NewsProcessor(
        gemini_api_key=GEMINI_API_KEY,
        ollama_base_url=OLLAMA_URL
    )
    
    try:
        # Load news data
        print("Loading news data...")
        articles = processor.load_news_data(JSON_FILE_PATH)
        
        if not articles:
            print("No articles found. Please check your JSON file.")
            return
        
        print(f"Found {len(articles)} articles")
        
        # Process articles
        print(f"\nProcessing {min(MAX_ARTICLES, len(articles))} articles...")
        results = processor.process_articles(articles, max_articles=MAX_ARTICLES)
        
        if not results:
            print("No tweets generated. Please check your configuration.")
            return
        
        # Print results
        processor.print_results(results)
        
        # Save results
        processor.save_results(results)
        
        print(f"\n✅ Successfully generated {len(results)} tweets with hashtags!")
        print("Results saved to 'generated_tweets.json'")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 