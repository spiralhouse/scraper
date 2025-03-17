import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup


class SitemapParser:
    """
    Parser for XML sitemaps to extract URLs for crawling.
    
    This class fetches and parses XML sitemaps, including sitemap indexes,
    and provides methods to extract URLs and their metadata for crawling.
    """
    
    def __init__(self, user_agent: str, max_subsitemaps: int = 5, overall_timeout: int = 30):
        """
        Initialize the SitemapParser.
        
        Args:
            user_agent: The user agent string to use for fetching sitemaps
            max_subsitemaps: Maximum number of sub-sitemaps to process from an index (default: 5)
            overall_timeout: Maximum time in seconds for the entire sitemap processing (default: 30)
        """
        self.user_agent = user_agent
        self.logger = logging.getLogger(__name__)
        self.headers = {'User-Agent': user_agent}
        self.max_subsitemaps = max_subsitemaps
        self.overall_timeout = overall_timeout
    
    def get_sitemap_url(self, url: str) -> str:
        """
        Get the URL of the sitemap.xml file for a given URL.
        
        Args:
            url: The URL to get the sitemap URL for
            
        Returns:
            URL to the sitemap.xml file
        """
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml"
    
    def fetch_sitemap(self, sitemap_url: str) -> Optional[str]:
        """
        Fetch a sitemap from the given URL.
        
        Args:
            sitemap_url: URL of the sitemap
            
        Returns:
            The content of the sitemap, or None if it couldn't be fetched
        """
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"Successfully fetched sitemap from {sitemap_url}")
                return response.text
            else:
                self.logger.warning(f"Failed to fetch sitemap from {sitemap_url}: HTTP {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error fetching sitemap from {sitemap_url}: {str(e)}")
            return None

    async def fetch_sitemap_async(self, sitemap_url: str) -> Optional[str]:
        """
        Fetch a sitemap asynchronously from the given URL.
        
        Args:
            sitemap_url: URL of the sitemap
            
        Returns:
            The content of the sitemap, or None if it couldn't be fetched
        """
        try:
            # Use synchronous requests library with a separate thread 
            # to avoid adding aiohttp as a dependency
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None, lambda: self.fetch_sitemap(sitemap_url)
            )
            return content
        except Exception as e:
            self.logger.error(f"Error fetching sitemap asynchronously from {sitemap_url}: {str(e)}")
            return None

    def is_sitemap_index(self, content: str) -> bool:
        """
        Check if the given content is a sitemap index.
        
        Args:
            content: The content of the sitemap
            
        Returns:
            True if the content is a sitemap index, False otherwise
        """
        try:
            soup = BeautifulSoup(content, 'lxml-xml')
            return soup.find('sitemapindex') is not None
        except Exception as e:
            self.logger.error(f"Error checking if content is sitemap index: {str(e)}")
            return False
    
    def parse_sitemap_index(self, content: str, base_url: str) -> List[str]:
        """
        Parse a sitemap index and return the URLs of the sitemaps it contains.
        
        Args:
            content: The content of the sitemap index
            base_url: The base URL to resolve relative URLs
            
        Returns:
            List of sitemap URLs
        """
        try:
            soup = BeautifulSoup(content, 'lxml-xml')
            sitemap_tags = soup.find_all('sitemap')
            sitemap_urls = []
            
            for sitemap in sitemap_tags:
                loc = sitemap.find('loc')
                if loc and loc.text:
                    # Make sure the URL is absolute
                    url = urljoin(base_url, loc.text.strip())
                    sitemap_urls.append(url)
            
            self.logger.info(f"Found {len(sitemap_urls)} sitemaps in sitemap index")
            # Limit the number of sub-sitemaps to process
            limited_urls = sitemap_urls[:self.max_subsitemaps]
            if len(sitemap_urls) > self.max_subsitemaps:
                self.logger.info(f"Limiting to {self.max_subsitemaps} sub-sitemaps out of {len(sitemap_urls)}")
            
            return limited_urls
        except Exception as e:
            self.logger.error(f"Error parsing sitemap index: {str(e)}")
            return []
    
    def parse_sitemap(self, content: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Parse a sitemap and return the URLs it contains with metadata.
        
        Args:
            content: The content of the sitemap
            base_url: The base URL to resolve relative URLs
            
        Returns:
            List of dictionaries containing URL and metadata
        """
        try:
            soup = BeautifulSoup(content, 'lxml-xml')
            url_tags = soup.find_all('url')
            urls = []
            
            for url in url_tags:
                loc = url.find('loc')
                if loc and loc.text:
                    # Make sure the URL is absolute
                    url_str = urljoin(base_url, loc.text.strip())
                    
                    # Extract metadata
                    lastmod = url.find('lastmod')
                    changefreq = url.find('changefreq')
                    priority = url.find('priority')
                    
                    url_data = {
                        'url': url_str,
                        'lastmod': lastmod.text.strip() if lastmod else None,
                        'changefreq': changefreq.text.strip() if changefreq else None,
                        'priority': float(priority.text.strip()) if priority else None
                    }
                    
                    urls.append(url_data)
            
            self.logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
        except Exception as e:
            self.logger.error(f"Error parsing sitemap: {str(e)}")
            return []
    
    async def process_sitemap(self, sitemap_url: str, base_url: str) -> Set[str]:
        """
        Process a single sitemap and extract URLs.
        
        Args:
            sitemap_url: URL of the sitemap
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Set of URLs found in the sitemap
        """
        urls = set()
        content = await self.fetch_sitemap_async(sitemap_url)
        if content:
            url_data_list = self.parse_sitemap(content, base_url)
            for url_data in url_data_list:
                urls.add(url_data['url'])
        return urls
    
    async def extract_urls_from_sitemap_async(self, sitemap_url: str) -> Set[str]:
        """
        Extract all URLs from a sitemap or sitemap index asynchronously.
        
        Args:
            sitemap_url: The URL of the sitemap or sitemap index
            
        Returns:
            Set of URLs found in the sitemap(s)
        """
        start_time = time.time()
        urls = set()
        base_url = f"{urlparse(sitemap_url).scheme}://{urlparse(sitemap_url).netloc}"
        
        # Fetch the initial sitemap
        content = await self.fetch_sitemap_async(sitemap_url)
        if not content:
            return urls
        
        # If we've exceeded the timeout, return what we have
        if time.time() - start_time > self.overall_timeout:
            self.logger.warning(f"Timeout exceeded while processing sitemap: {sitemap_url}")
            return urls
        
        # Check if it's a sitemap index
        if self.is_sitemap_index(content):
            # Parse the sitemap index to get the URLs of the sitemaps
            sitemap_urls = self.parse_sitemap_index(content, base_url)
            
            # Process each sitemap concurrently
            tasks = []
            for url in sitemap_urls:
                # Check timeout before starting a new task
                if time.time() - start_time > self.overall_timeout:
                    self.logger.warning(f"Timeout exceeded while processing sub-sitemaps")
                    break
                tasks.append(self.process_sitemap(url, base_url))
            
            if tasks:
                # Wait for all tasks to complete or timeout
                try:
                    results = await asyncio.gather(*tasks)
                    for result in results:
                        urls.update(result)
                except asyncio.TimeoutError:
                    self.logger.warning("Timeout while processing sub-sitemaps")
        else:
            # It's a regular sitemap, parse it directly
            url_data_list = self.parse_sitemap(content, base_url)
            for url_data in url_data_list:
                urls.add(url_data['url'])
        
        self.logger.info(f"Extracted {len(urls)} URLs from sitemap(s) in {time.time() - start_time:.2f} seconds")
        return urls
    
    def extract_urls_from_sitemap(self, sitemap_url: str) -> Set[str]:
        """
        Extract all URLs from a sitemap or sitemap index.
        
        Args:
            sitemap_url: The URL of the sitemap or sitemap index
            
        Returns:
            Set of URLs found in the sitemap(s)
        """
        try:
            # Run the async method in an event loop with a timeout
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            task = self.extract_urls_from_sitemap_async(sitemap_url)
            future = asyncio.ensure_future(task, loop=loop)
            
            # Add overall timeout
            try:
                urls = loop.run_until_complete(
                    asyncio.wait_for(future, timeout=self.overall_timeout)
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"Global timeout reached while processing sitemap: {sitemap_url}")
                # Return any URLs we collected before timeout
                urls = set()
                if future.done():
                    urls = future.result()
                else:
                    future.cancel()
            finally:
                loop.close()
                
            return urls
        except Exception as e:
            self.logger.error(f"Error extracting URLs from sitemap: {str(e)}")
            return set()
    
    def get_urls_from_domain(self, domain_url: str) -> Set[str]:
        """
        Get all URLs from a domain's sitemap.
        
        Args:
            domain_url: The URL of the domain (not the sitemap)
            
        Returns:
            Set of URLs found in the domain's sitemap(s)
        """
        sitemap_url = self.get_sitemap_url(domain_url)
        return self.extract_urls_from_sitemap(sitemap_url) 