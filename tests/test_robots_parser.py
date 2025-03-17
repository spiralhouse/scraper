import unittest
from unittest.mock import patch, MagicMock

from scraper.robots_parser import RobotsParser


class TestRobotsParser(unittest.TestCase):
    """Test cases for the RobotsParser class."""
    
    def setUp(self):
        """Set up test environment."""
        self.user_agent = "TestBot"
        self.parser = RobotsParser(self.user_agent)
    
    @patch('requests.get')
    def test_fetch_robots_txt_success(self, mock_get):
        """Test successful fetching of robots.txt."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        User-agent: *
        Disallow: /private/
        Allow: /
        
        User-agent: TestBot
        Disallow: /test-private/
        Allow: /
        
        Crawl-delay: 5
        """
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.parser.fetch_robots_txt("https://example.com")
        
        # Verify results
        self.assertTrue(result)
        mock_get.assert_called_once_with("https://example.com/robots.txt", timeout=10)
        
        # Verify the parser was created and domain added to cache
        self.assertIn("example.com", self.parser.parsers)
        self.assertIn("example.com", self.parser.fetched_domains)
    
    @patch('requests.get')
    def test_fetch_robots_txt_404(self, mock_get):
        """Test fetching when robots.txt doesn't exist."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.parser.fetch_robots_txt("https://example.com")
        
        # Verify results
        self.assertTrue(result)  # Should still return True for successful operation
        self.assertIn("example.com", self.parser.parsers)
        
        # The empty parser should allow everything
        self.assertTrue(self.parser.is_allowed("https://example.com/anything"))
    
    @patch('requests.get')
    def test_fetch_robots_txt_error(self, mock_get):
        """Test error handling when fetching robots.txt."""
        # Make the request raise an exception
        mock_get.side_effect = Exception("Network error")
        
        # Call the method
        result = self.parser.fetch_robots_txt("https://example.com")
        
        # Verify results
        self.assertFalse(result)
        self.assertNotIn("example.com", self.parser.parsers)
        self.assertIn("example.com", self.parser.fetched_domains)
    
    @patch.object(RobotsParser, 'fetch_robots_txt')
    def test_is_allowed(self, mock_fetch):
        """Test checking if a URL is allowed."""
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser.is_allowed.return_value = False
        self.parser.parsers["example.com"] = mock_parser
        
        # Call the method
        result = self.parser.is_allowed("https://example.com/private")
        
        # Verify results
        self.assertFalse(result)
        mock_fetch.assert_not_called()  # Should not fetch since already in parsers
        mock_parser.is_allowed.assert_called_once_with(self.user_agent, "https://example.com/private")
    
    @patch.object(RobotsParser, 'fetch_robots_txt')
    def test_is_allowed_fetch_failure(self, mock_fetch):
        """Test that URLs are allowed when robots.txt fetch fails."""
        # Setup mock to return False (fetch failure)
        mock_fetch.return_value = False
        
        # Call the method
        result = self.parser.is_allowed("https://example.com/something")
        
        # Verify results
        self.assertTrue(result)  # Should allow when fetch fails
        mock_fetch.assert_called_once_with("https://example.com/something")
    
    @patch.object(RobotsParser, 'fetch_robots_txt')
    def test_get_crawl_delay(self, mock_fetch):
        """Test getting crawl delay from robots.txt."""
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser.get_crawl_delay.return_value = 3.5
        self.parser.parsers["example.com"] = mock_parser
        
        # Call the method
        delay = self.parser.get_crawl_delay("https://example.com/page")
        
        # Verify results
        self.assertEqual(delay, 3.5)
        mock_fetch.assert_not_called()
        mock_parser.get_crawl_delay.assert_called_once_with(self.user_agent)
    
    @patch.object(RobotsParser, 'fetch_robots_txt')
    def test_get_crawl_delay_not_specified(self, mock_fetch):
        """Test getting crawl delay when not specified in robots.txt."""
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser.get_crawl_delay.return_value = None
        self.parser.parsers["example.com"] = mock_parser
        
        # Call the method
        delay = self.parser.get_crawl_delay("https://example.com/page")
        
        # Verify results
        self.assertEqual(delay, self.parser.default_crawl_delay)
        mock_fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main() 