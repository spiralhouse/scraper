import logging
from typing import Optional, Set
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


class ResponseParser:
    """
    Parses HTML responses to extract links and other relevant information.

    This class is responsible for processing HTML content, extracting all links,
    normalizing them to absolute URLs, and filtering out non-HTTP/HTTPS links.
    """

    def __init__(self, base_url: str):
        """
        Initialize the ResponseParser with a base URL.

        Args:
            base_url: The base URL used to resolve relative links
        """
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def extract_links(self, html_content: str) -> Set[str]:
        """
        Extract all links from HTML content.

        Args:
            html_content: HTML content as a string

        Returns:
            Set of unique absolute URLs found in the HTML
        """
        if not html_content:
            self.logger.warning("Received empty HTML content")
            return set()

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = set()

            # Extract links from anchor tags
            for anchor in soup.find_all('a', href=True):
                href = anchor['href']
                absolute_url = self._normalize_url(href)
                if absolute_url:
                    links.add(absolute_url)

            # Extract links from other tags that might contain URLs
            for tag_name, attr_name in [('img', 'src'), ('script', 'src'), ('link', 'href')]:
                for tag in soup.find_all(tag_name, {attr_name: True}):
                    href = tag[attr_name]
                    absolute_url = self._normalize_url(href)
                    if absolute_url:
                        links.add(absolute_url)

            return links

        except Exception as e:
            self.logger.error(f"Error parsing HTML content: {str(e)}")
            return set()

    def _normalize_url(self, url: str) -> Optional[str]:
        """
        Normalize a URL to an absolute URL and filter out non-HTTP(S) URLs.

        Args:
            url: The URL to normalize (can be absolute or relative)

        Returns:
            Normalized absolute URL or None if the URL should be excluded
        """
        # Skip fragment-only URLs, javascript: URLs, mailto: URLs, etc.
        if not url or url.startswith('#') or ':' in url and not url.startswith(('http://', 'https://')):
            return None

        # Convert to absolute URL
        absolute_url = urljoin(self.base_url, url)

        # Remove fragments (anchors)
        absolute_url = absolute_url.split('#')[0]

        # Validate URL format
        try:
            parsed = urlparse(absolute_url)
            if not parsed.scheme or not parsed.netloc:
                return None

            # Ensure it's HTTP or HTTPS
            if parsed.scheme not in ('http', 'https'):
                return None

            return absolute_url
        except Exception:
            return None

    def extract_page_title(self, html_content: str) -> Optional[str]:
        """
        Extract the title of the page from HTML content.

        Args:
            html_content: HTML content as a string

        Returns:
            Page title or None if not found
        """
        if not html_content:
            return None

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            return title_tag.text.strip() if title_tag else None
        except Exception:
            return None

    def extract_metadata(self, html_content: str) -> dict:
        """
        Extract metadata from HTML content (meta tags).

        Args:
            html_content: HTML content as a string

        Returns:
            Dictionary of metadata key-value pairs
        """
        metadata = {}

        if not html_content:
            return metadata

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract standard meta tags
            for meta in soup.find_all('meta'):
                if meta.get('name') and meta.get('content'):
                    metadata[meta['name'].lower()] = meta['content']
                elif meta.get('property') and meta.get('content'):
                    metadata[meta['property'].lower()] = meta['content']

            return metadata
        except Exception as e:
            self.logger.error(f"Error extracting metadata: {str(e)}")
            return metadata
