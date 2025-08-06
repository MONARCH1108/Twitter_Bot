import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import ollama
import warnings
warnings.filterwarnings("ignore")

class GuardianCrawler:
    def __init__(self, model_name="llama3.2:latest"):
        self.base_url = "https://www.theguardian.com"
        self.session = requests.Session()
        self.lock = threading.Lock()
        self.model_name = model_name
        
        # Initialize Ollama client
        self.ollama_client = ollama.Client()
        
        # Test Ollama connection
        try:
            response = self.ollama_client.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': 'Hello, are you working?'}
            ])
            print(f"✅ Ollama connection successful with model: {self.model_name}")
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            print(f"Make sure Ollama is running and the model is installed: ollama run {self.model_name}")
        
        # Enhanced headers to appear more like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Guardian URL patterns for better article discovery
        self.url_patterns = {
            'world': [
                'https://www.theguardian.com/world',
                'https://www.theguardian.com/world/europe-news',
                'https://www.theguardian.com/world/americas',
                'https://www.theguardian.com/world/asia-pacific'
            ],
            'uk': [
                'https://www.theguardian.com/uk-news',
                'https://www.theguardian.com/politics',
                'https://www.theguardian.com/society'
            ],
            'business': [
                'https://www.theguardian.com/business',
                'https://www.theguardian.com/business/economics',
                'https://www.theguardian.com/technology'
            ],
            'environment': [
                'https://www.theguardian.com/environment',
                'https://www.theguardian.com/environment/climate-change'
            ],
            'science': [
                'https://www.theguardian.com/science',
                'https://www.theguardian.com/science/medical-research'
            ],
            'culture': [
                'https://www.theguardian.com/culture',
                'https://www.theguardian.com/film',
                'https://www.theguardian.com/books'
            ],
            'sport': [
                'https://www.theguardian.com/sport',
                'https://www.theguardian.com/football'
            ]
        }
        
    def discover_article_urls(self, base_urls, max_per_category=5):
        """Discover actual article URLs from category pages - PARALLELIZED"""
        def fetch_single_category(url):
            try:
                print(f"🔍 Discovering articles from: {url}")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Guardian-specific selectors for article links
                link_selectors = [
                    'a[data-link-name="article"]',
                    '.fc-item__link',
                    '.u-faux-block-link__overlay',
                    'a[href*="/2024/"], a[href*="/2025/"]',
                    '.fc-item__content a',
                    '.card__link',
                    '.headline a',
                    'h3 a[href], h4 a[href]',
                    '.fc-item__header a',
                    'a[data-component="LinkTo"]'
                ]
                
                found_links = set()
                
                for selector in link_selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(url, href)
                            
                            if self.is_valid_article_url(full_url):
                                found_links.add(full_url)
                
                category_articles = list(found_links)[:max_per_category]
                print(f"📄 Found {len(category_articles)} articles from {url}")
                return category_articles
                
            except Exception as e:
                print(f"❌ Error discovering articles from {url}: {e}")
                return []
        
        # PARALLELIZED URL DISCOVERY
        all_articles = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url = {executor.submit(fetch_single_category, url): url for url in base_urls}
            
            for future in as_completed(future_to_url):
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as e:
                    print(f"❌ Error in parallel discovery: {e}")
        
        return list(set(all_articles))
    
    def is_valid_article_url(self, url):
        """Check if URL is a valid Guardian article"""
        if not url or not ('theguardian.com' in url):
            return False
        
        exclude_patterns = [
            '/live/', '/gallery/', '/video/', '/audio/',
            '/newsletters/', '/membership/', '/help/', '/info/',
            '/privacy/', '/terms/', '/contact/', '/jobs/',
            '.json', '.xml', '.css', '.js', '.png', '.jpg',
            '#', 'mailto:', 'tel:', '/crosswords/', '/games/',
            '/weather/', '/travel/offers/', '/guardian-live-events/'
        ]
        
        for pattern in exclude_patterns:
            if pattern in url.lower():
                return False
        
        # Guardian articles typically have year in URL path
        valid_patterns = [
            '/2024/', '/2025/', '/world/', '/uk-news/', '/politics/',
            '/business/', '/environment/', '/science/', '/culture/',
            '/sport/', '/technology/', '/society/', '/education/'
        ]
        
        return any(pattern in url for pattern in valid_patterns)
    
    def extract_content_direct(self, urls):
        """Direct content extraction using requests and BeautifulSoup"""
        print(f"🚀 Processing {len(urls)} URLs with direct extraction...")
        
        def extract_single_article(url):
            try:
                print(f"📖 Processing: {url}")
                response = self.session.get(url, timeout=20)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title - Guardian specific selectors
                title_selectors = [
                    'h1[data-gu-name="headline"]',
                    'h1.content__headline',
                    '.content__main h1',
                    'h1.headline',
                    'h1',
                    '.article-header h1'
                ]
                
                title = ""
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break
                
                # Extract content - Guardian specific selectors
                content_selectors = [
                    '.article-body-commercial-selector p',
                    '.content__article-body p',
                    '[data-gu-name="body"] p',
                    '.article-body p',
                    '.content__main-column p',
                    'div[data-component="body"] p',
                    '.prose p'
                ]
                
                content_parts = []
                for selector in content_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        # Filter out ads and non-content paragraphs
                        if (len(text) > 20 and text not in content_parts and 
                            not text.startswith('Guardian') and
                            'advertisement' not in text.lower() and
                            'subscribe' not in text.lower() and
                            'premium' not in text.lower()):
                            content_parts.append(text)
                    
                    if len(content_parts) >= 5:  # Get at least 5 paragraphs
                        break
                
                content = ' '.join(content_parts)
                
                if len(content) < 100:
                    print(f"⚠️ Content too short for: {url}")
                    return None
                
                article = {
                    'url': url,
                    'title': title or "No title found",
                    'content': content[:3000],
                    'extracted_at': datetime.now().isoformat(),
                    'word_count': len(content.split()),
                    'category': self.categorize_url(url)
                }
                
                print(f"✅ Extracted: {title[:50]}... ({len(content)} chars)")
                return article
                
            except Exception as e:
                print(f"❌ Error extracting {url}: {e}")
                return None
        
        # Process articles with some parallelization but not too aggressive
        articles = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {executor.submit(extract_single_article, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                try:
                    article = future.result()
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"❌ Article extraction error: {e}")
        
        print(f"✅ Successfully extracted {len(articles)} articles")
        return articles
    
    def categorize_url(self, url):
        """Categorize URL based on path"""
        if not url:
            return 'unknown'
        
        if '/world/' in url:
            return 'world'
        elif '/uk-news/' in url:
            return 'uk'
        elif '/politics/' in url:
            return 'politics'
        elif '/business/' in url:
            return 'business'
        elif '/environment/' in url:
            return 'environment'
        elif '/science/' in url:
            return 'science'
        elif '/technology/' in url:
            return 'technology'
        elif '/culture/' in url or '/film/' in url or '/books/' in url:
            return 'culture'
        elif '/sport/' in url or '/football/' in url:
            return 'sport'
        elif '/society/' in url:
            return 'society'
        elif '/education/' in url:
            return 'education'
        else:
            return 'general'
    
    def analyze_with_ollama_fast(self, content, category):
        """OPTIMIZED Ollama analysis"""
        prompt = f"""Analyze this Guardian {category} article briefly. Return only JSON:

Content: {content[:800]}...

{{"headline":"Main headline","summary":"Brief summary","key_topics":["topic1","topic2"],"sentiment":"positive/negative/neutral","urgency":"high/medium/low"}}"""
        
        try:
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': 0.1, 
                    'num_predict': 150,
                    'top_k': 10,
                    'top_p': 0.9
                }
            )
            
            response_text = response['message']['content'].strip()
            
            # Quick JSON extraction
            if response_text.startswith('{'):
                try:
                    return json.loads(response_text)
                except:
                    pass
            
            # Fallback JSON extraction
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
        except Exception as e:
            print(f"❌ Analysis failed for {category}: {e}")
            
        # Fast fallback
        return {
            "headline": "Analysis failed",
            "summary": "Could not analyze content",
            "key_topics": [],
            "sentiment": "neutral",
            "urgency": "medium"
        }
    
    def process_articles_parallel(self, articles):
        """PARALLELIZED article processing with Ollama"""
        print(f"🤖 Analyzing {len(articles)} articles with Ollama...")
        
        def analyze_single_article(article):
            try:
                analysis = self.analyze_with_ollama_fast(article['content'], article['category'])
                
                # Merge analysis with article
                article['ai_analysis'] = analysis
                
                if not article.get('title') and analysis.get('headline'):
                    article['title'] = analysis['headline']
                
                article['summary'] = analysis.get('summary', '')
                article['topics'] = analysis.get('key_topics', [])
                article['sentiment'] = analysis.get('sentiment', 'neutral')
                article['urgency'] = analysis.get('urgency', 'medium')
                
                print(f"✅ Analyzed: {article.get('title', 'Untitled')[:50]}...")
                return article
            except Exception as e:
                print(f"❌ Analysis error: {e}")
                return article
        
        # Process with limited parallelization for Ollama stability
        processed_articles = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_article = {executor.submit(analyze_single_article, article): article for article in articles}
            
            for future in as_completed(future_to_article):
                try:
                    processed_article = future.result()
                    processed_articles.append(processed_article)
                except Exception as e:
                    print(f"❌ Processing error: {e}")
        
        return processed_articles
    
    def calculate_sentiment_distribution(self, articles):
        """Calculate sentiment distribution"""
        sentiments = [a.get('sentiment', 'neutral') for a in articles if a.get('sentiment')]
        
        distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        for sentiment in sentiments:
            if sentiment in distribution:
                distribution[sentiment] += 1
        
        return distribution
    
    def extract_top_topics(self, articles):
        """Extract most common topics"""
        all_topics = []
        for article in articles:
            topics = article.get('topics', [])
            all_topics.extend(topics)
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def generate_summary(self, all_articles):
        """Generate comprehensive summary"""
        if not all_articles:
            return {}
        
        sentiments = [a.get('sentiment', 'neutral') for a in all_articles]
        sentiment_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
        for s in sentiments:
            if s in sentiment_dist:
                sentiment_dist[s] += 1
        
        all_topics = []
        for article in all_articles:
            all_topics.extend(article.get('topics', []))
        
        return {
            'total_articles': len(all_articles),
            'total_categories': len(set(a.get('category', 'unknown') for a in all_articles)),
            'avg_word_count': sum(a.get('word_count', 0) for a in all_articles) / len(all_articles) if all_articles else 0,
            'global_sentiment': sentiment_dist,
            'unique_topics': len(set(all_topics)),
            'all_topics': list(set(all_topics))[:20]
        }
    
    def crawl_all_content(self):
        """Main crawling function"""
        print("📰 Starting Guardian Crawler")
        
        all_data = {
            'crawl_metadata': {
                'started': datetime.now().isoformat(),
                'source': 'The Guardian',
                'method': 'Direct Requests + BeautifulSoup + Ollama',
                'model_used': self.model_name,
                'version': '1.0-GUARDIAN'
            },
            'categories': {},
            'summary': {},
            'all_articles': []
        }
        
        total_articles = []
        
        # Process each category
        for category, urls in self.url_patterns.items():
            print(f"\n🏷️ Processing {category.upper()} category...")
            
            try:
                # Discover article URLs
                article_urls = self.discover_article_urls(urls, max_per_category=5)
                
                if not article_urls:
                    print(f"⚠️ No articles found for {category}")
                    continue
                
                print(f"📄 Found {len(article_urls)} URLs for {category}")
                
                # Direct content extraction
                articles = self.extract_content_direct(article_urls)
                
                if articles:
                    # AI processing
                    processed_articles = self.process_articles_parallel(articles)
                    
                    # Store category data
                    category_data = {
                        'category_name': category,
                        'total_articles': len(processed_articles),
                        'articles': processed_articles,
                        'statistics': {
                            'avg_word_count': sum(a.get('word_count', 0) for a in processed_articles) / len(processed_articles) if processed_articles else 0,
                            'sentiment_distribution': self.calculate_sentiment_distribution(processed_articles),
                            'top_topics': self.extract_top_topics(processed_articles)
                        }
                    }
                    
                    all_data['categories'][category] = category_data
                    total_articles.extend(processed_articles)
                    
                    print(f"✅ {category}: {len(processed_articles)} articles processed")
                
            except Exception as e:
                print(f"❌ Error processing {category}: {e}")
                continue
        
        # Generate final summary
        all_data['all_articles'] = total_articles
        all_data['summary'] = self.generate_summary(total_articles)
        all_data['crawl_metadata']['completed'] = datetime.now().isoformat()
        all_data['crawl_metadata']['success'] = len(total_articles) > 0
        
        return all_data
    
    def save_data(self, data, filename='guardian_crawl_data.json'):
        """Save data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Data saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            return False
    
    def print_results(self, data):
        """Print results summary and complete JSON"""
        print("\n" + "="*80)
        print("📰 THE GUARDIAN CRAWL RESULTS")
        print("="*80)
        
        if not data:
            print("❌ No data available")
            return
        
        # Print summary
        summary = data.get('summary', {})
        print(f"📊 Total Articles: {summary.get('total_articles', 0)}")
        print(f"🏷️ Categories: {summary.get('total_categories', 0)}")
        print(f"📝 Avg Words: {summary.get('avg_word_count', 0):.0f}")
        
        categories = data.get('categories', {})
        for cat_name, cat_data in categories.items():
            print(f"   📂 {cat_name.upper()}: {cat_data.get('total_articles', 0)} articles")
        
        # Print complete JSON
        print("\n" + "="*80)
        print("📄 COMPLETE JSON OUTPUT")
        print("="*80)
        print(json.dumps(data, indent=2, ensure_ascii=False))

# Usage
if __name__ == "__main__":
    print("📰 The Guardian News Crawler - Quality journalism at your fingertips!")
    
    crawler = GuardianCrawler(model_name="llama3.2:latest")
    
    # Run the crawler
    data = crawler.crawl_all_content()
    
    if data and data.get('summary', {}).get('total_articles', 0) > 0:
        # Print results and JSON
        crawler.print_results(data)
        
        # Save data
        crawler.save_data(data, 'guardian_crawl_data.json')
        
        print(f"\n✅ Guardian crawling completed successfully!")
        print(f"💾 File saved: guardian_crawl_data.json")
        
    else:
        print("❌ No articles were successfully extracted.")
        print("Possible issues:")
        print("- Network connectivity")
        print("- Guardian website blocking requests")
        print("- Ollama not running")
        print("- Try running: ollama run llama3.2:latest")