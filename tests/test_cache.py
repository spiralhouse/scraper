import unittest
import tempfile
import shutil
import time
from unittest.mock import patch, MagicMock

from scraper.cache_manager import Cache


class TestCache(unittest.TestCase):
    """Test cases for the Cache class."""

    def setUp(self):
        """Set up the test environment before each test."""
        # Create a temporary directory for cache files
        self.temp_dir = tempfile.mkdtemp()

        # Create cache instances for testing with different configurations
        self.memory_cache = Cache(use_persistent=False)
        self.persistent_cache = Cache(use_persistent=True, cache_dir=self.temp_dir, expiry_time=1)  # 1 second expiry

    def tearDown(self):
        """Clean up after each test."""
        # Close connections
        self.memory_cache.close()
        self.persistent_cache.close()

        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def test_memory_cache_operations(self):
        """Test basic memory cache operations."""
        cache = self.memory_cache

        # Test empty cache
        self.assertFalse(cache.has("https://example.com"))
        self.assertIsNone(cache.get("https://example.com"))

        # Test setting and getting values
        cache.set("https://example.com", "content", 200, {"Content-Type": "text/html"})
        self.assertTrue(cache.has("https://example.com"))

        result = cache.get("https://example.com")
        self.assertIsNotNone(result)
        content, status, headers = result
        self.assertEqual(content, "content")
        self.assertEqual(status, 200)
        self.assertEqual(headers, {"Content-Type": "text/html"})

    def test_persistent_cache_operations(self):
        """Test persistent cache operations."""
        cache = self.persistent_cache

        # Test setting and getting values
        cache.set("https://example.org", "persistent content", 201, {"Server": "nginx"})
        self.assertTrue(cache.has("https://example.org"))

        # Create a new cache instance pointing to the same file to verify persistence
        new_cache = Cache(use_persistent=True, cache_dir=self.temp_dir, expiry_time=1)
        self.assertTrue(new_cache.has("https://example.org"))

        result = new_cache.get("https://example.org")
        self.assertIsNotNone(result)
        content, status, headers = result
        self.assertEqual(content, "persistent content")
        self.assertEqual(status, 201)
        self.assertEqual(headers, {"Server": "nginx"})

        new_cache.close()

    def test_cache_expiry(self):
        """Test that cache entries expire after the specified time."""
        cache = self.persistent_cache  # Using cache with 1-second expiry

        # Add an entry
        cache.set("https://expiry-test.com", "expiring content", 200, {})
        self.assertTrue(cache.has("https://expiry-test.com"))

        # Wait for expiry
        time.sleep(1.5)  # Wait longer than the 1 second expiry time

        # Verify it's expired
        self.assertFalse(cache.has("https://expiry-test.com"))
        self.assertIsNone(cache.get("https://expiry-test.com"))

    def test_clear_cache(self):
        """Test clearing the entire cache."""
        cache = self.memory_cache

        # Add multiple entries
        cache.set("https://site1.com", "content1", 200, {})
        cache.set("https://site2.com", "content2", 200, {})
        cache.set("https://site3.com", "content3", 200, {})

        # Clear everything
        cache.clear()

        # Verify all gone
        self.assertFalse(cache.has("https://site1.com"))
        self.assertFalse(cache.has("https://site2.com"))
        self.assertFalse(cache.has("https://site3.com"))

    def test_clear_expired(self):
        """Test clearing only expired entries."""
        # Create a separate directory for this test to ensure complete isolation
        separate_temp_dir = tempfile.mkdtemp(prefix="isolated_cache_test_")

        try:
            # Create an isolated cache with its own directory
            isolated_cache = Cache(use_persistent=True, cache_dir=separate_temp_dir, expiry_time=1)

            # Ensure we start with a clean slate
            isolated_cache.clear()

            # Verify we're starting with a clean state by trying to get a known URL
            self.assertIsNone(isolated_cache.get("https://will-expire.com"))
            self.assertIsNone(isolated_cache.get("https://wont-expire.com"))

            # Add a single entry that will expire
            isolated_cache.set("https://will-expire.com", "old content", 200, {})

            # Verify it was added
            self.assertTrue(isolated_cache.has("https://will-expire.com"))

            # Wait for it to expire
            time.sleep(1.5)

            # Add a fresh entry
            isolated_cache.set("https://wont-expire.com", "new content", 200, {})

            # Clear expired entries and check count
            cleared = isolated_cache.clear_expired()

            # Should only clear the expired entry
            self.assertEqual(cleared, 1, f"Expected to clear 1 expired entry, but cleared {cleared}")
            self.assertFalse(isolated_cache.has("https://will-expire.com"))
            self.assertTrue(isolated_cache.has("https://wont-expire.com"))

        finally:
            # Ensure we clean up properly
            if 'isolated_cache' in locals():
                isolated_cache.close()
            # Clean up the temporary directory
            shutil.rmtree(separate_temp_dir)

    def test_context_manager(self):
        """Test using the cache as a context manager."""
        with Cache(use_persistent=False) as cache:
            cache.set("https://example.com", "content", 200, {})
            self.assertTrue(cache.has("https://example.com"))

    @patch('sqlite3.connect')
    def test_db_error_fallback(self, mock_connect):
        """Test fallback to memory cache when database connection fails."""
        # Make the connection raise an exception
        mock_connect.side_effect = Exception("DB connection error")

        # This should try to create a persistent cache but fail and fall back
        cache = Cache(use_persistent=True, cache_dir=self.temp_dir)

        # Verify it's using memory-only mode
        self.assertFalse(cache.use_persistent)

        # Verify memory cache still works
        cache.set("https://example.com", "fallback content", 200, {})
        self.assertTrue(cache.has("https://example.com"))

    def test_overwrite_entry(self):
        """Test overwriting an existing cache entry."""
        cache = self.memory_cache

        # Add initial entry
        cache.set("https://update-test.com", "original", 200, {"Version": "1"})

        # Update with new values
        cache.set("https://update-test.com", "updated", 201, {"Version": "2"})

        # Verify it was updated
        result = cache.get("https://update-test.com")
        self.assertIsNotNone(result)
        content, status, headers = result
        self.assertEqual(content, "updated")
        self.assertEqual(status, 201)
        self.assertEqual(headers, {"Version": "2"})


if __name__ == '__main__':
    unittest.main()
