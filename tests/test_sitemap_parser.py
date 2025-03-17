import unittest
from unittest.mock import patch, MagicMock
import asyncio

from scraper.sitemap_parser import SitemapParser


class TestSitemapParser(unittest.TestCase):
    """Test cases for the SitemapParser class."""
    
    def setUp(self):
        """Set up test environment."""
        self.user_agent = "TestBot"
        self.parser = SitemapParser(self.user_agent, max_subsitemaps=2, overall_timeout=5)
    
    def test_get_sitemap_url(self):
        """Test generating sitemap URL from a domain URL."""
        test_cases = [
            ("https://example.com", "https://example.com/sitemap.xml"),
            ("https://example.com/page", "https://example.com/sitemap.xml"),
            ("http://sub.example.com", "http://sub.example.com/sitemap.xml"),
        ]
        
        for input_url, expected_url in test_cases:
            with self.subTest(url=input_url):
                result = self.parser.get_sitemap_url(input_url)
                self.assertEqual(result, expected_url)
    
    @patch('requests.get')
    def test_fetch_sitemap_success(self, mock_get):
        """Test successful fetching of sitemap."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<xml>sitemap content</xml>"
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.parser.fetch_sitemap("https://example.com/sitemap.xml")
        
        # Verify results
        self.assertEqual(result, "<xml>sitemap content</xml>")
        mock_get.assert_called_once_with(
            "https://example.com/sitemap.xml", 
            headers={'User-Agent': self.user_agent}, 
            timeout=10
        )
    
    @patch('requests.get')
    def test_fetch_sitemap_failure(self, mock_get):
        """Test handling of sitemap fetch failures."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.parser.fetch_sitemap("https://example.com/sitemap.xml")
        
        # Verify results
        self.assertIsNone(result)
    
    @patch('requests.get')
    def test_fetch_sitemap_exception(self, mock_get):
        """Test handling of exceptions during sitemap fetch."""
        # Make the request raise an exception
        mock_get.side_effect = Exception("Network error")
        
        # Call the method
        result = self.parser.fetch_sitemap("https://example.com/sitemap.xml")
        
        # Verify results
        self.assertIsNone(result)
    
    def test_is_sitemap_index(self):
        """Test detecting sitemap index vs regular sitemap."""
        # Sitemap index
        sitemap_index = """
        <?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap>
                <loc>https://example.com/sitemap1.xml</loc>
                <lastmod>2023-01-01</lastmod>
            </sitemap>
            <sitemap>
                <loc>https://example.com/sitemap2.xml</loc>
            </sitemap>
            <sitemap>
                <loc>/sitemap3.xml</loc>
            </sitemap>
        </sitemapindex>
        """
        
        # Regular sitemap
        regular_sitemap = """
        <?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
            </url>
        </urlset>
        """
        
        # Non-XML content
        non_xml = "This is not XML"
        
        # Test cases
        self.assertTrue(self.parser.is_sitemap_index(sitemap_index))
        self.assertFalse(self.parser.is_sitemap_index(regular_sitemap))
        self.assertFalse(self.parser.is_sitemap_index(non_xml))
    
    def test_parse_sitemap_index(self):
        """Test parsing a sitemap index."""
        sitemap_index = """
        <?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap>
                <loc>https://example.com/sitemap1.xml</loc>
                <lastmod>2023-01-01</lastmod>
            </sitemap>
            <sitemap>
                <loc>/sitemap2.xml</loc>
            </sitemap>
            <sitemap>
                <loc>/sitemap3.xml</loc>
            </sitemap>
        </sitemapindex>
        """
        
        base_url = "https://example.com"
        # Only 2 sub-sitemaps should be returned due to max_subsitemaps=2
        expected_urls = [
            "https://example.com/sitemap1.xml",
            "https://example.com/sitemap2.xml"
        ]
        
        result = self.parser.parse_sitemap_index(sitemap_index, base_url)
        self.assertEqual(sorted(result), sorted(expected_urls))
    
    def test_parse_sitemap(self):
        """Test parsing a regular sitemap."""
        sitemap = """
        <?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
                <lastmod>2023-01-01</lastmod>
                <changefreq>daily</changefreq>
                <priority>0.8</priority>
            </url>
            <url>
                <loc>/page2</loc>
                <priority>0.5</priority>
            </url>
        </urlset>
        """
        
        base_url = "https://example.com"
        expected_data = [
            {
                'url': 'https://example.com/page1',
                'lastmod': '2023-01-01',
                'changefreq': 'daily',
                'priority': 0.8
            },
            {
                'url': 'https://example.com/page2',
                'lastmod': None,
                'changefreq': None,
                'priority': 0.5
            }
        ]
        
        result = self.parser.parse_sitemap(sitemap, base_url)
        
        # Compare each URL data
        for expected, actual in zip(sorted(expected_data, key=lambda x: x['url']), 
                                    sorted(result, key=lambda x: x['url'])):
            self.assertEqual(expected['url'], actual['url'])
            self.assertEqual(expected['lastmod'], actual['lastmod'])
            self.assertEqual(expected['changefreq'], actual['changefreq'])
            self.assertEqual(expected['priority'], actual['priority'])
    
    @patch.object(SitemapParser, 'extract_urls_from_sitemap')
    def test_get_urls_from_domain(self, mock_extract):
        """Test getting URLs from a domain sitemap."""
        # Setup mock
        expected_urls = {'https://example.com/page1', 'https://example.com/page2'}
        mock_extract.return_value = expected_urls
        
        # Call the method
        result = self.parser.get_urls_from_domain("https://example.com")
        
        # Verify results
        self.assertEqual(result, expected_urls)
        mock_extract.assert_called_once_with("https://example.com/sitemap.xml")


if __name__ == "__main__":
    unittest.main() 