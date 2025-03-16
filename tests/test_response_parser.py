import unittest

from scraper.response_parser import ResponseParser


class TestResponseParser(unittest.TestCase):
    """Test cases for the ResponseParser class."""

    def setUp(self):
        """Set up the test environment before each test."""
        self.parser = ResponseParser(base_url="https://example.com")

    def test_extract_links_empty_content(self):
        """Test that empty content returns empty set of links."""
        links = self.parser.extract_links("")
        self.assertEqual(links, set())

    def test_extract_links_with_anchors(self):
        """Test extraction of links from anchor tags."""
        html = """
        <html>
        <body>
            <a href="https://example.org">External Link</a>
            <a href="/page1.html">Relative Link</a>
            <a href="#section">Fragment Link</a>
            <a href="javascript:void(0)">JavaScript Link</a>
            <a href="mailto:user@example.com">Email Link</a>
        </body>
        </html>
        """
        links = self.parser.extract_links(html)
        expected = {
            "https://example.org",
            "https://example.com/page1.html"
        }
        self.assertEqual(links, expected)

    def test_extract_links_with_other_elements(self):
        """Test extraction of links from other HTML elements."""
        html = """
        <html>
        <head>
            <link href="/style.css" rel="stylesheet">
            <script src="/script.js"></script>
        </head>
        <body>
            <img src="/image.jpg" alt="Image">
            <img src="https://cdn.example.org/image.png" alt="External Image">
        </body>
        </html>
        """
        links = self.parser.extract_links(html)
        expected = {
            "https://example.com/style.css",
            "https://example.com/script.js",
            "https://example.com/image.jpg",
            "https://cdn.example.org/image.png"
        }
        self.assertEqual(links, expected)

    def test_normalize_url(self):
        """Test URL normalization."""
        test_cases = [
            # (input_url, expected_output)
            ("https://example.org", "https://example.org"),
            ("/page1.html", "https://example.com/page1.html"),
            ("page2.html", "https://example.com/page2.html"),
            ("#section", None),
            ("javascript:alert('test')", None),
            ("mailto:user@example.com", None),
            ("ftp://example.com/file.txt", None),
            ("https://example.com/page.html#fragment", "https://example.com/page.html"),
        ]

        for input_url, expected in test_cases:
            with self.subTest(url=input_url):
                self.assertEqual(self.parser._normalize_url(input_url), expected)

    def test_extract_page_title(self):
        """Test extraction of page title."""
        html = """
        <html>
        <head>
            <title>Test Page Title</title>
        </head>
        <body>
            <h1>Heading</h1>
        </body>
        </html>
        """
        title = self.parser.extract_page_title(html)
        self.assertEqual(title, "Test Page Title")

        # Test with missing title
        html_no_title = "<html><body>No title here</body></html>"
        title = self.parser.extract_page_title(html_no_title)
        self.assertIsNone(title)

    def test_extract_metadata(self):
        """Test extraction of metadata from meta tags."""
        html = """
        <html>
        <head>
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, keywords, scraper">
            <meta property="og:title" content="OpenGraph Title">
            <meta property="og:image" content="https://example.com/image.jpg">
        </head>
        <body>
            <p>Some content</p>
        </body>
        </html>
        """
        metadata = self.parser.extract_metadata(html)
        expected = {
            "description": "Test description",
            "keywords": "test, keywords, scraper",
            "og:title": "OpenGraph Title",
            "og:image": "https://example.com/image.jpg"
        }
        self.assertEqual(metadata, expected)


if __name__ == '__main__':
    unittest.main()
