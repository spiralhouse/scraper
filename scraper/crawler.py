import asyncio
import logging
from typing import Set, Dict, Any, Optional, Callable, List
from urllib.parse import urlparse
import time

from scraper.cache_manager import Cache
from scraper.request_handler import RequestHandler
from scraper.response_parser import ResponseParser
from scraper.robots_parser import RobotsParser
from scraper.sitemap_parser import SitemapParser


class Crawler:
    """
    Main component that orchestrates the web crawling process.
    
    This class coordinates the RequestHandler, ResponseParser, and Cache
    to recursively crawl web pages, extract links, and store results.
    """
    
    def __init__(
        self,
        max_depth: int = 3,
        allow_external_domains: bool = False,
        allow_subdomains: bool = True,
        concurrency_limit: int = 10,
        use_cache: bool = True,
        cache_dir: Optional[str] = None,
        request_delay: float = 0.1,
        user_agent: str = "ScraperBot (https://github.com/johnburbridge/scraper)",
        on_page_crawled: Optional[Callable[[str, dict], None]] = None,
        respect_robots_txt: bool = True,
        use_sitemap: bool = False,
        max_subsitemaps: int = 5,
        sitemap_timeout: int = 30
    ):
        """
        Initialize the Crawler with configurable parameters.
        
        Args:
            max_depth: Maximum recursion depth for crawling (default: 3)
            allow_external_domains: Whether to follow links to other domains (default: False)
            allow_subdomains: Whether to follow links to subdomains (default: True)
            concurrency_limit: Maximum number of concurrent requests (default: 10)
            use_cache: Whether to use caching (default: True)
            cache_dir: Directory for the cache database (if None, uses default)
            request_delay: Delay between requests in seconds (default: 0.1)
            user_agent: User-agent string to identify the crawler
            on_page_crawled: Optional callback function called when a page is crawled
            respect_robots_txt: Whether to respect robots.txt rules (default: True)
            use_sitemap: Whether to use sitemap.xml for URL discovery (default: False)
            max_subsitemaps: Maximum number of sub-sitemaps to process (default: 5)
            sitemap_timeout: Timeout in seconds for sitemap processing (default: 30)
        """
        self.max_depth = max_depth
        self.allow_external_domains = allow_external_domains
        self.allow_subdomains = allow_subdomains
        self.concurrency_limit = concurrency_limit
        self.request_delay = request_delay
        self.user_agent = user_agent
        self.on_page_crawled = on_page_crawled
        self.respect_robots_txt = respect_robots_txt
        self.use_sitemap = use_sitemap
        self.max_subsitemaps = max_subsitemaps
        self.sitemap_timeout = sitemap_timeout
        
        self.logger = logging.getLogger(__name__)
        self.cache = Cache(use_persistent=use_cache, cache_dir=cache_dir)
        self.request_handler = RequestHandler(user_agent=user_agent)
        
        # Initialize robots.txt parser if needed
        self.robots_parser = RobotsParser(user_agent) if respect_robots_txt else None
        
        # Initialize sitemap parser if needed
        self.sitemap_parser = SitemapParser(
            user_agent, 
            max_subsitemaps=max_subsitemaps, 
            overall_timeout=sitemap_timeout
        ) if use_sitemap else None
        
        # Stats tracking
        self.stats = {
            "pages_crawled": 0,
            "pages_skipped": 0,
            "start_time": 0,
            "end_time": 0
        }
        
        # Sets to track URLs
        self.visited_urls: Set[str] = set()
        self.queue: Set[str] = set()
        
        # Semaphore for controlling concurrency
        self.semaphore = asyncio.Semaphore(concurrency_limit)
    
    def _is_allowed_domain(self, url: str, base_domain: str) -> bool:
        """
        Check if a URL's domain is allowed based on configuration.
        
        Args:
            url: The URL to check
            base_domain: The base domain of the initial URL
            
        Returns:
            True if the domain is allowed, False otherwise
        """
        parsed_url = urlparse(url)
        url_domain = parsed_url.netloc.lower()
        
        # Always allow the exact same domain
        if url_domain == base_domain:
            return True
            
        # Check for subdomains if allowed
        if self.allow_subdomains and url_domain.endswith(f".{base_domain}"):
            return True
            
        # Check for external domains if allowed
        if self.allow_external_domains:
            return True
            
        return False
    
    async def _crawl_url(self, url: str, depth: int, base_domain: str) -> Set[str]:
        """
        Crawl a single URL and extract links.
        
        Args:
            url: The URL to crawl
            depth: Current recursion depth
            base_domain: The base domain of the initial URL
            
        Returns:
            Set of discovered URLs
        """
        # Skip if already visited
        if url in self.visited_urls:
            return set()
            
        self.visited_urls.add(url)
        
        # Check robots.txt rules if enabled
        if self.respect_robots_txt and self.robots_parser:
            if not self.robots_parser.is_allowed(url):
                self.logger.info(f"Skipping {url} (disallowed by robots.txt)")
                return set()
            
            # Adjust request delay based on crawl-delay directive
            robots_delay = self.robots_parser.get_crawl_delay(url)
            delay = max(self.request_delay, robots_delay)
        else:
            delay = self.request_delay
        
        # Check cache first
        cached_response = self.cache.get(url)
        
        if cached_response:
            content, status_code, headers = cached_response
            self.logger.info(f"Using cached response for {url}")
            self.stats["pages_skipped"] += 1
        else:
            # Respect request delay
            await asyncio.sleep(delay)
            
            # Make request
            async with self.semaphore:
                content, status_code, headers = self.request_handler.get(url)
            
            if content and status_code == 200:
                # Cache successful response
                self.cache.set(url, content, status_code, headers)
            else:
                self.logger.warning(f"Failed to fetch {url}, status: {status_code}")
                return set()
        
        # Update stats
        self.stats["pages_crawled"] += 1
        
        # Parse response
        parser = ResponseParser(base_url=url)
        extracted_links = parser.extract_links(content)
        
        # Get metadata
        title = parser.extract_page_title(content)
        metadata = parser.extract_metadata(content)
        
        # Create result object
        page_data = {
            "url": url,
            "status_code": status_code,
            "title": title,
            "depth": depth,
            "metadata": metadata,
            "links": list(extracted_links)
        }
        
        # Call the callback if provided
        if self.on_page_crawled:
            self.on_page_crawled(url, page_data)
        
        # Filter links by domain
        allowed_links = {
            link for link in extracted_links 
            if self._is_allowed_domain(link, base_domain)
        }
        
        return allowed_links
    
    async def _crawl_recursive(self, url: str, depth: int, base_domain: str) -> None:
        """
        Recursively crawl URLs up to the maximum depth.
        
        Args:
            url: The URL to start crawling from
            depth: Current recursion depth
            base_domain: The base domain of the initial URL
        """
        if depth > self.max_depth:
            return
            
        discovered_links = await self._crawl_url(url, depth, base_domain)
        
        # Filter out already visited or queued links
        new_links = discovered_links - self.visited_urls - self.queue
        self.queue.update(new_links)
        
        # Create tasks for each new link
        tasks = []
        for link in new_links:
            task = asyncio.create_task(self._crawl_recursive(link, depth + 1, base_domain))
            tasks.append(task)
            
        if tasks:
            await asyncio.gather(*tasks)
    
    async def crawl_async(self, start_url: str) -> Dict[str, Any]:
        """
        Start an asynchronous crawl from the given URL.
        
        Args:
            start_url: The URL to start crawling from
            
        Returns:
            Dictionary with crawling statistics
        """
        self.logger.info(f"Starting crawl from {start_url}")
        
        # Reset state
        self.visited_urls.clear()
        self.queue.clear()
        self.stats["pages_crawled"] = 0
        self.stats["pages_skipped"] = 0
        self.stats["start_time"] = time.time()
        
        # Parse base domain from start URL
        parsed_start_url = urlparse(start_url)
        base_domain = parsed_start_url.netloc.lower()
        
        # Use sitemap for URL discovery if enabled
        initial_urls = set([start_url])
        sitemap_urls = set()
        
        if self.use_sitemap and self.sitemap_parser:
            self.logger.info(f"Fetching sitemap for {start_url}")
            sitemap_urls = self.sitemap_parser.get_urls_from_domain(start_url)
            
            # Filter URLs by domain restrictions
            filtered_sitemap_urls = {
                url for url in sitemap_urls
                if self._is_allowed_domain(url, base_domain)
            }
            
            if filtered_sitemap_urls:
                self.logger.info(f"Found {len(filtered_sitemap_urls)} URLs from sitemap")
                initial_urls.update(filtered_sitemap_urls)
                self.stats["sitemap_urls_found"] = len(sitemap_urls)
                self.stats["sitemap_urls_used"] = len(filtered_sitemap_urls)
        
        # Start crawling from all initial URLs
        tasks = []
        for url in initial_urls:
            task = asyncio.create_task(self._crawl_recursive(url, 1, base_domain))
            tasks.append(task)
            
        if tasks:
            await asyncio.gather(*tasks)
        
        # Update stats
        self.stats["end_time"] = time.time()
        self.stats["duration"] = self.stats["end_time"] - self.stats["start_time"]
        self.stats["total_urls"] = len(self.visited_urls)
        
        self.logger.info(f"Crawl completed. Visited {self.stats['total_urls']} URLs in {self.stats['duration']:.2f} seconds")
        
        return self.stats
    
    def crawl(self, start_url: str) -> Dict[str, Any]:
        """
        Start a synchronous crawl from the given URL.
        
        Args:
            start_url: The URL to start crawling from
            
        Returns:
            Dictionary with crawling statistics
        """
        return asyncio.run(self.crawl_async(start_url))
    
    def close(self) -> None:
        """Clean up resources used by the crawler."""
        self.request_handler.close()
        self.cache.close() 