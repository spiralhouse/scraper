import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from urllib.parse import urlparse

from scraper.crawler import Crawler
from scraper.request_handler import RequestHandler
from scraper.response_parser import ResponseParser
from scraper.cache_manager import Cache


def async_run(coro):
    """Helper function to run coroutines in tests with a fresh event loop."""
    try:
        # Try to get an existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # Create a new event loop if there isn't one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    finally:
        # Clean up but don't close the loop as it might be reused
        pass


class TestCrawler(unittest.TestCase):
    """Tests for the Crawler class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create and set an event loop for Python 3.9 compatibility
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
            
        self.crawler = Crawler(
            max_depth=2,
            concurrency_limit=5,
            use_cache=False,
            request_delay=0
        )

    def tearDown(self):
        """Clean up after tests."""
        self.crawler.close()
        # Reset the event loop for next test
        try:
            # Get the current event loop
            loop = asyncio.get_event_loop()
            # If the loop is running, stop it
            if loop.is_running():
                loop.stop()
            # Close it
            loop.close()
        except RuntimeError:
            pass  # No event loop exists
        finally:
            # Reset to None to clean up
            asyncio.set_event_loop(None)

    def test_is_allowed_domain_same_domain(self):
        """Test that same domain is always allowed."""
        base_domain = "example.com"
        url = "https://example.com/page"
        
        result = self.crawler._is_allowed_domain(url, base_domain)
        
        self.assertTrue(result)

    def test_is_allowed_domain_subdomain_allowed(self):
        """Test that subdomains are allowed when configured."""
        base_domain = "example.com"
        url = "https://sub.example.com/page"
        self.crawler.allow_subdomains = True
        
        result = self.crawler._is_allowed_domain(url, base_domain)
        
        self.assertTrue(result)

    def test_is_allowed_domain_subdomain_not_allowed(self):
        """Test that subdomains are not allowed when configured."""
        base_domain = "example.com"
        url = "https://sub.example.com/page"
        self.crawler.allow_subdomains = False
        
        result = self.crawler._is_allowed_domain(url, base_domain)
        
        self.assertFalse(result)

    def test_is_allowed_domain_external_allowed(self):
        """Test that external domains are allowed when configured."""
        base_domain = "example.com"
        url = "https://another-site.com/page"
        self.crawler.allow_external_domains = True
        
        result = self.crawler._is_allowed_domain(url, base_domain)
        
        self.assertTrue(result)

    def test_is_allowed_domain_external_not_allowed(self):
        """Test that external domains are not allowed when configured."""
        base_domain = "example.com"
        url = "https://another-site.com/page"
        self.crawler.allow_external_domains = False
        
        result = self.crawler._is_allowed_domain(url, base_domain)
        
        self.assertFalse(result)

    @patch.object(Cache, 'get')
    @patch.object(Cache, 'set')
    @patch.object(RequestHandler, 'get')
    @patch.object(ResponseParser, 'extract_links')
    @patch.object(ResponseParser, 'extract_page_title')
    @patch.object(ResponseParser, 'extract_metadata')
    def test_crawl_url_uncached(self, mock_extract_metadata, mock_extract_title, 
                                mock_extract_links, mock_request_get, mock_cache_set, 
                                mock_cache_get):
        """Test crawling a URL that's not in the cache."""
        url = "https://example.com"
        depth = 1
        base_domain = "example.com"
        
        # Configure mocks
        mock_cache_get.return_value = None
        mock_request_get.return_value = ("HTML content", 200, {})
        mock_extract_links.return_value = {"https://example.com/page1", "https://example.com/page2"}
        mock_extract_title.return_value = "Example Page"
        mock_extract_metadata.return_value = {"description": "An example page"}
        
        callback_mock = Mock()
        self.crawler.on_page_crawled = callback_mock
        
        # Call the method under test and await the result
        result = async_run(self.crawler._crawl_url(url, depth, base_domain))
        
        # Verify interactions
        mock_cache_get.assert_called_once_with(url)
        mock_request_get.assert_called_once_with(url)
        mock_cache_set.assert_called_once_with(url, "HTML content", 200, {})
        mock_extract_links.assert_called_once()
        mock_extract_title.assert_called_once()
        mock_extract_metadata.assert_called_once()
        
        # Verify results
        self.assertEqual(result, {"https://example.com/page1", "https://example.com/page2"})
        self.assertEqual(self.crawler.stats["pages_crawled"], 1)
        self.assertEqual(self.crawler.stats["pages_skipped"], 0)
        
        # Verify callback
        callback_mock.assert_called_once()
        args, kwargs = callback_mock.call_args
        self.assertEqual(args[0], url)
        self.assertEqual(args[1]["url"], url)
        self.assertEqual(args[1]["depth"], depth)

    @patch.object(Cache, 'get')
    @patch.object(Cache, 'set')
    @patch.object(RequestHandler, 'get')
    @patch.object(ResponseParser, 'extract_links')
    @patch.object(ResponseParser, 'extract_page_title')
    @patch.object(ResponseParser, 'extract_metadata')
    def test_crawl_url_cached(self, mock_extract_metadata, mock_extract_title, 
                              mock_extract_links, mock_request_get, mock_cache_set, 
                              mock_cache_get):
        """Test crawling a URL that's in the cache."""
        url = "https://example.com"
        depth = 1
        base_domain = "example.com"
        
        # Configure mocks
        mock_cache_get.return_value = ("Cached HTML content", 200, {})
        mock_extract_links.return_value = {"https://example.com/page1", "https://example.com/page2"}
        mock_extract_title.return_value = "Example Page"
        mock_extract_metadata.return_value = {"description": "An example page"}
        
        # Call the method under test
        result = async_run(self.crawler._crawl_url(url, depth, base_domain))
        
        # Verify interactions
        mock_cache_get.assert_called_once_with(url)
        mock_request_get.assert_not_called()
        mock_cache_set.assert_not_called()
        mock_extract_links.assert_called_once()
        
        # Verify results
        self.assertEqual(result, {"https://example.com/page1", "https://example.com/page2"})
        self.assertEqual(self.crawler.stats["pages_crawled"], 1)
        self.assertEqual(self.crawler.stats["pages_skipped"], 1)

    @patch.object(Cache, 'get')
    @patch.object(RequestHandler, 'get')
    def test_crawl_url_already_visited(self, mock_request_get, mock_cache_get):
        """Test that already visited URLs are skipped."""
        url = "https://example.com"
        depth = 1
        base_domain = "example.com"
        
        # Mark URL as already visited
        self.crawler.visited_urls.add(url)
        
        # Call the method under test
        result = async_run(self.crawler._crawl_url(url, depth, base_domain))
        
        # Verify interactions
        mock_cache_get.assert_not_called()
        mock_request_get.assert_not_called()
        
        # Verify results
        self.assertEqual(result, set())

    @patch.object(RequestHandler, 'get')
    def test_crawl_url_request_failed(self, mock_request_get):
        """Test handling of failed requests."""
        url = "https://example.com"
        depth = 1
        base_domain = "example.com"
        
        # Configure mock
        mock_request_get.return_value = (None, 404, {})
        
        # Call the method under test
        result = async_run(self.crawler._crawl_url(url, depth, base_domain))
        
        # Verify results
        self.assertEqual(result, set())
        self.assertEqual(self.crawler.stats["pages_crawled"], 0)

    @patch.object(Crawler, '_crawl_url')
    def test_crawl_recursive_max_depth(self, mock_crawl_url):
        """Test that crawling stops at max_depth."""
        url = "https://example.com"
        depth = 3  # > max_depth (2)
        base_domain = "example.com"
        
        # Call the method under test
        async_run(self.crawler._crawl_recursive(url, depth, base_domain))
        
        # Verify that _crawl_url is not called
        mock_crawl_url.assert_not_called()

    def test_crawl_recursive_no_new_links(self):
        """Test recursive crawling when no new links are found."""
        url = "https://example.com"
        depth = 1
        base_domain = "example.com"
        
        # Mock _crawl_url to return empty set
        with patch.object(self.crawler, '_crawl_url') as mock_crawl_url:
            mock_crawl_url.return_value = set()
            
            # Call the method under test
            async_run(self.crawler._crawl_recursive(url, depth, base_domain))
            
            # Verify interactions
            mock_crawl_url.assert_called_once_with(url, depth, base_domain)

    def test_crawl_recursive_with_new_links(self):
        """Test recursive crawling with new links."""
        url = "https://example.com"
        depth = 1
        base_domain = "example.com"
        
        # Create a new crawler instance for this test to avoid interference
        crawler = Crawler(max_depth=2, concurrency_limit=5, use_cache=False, request_delay=0)
        
        try:
            # Mock _crawl_url directly on the instance
            crawler._crawl_url = AsyncMock(return_value={"https://example.com/page1", "https://example.com/page2"})
            
            # Also mock _crawl_recursive to prevent actual recursion
            original_recursive = crawler._crawl_recursive
            recursive_mock = AsyncMock()
            crawler._crawl_recursive = recursive_mock
            
            # Run the test
            async_run(original_recursive(url, depth, base_domain))
            
            # Verify _crawl_url was called
            crawler._crawl_url.assert_called_once_with(url, depth, base_domain)
            
            # Verify recursive calls
            self.assertEqual(recursive_mock.call_count, 2)
            recursive_mock.assert_any_call("https://example.com/page1", depth + 1, base_domain)
            recursive_mock.assert_any_call("https://example.com/page2", depth + 1, base_domain)
        finally:
            crawler.close()

    @patch.object(Crawler, '_crawl_recursive')
    def test_crawl_async(self, mock_crawl_recursive):
        """Test the asynchronous crawling entry point."""
        start_url = "https://example.com"
        
        # Configure mock
        mock_crawl_recursive.return_value = None
        
        # Call the method under test
        result = async_run(self.crawler.crawl_async(start_url))
        
        # Verify _crawl_recursive was called with correct parameters
        mock_crawl_recursive.assert_called_once_with(start_url, 1, "example.com")
        
        # Verify stats in result
        self.assertIn("pages_crawled", result)
        self.assertIn("pages_skipped", result)
        self.assertIn("duration", result)
        self.assertIn("total_urls", result)

    @patch.object(Crawler, 'crawl_async')
    def test_crawl(self, mock_crawl_async):
        """Test the synchronous crawling entry point."""
        start_url = "https://example.com"
        expected_result = {"pages_crawled": 5}
        
        # Configure mock
        mock_crawl_async.return_value = expected_result
        
        # Call the method under test
        result = self.crawler.crawl(start_url)
        
        # Verify result
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main() 