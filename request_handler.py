import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Dict, Optional, Union, Tuple


class RequestHandler:
    """
    Handles HTTP requests with proper headers, retries, and timeouts.
    
    This class is responsible for making HTTP requests to URLs, handling
    retries on failure, setting appropriate timeouts, and managing headers
    including user-agent information.
    """

    def __init__(
            self,
            timeout: int = 30,
            max_retries: int = 3,
            backoff_factor: float = 0.3,
            user_agent: str = "ScraperBot (https://github.com/yourusername/scraper)"
    ):
        """
        Initialize the RequestHandler with configurable parameters.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            backoff_factor: Backoff factor for retry delays
            user_agent: User-agent string to identify the scraper
        """
        self.timeout = timeout
        self.session = self._create_session(max_retries, backoff_factor)
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.logger = logging.getLogger(__name__)

    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """
        Create and configure a requests session with retry capabilities.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retry delays
            
        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def get(self, url: str, custom_headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], int, Dict]:
        """
        Make a GET request to the specified URL.
        
        Args:
            url: The URL to request
            custom_headers: Optional additional headers to send with the request
            
        Returns:
            Tuple containing (content, status_code, headers)
            content will be None if request fails
        """
        headers = self.headers.copy()
        if custom_headers:
            headers.update(custom_headers)

        try:
            self.logger.info(f"Requesting URL: {url}")
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout
            )
            return response.text, response.status_code, dict(response.headers)

        except requests.RequestException as e:
            self.logger.error(f"Error requesting {url}: {str(e)}")
            return None, 0, {}

    def close(self) -> None:
        """Close the requests session to free resources."""
        self.session.close()

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure resources are cleaned up when used as context manager."""
        self.close()