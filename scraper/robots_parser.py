import logging
from urllib.parse import urlparse
import requests
from robotexclusionrulesparser import RobotExclusionRulesParser


class RobotsParser:
    """
    Parser for robots.txt files to check if a URL can be crawled.
    
    This class fetches and parses robots.txt files for domains, and provides
    methods to check if a given URL is allowed to be crawled based on the
    rules defined in the robots.txt file.
    """
    
    def __init__(self, user_agent: str):
        """
        Initialize the RobotsParser.
        
        Args:
            user_agent: The user agent string to use for fetching robots.txt
                        and for checking permissions
        """
        self.user_agent = user_agent
        self.logger = logging.getLogger(__name__)
        self.parsers = {}  # Cache of parsed robots.txt files keyed by domain
        self.fetched_domains = set()  # Set of domains for which robots.txt has been fetched
        self.default_crawl_delay = 0  # Default crawl delay (seconds)
    
    def get_robots_url(self, url: str) -> str:
        """
        Get the URL of the robots.txt file for a given URL.
        
        Args:
            url: The URL to get the robots.txt URL for
            
        Returns:
            URL to the robots.txt file
        """
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    
    def fetch_robots_txt(self, domain_url: str) -> bool:
        """
        Fetch and parse the robots.txt file for a domain.
        
        Args:
            domain_url: URL of the website (not the robots.txt file)
            
        Returns:
            True if robots.txt was successfully fetched and parsed, False otherwise
        """
        parsed_url = urlparse(domain_url)
        domain = parsed_url.netloc
        
        # Skip if already fetched
        if domain in self.fetched_domains:
            return domain in self.parsers
        
        self.fetched_domains.add(domain)
        robots_url = self.get_robots_url(domain_url)
        
        try:
            response = requests.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                parser = RobotExclusionRulesParser()
                parser.parse(response.text)
                self.parsers[domain] = parser
                self.logger.info(f"Successfully parsed robots.txt for {domain}")
                return True
            elif response.status_code == 404:
                # No robots.txt file, assume everything is allowed
                self.logger.info(f"No robots.txt found for {domain} (404)")
                parser = RobotExclusionRulesParser()
                parser.parse("")  # Empty robots.txt means everything is allowed
                self.parsers[domain] = parser
                return True
            else:
                self.logger.warning(f"Failed to fetch robots.txt for {domain}: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error fetching robots.txt for {domain}: {str(e)}")
            return False
    
    def is_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed to be crawled.
        
        Args:
            url: The URL to check
            
        Returns:
            True if the URL is allowed to be crawled, False otherwise
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Fetch robots.txt if not already fetched
        if domain not in self.parsers and not self.fetch_robots_txt(url):
            # If fetch fails, assume allowed (permissive default)
            self.logger.warning(f"Assuming URL is allowed due to robots.txt fetch failure: {url}")
            return True
        
        # Get the parser for this domain
        if domain in self.parsers:
            return self.parsers[domain].is_allowed(self.user_agent, url)
        
        # Default permissive case
        return True
    
    def get_crawl_delay(self, url: str) -> float:
        """
        Get the crawl delay specified in robots.txt.
        
        Args:
            url: The URL to check
            
        Returns:
            Crawl delay in seconds, or the default if not specified
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Fetch robots.txt if not already fetched
        if domain not in self.parsers and not self.fetch_robots_txt(url):
            return self.default_crawl_delay
        
        # Get the parser for this domain
        if domain in self.parsers:
            delay = self.parsers[domain].get_crawl_delay(self.user_agent)
            return delay if delay is not None else self.default_crawl_delay
        
        return self.default_crawl_delay 