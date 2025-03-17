import logging
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
    
    def __init__(self, user_agent: str):
        """
        Initialize the SitemapParser.
        
        Args:
            user_agent: The user agent string to use for fetching sitemaps
        """
        self.user_agent = user_agent
        self.logger = logging.getLogger(__name__)
        self.headers = {'User-Agent': user_agent}
    
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
            return sitemap_urls
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
    
    def extract_urls_from_sitemap(self, sitemap_url: str) -> Set[str]:
        """
        Extract all URLs from a sitemap or sitemap index.
        
        Args:
            sitemap_url: The URL of the sitemap or sitemap index
            
        Returns:
            Set of URLs found in the sitemap(s)
        """
        urls = set()
        base_url = f"{urlparse(sitemap_url).scheme}://{urlparse(sitemap_url).netloc}"
        
        # Fetch the initial sitemap
        content = self.fetch_sitemap(sitemap_url)
        if not content:
            return urls
        
        # Check if it's a sitemap index
        if self.is_sitemap_index(content):
            # Parse the sitemap index to get the URLs of the sitemaps
            sitemap_urls = self.parse_sitemap_index(content, base_url)
            
            # Process each sitemap
            for url in sitemap_urls:
                sitemap_content = self.fetch_sitemap(url)
                if sitemap_content:
                    # Parse the sitemap and add the URLs to the set
                    url_data_list = self.parse_sitemap(sitemap_content, base_url)
                    for url_data in url_data_list:
                        urls.add(url_data['url'])
        else:
            # It's a regular sitemap, parse it directly
            url_data_list = self.parse_sitemap(content, base_url)
            for url_data in url_data_list:
                urls.add(url_data['url'])
        
        return urls
    
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