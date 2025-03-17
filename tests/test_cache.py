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
            # Create an isolated cache with a 10 second expiry time
            isolated_cache = Cache(use_persistent=True, cache_dir=separate_temp_dir, expiry_time=10)

            # Ensure we start with a clean slate
            isolated_cache.clear()

            # Get current time
            current_time = time.time()

            # Add an expired entry (20 seconds old)
            isolated_cache.set("https://will-expire.com", "old content", 200, {})
            # Manually update the timestamp to make it expired
            isolated_cache.memory_cache["https://will-expire.com"]["timestamp"] = current_time - 20
            if isolated_cache.use_persistent and isolated_cache.conn:
                cursor = isolated_cache.conn.cursor()
                cursor.execute(
                    "UPDATE cache SET timestamp = ? WHERE url = ?",
                    (int(current_time - 20), "https://will-expire.com")
                )
                isolated_cache.conn.commit()

            # Add a fresh entry
            isolated_cache.set("https://wont-expire.com", "new content", 200, {})

            # Verify entries exist in memory cache
            self.assertIn("https://will-expire.com", isolated_cache.memory_cache)
            self.assertIn("https://wont-expire.com", isolated_cache.memory_cache)

            # Verify entries exist in persistent cache
            if isolated_cache.use_persistent and isolated_cache.conn:
                cursor = isolated_cache.conn.cursor()
                cursor.execute("SELECT url FROM cache WHERE url = ?", ("https://will-expire.com",))
                self.assertIsNotNone(cursor.fetchone())
                cursor.execute("SELECT url FROM cache WHERE url = ?", ("https://wont-expire.com",))
                self.assertIsNotNone(cursor.fetchone())

            # Clear expired entries and check count
            cleared = isolated_cache.clear_expired()

            # Should only clear the expired entry
            self.assertEqual(cleared, 1, f"Expected to clear 1 expired entry, but cleared {cleared}")

            # Verify the expired entry is gone and the fresh one remains
            self.assertNotIn("https://will-expire.com", isolated_cache.memory_cache)
            self.assertIn("https://wont-expire.com", isolated_cache.memory_cache)

            # Verify persistent cache state
            if isolated_cache.use_persistent and isolated_cache.conn:
                cursor = isolated_cache.conn.cursor()
                cursor.execute("SELECT url FROM cache WHERE url = ?", ("https://will-expire.com",))
                self.assertIsNone(cursor.fetchone())
                cursor.execute("SELECT url FROM cache WHERE url = ?", ("https://wont-expire.com",))
                self.assertIsNotNone(cursor.fetchone())
        finally:
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
