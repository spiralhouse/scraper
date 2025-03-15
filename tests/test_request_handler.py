import unittest
from unittest.mock import patch, Mock, MagicMock
import requests
import sys
import os

# Add the parent directory to sys.path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from request_handler import RequestHandler


class TestRequestHandler(unittest.TestCase):
    """Test cases for the RequestHandler class."""

    def setUp(self):
        """Set up the test environment before each test."""
        self.handler = RequestHandler(
            timeout=10,
            max_retries=2,
            backoff_factor=0.1,
            user_agent="TestBot/1.0"
        )

    def tearDown(self):
        """Clean up after each test."""
        self.handler.close()

    def test_initialization(self):
        """Test that the RequestHandler initializes with correct values."""
        self.assertEqual(self.handler.timeout, 10)
        self.assertEqual(self.handler.headers['User-Agent'], "TestBot/1.0")
        self.assertIsInstance(self.handler.session, requests.Session)

    @patch('requests.Session.get')
    def test_get_success(self, mock_get):
        """Test successful GET request."""
        # Create mock response
        mock_response = Mock()
        mock_response.text = "<html>Test Content</html>"
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response

        # Make the request
        content, status, headers = self.handler.get("https://example.com")

        # Assert request was made with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]
        self.assertEqual(call_args['timeout'], 10)
        self.assertEqual(call_args['headers']['User-Agent'], "TestBot/1.0")

        # Assert response was processed correctly
        self.assertEqual(content, "<html>Test Content</html>")
        self.assertEqual(status, 200)
        self.assertEqual(headers, {'Content-Type': 'text/html'})

    @patch('requests.Session.get')
    def test_get_with_custom_headers(self, mock_get):
        """Test GET request with custom headers."""
        # Create mock response
        mock_response = Mock()
        mock_response.text = "<html>Test Content</html>"
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

        # Make the request with custom headers
        custom_headers = {'Referer': 'https://example.org'}
        self.handler.get("https://example.com", custom_headers=custom_headers)

        # Assert custom header was included in the request
        call_args = mock_get.call_args[1]
        self.assertEqual(call_args['headers']['Referer'], 'https://example.org')
        self.assertEqual(call_args['headers']['User-Agent'], "TestBot/1.0")

    @patch('requests.Session.get')
    def test_get_exception_handling(self, mock_get):
        """Test handling of exceptions during GET requests."""
        # Configure mock to raise an exception
        mock_get.side_effect = requests.RequestException("Connection failed")

        # Make the request
        content, status, headers = self.handler.get("https://example.com")

        # Assert the error was handled properly
        self.assertIsNone(content)
        self.assertEqual(status, 0)
        self.assertEqual(headers, {})

    @patch('requests.Session')
    def test_session_creation_with_retry(self, mock_session_class):
        """Test that session is created with proper retry configuration."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        handler = RequestHandler(max_retries=5, backoff_factor=0.5)

        # Verify session.mount was called twice (for http:// and https://)
        self.assertEqual(mock_session.mount.call_count, 2)

    def test_context_manager(self):
        """Test the context manager protocol."""
        with patch.object(RequestHandler, 'close') as mock_close:
            with RequestHandler() as handler:
                self.assertIsInstance(handler, RequestHandler)

            # Verify close was called after exiting context
            mock_close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
