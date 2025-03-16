import os
import json
import time
from typing import Dict, Optional, Any, Tuple
import logging
import sqlite3
from pathlib import Path


class Cache:
    """
    A flexible caching system for storing URL responses.
    
    This class provides both in-memory and persistent (SQLite) caching for
    URL responses to avoid duplicate requests and improve performance.
    """

    def __init__(self, use_persistent: bool = True, cache_dir: str = None, expiry_time: int = 86400):
        """
        Initialize the cache.
        
        Args:
            use_persistent: Whether to use persistent storage (SQLite) or just in-memory cache
            cache_dir: Directory for storing the cache database (if None, uses ./cache)
            expiry_time: Time in seconds after which cached entries expire (default: 24 hours)
        """
        self.logger = logging.getLogger(__name__)
        self.use_persistent = use_persistent
        self.expiry_time = expiry_time
        self.memory_cache: Dict[str, Dict] = {}

        # Setup persistent cache if requested
        self.conn = None
        if use_persistent:
            if cache_dir is None:
                cache_dir = os.path.join(os.getcwd(), 'cache')

            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            self.db_path = os.path.join(cache_dir, 'scraper_cache.db')
            self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database schema."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            # Create table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                url TEXT PRIMARY KEY,
                content TEXT,
                status_code INTEGER,
                headers TEXT,
                timestamp INTEGER
            )
            ''')

            self.conn.commit()
            self.logger.info(f"Initialized persistent cache at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize cache database: {str(e)}")
            self.use_persistent = False  # Fall back to memory-only cache

    def get(self, url: str) -> Optional[Tuple[str, int, Dict]]:
        """
        Retrieve a cached response for a URL.
        
        Args:
            url: The URL to retrieve from cache
            
        Returns:
            Tuple of (content, status_code, headers) if found and not expired, None otherwise
        """
        # First check memory cache
        if url in self.memory_cache:
            entry = self.memory_cache[url]
            if time.time() - entry['timestamp'] < self.expiry_time:
                return entry['content'], entry['status_code'], entry['headers']
            else:
                # Expired, remove from memory cache
                del self.memory_cache[url]

        # Then check persistent cache if enabled
        if self.use_persistent and self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT content, status_code, headers, timestamp FROM cache WHERE url = ?",
                    (url,)
                )
                result = cursor.fetchone()

                if result:
                    content, status_code, headers_json, timestamp = result

                    # Check if expired
                    if time.time() - timestamp < self.expiry_time:
                        headers = json.loads(headers_json)

                        # Add to memory cache for faster future access
                        self.memory_cache[url] = {
                            'content': content,
                            'status_code': status_code,
                            'headers': headers,
                            'timestamp': timestamp
                        }

                        return content, status_code, headers
                    else:
                        # Expired, remove from persistent cache
                        cursor.execute("DELETE FROM cache WHERE url = ?", (url,))
                        self.conn.commit()
            except Exception as e:
                self.logger.error(f"Error retrieving from cache: {str(e)}")

        return None

    def set(self, url: str, content: str, status_code: int, headers: Dict[str, str]) -> None:
        """
        Store a response in the cache.
        
        Args:
            url: The URL that was requested
            content: The response content (typically HTML)
            status_code: The HTTP status code
            headers: The response headers
        """
        timestamp = int(time.time())

        # Update memory cache
        self.memory_cache[url] = {
            'content': content,
            'status_code': status_code,
            'headers': headers,
            'timestamp': timestamp
        }

        # Update persistent cache if enabled
        if self.use_persistent and self.conn:
            try:
                cursor = self.conn.cursor()
                headers_json = json.dumps(headers)

                cursor.execute(
                    "INSERT OR REPLACE INTO cache (url, content, status_code, headers, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (url, content, status_code, headers_json, timestamp)
                )

                self.conn.commit()
            except Exception as e:
                self.logger.error(f"Error storing in cache: {str(e)}")

    def has(self, url: str) -> bool:
        """
        Check if a URL is in the cache and not expired.
        
        Args:
            url: The URL to check
            
        Returns:
            True if the URL is cached and not expired, False otherwise
        """
        # First check memory cache
        if url in self.memory_cache:
            entry = self.memory_cache[url]
            if time.time() - entry['timestamp'] < self.expiry_time:
                return True
            else:
                # Expired, remove from memory cache
                del self.memory_cache[url]

        # Then check persistent cache if enabled
        if self.use_persistent and self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT timestamp FROM cache WHERE url = ?",
                    (url,)
                )
                result = cursor.fetchone()

                if result and (time.time() - result[0] < self.expiry_time):
                    return True
                elif result:
                    # Expired, remove from persistent cache
                    cursor.execute("DELETE FROM cache WHERE url = ?", (url,))
                    self.conn.commit()
            except Exception as e:
                self.logger.error(f"Error checking cache: {str(e)}")

        return False

    def clear(self) -> None:
        """Clear all cached data."""
        # Clear memory cache
        self.memory_cache.clear()

        # Clear persistent cache if enabled
        if self.use_persistent and self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM cache")
                self.conn.commit()
                self.logger.info("Cache cleared")
            except Exception as e:
                self.logger.error(f"Error clearing cache: {str(e)}")

    def clear_expired(self) -> int:
        """
        Clear expired entries from the cache.

        Returns:
            Number of entries cleared
        """
        cleared_count = 0
        current_time = time.time()

        # Clear expired entries from memory cache
        expired_urls = [url for url, entry in self.memory_cache.items()
                        if current_time - entry['timestamp'] >= self.expiry_time]
        for url in expired_urls:
            del self.memory_cache[url]
            cleared_count += 1

        # Clear expired entries from persistent cache if enabled
        if self.use_persistent and self.conn:
            try:
                cursor = self.conn.cursor()
                expire_time = int(current_time - self.expiry_time)

                # First, get the count of entries to be deleted
                cursor.execute(
                    "SELECT COUNT(*) FROM cache WHERE timestamp < ?",
                    (expire_time,)
                )
                db_cleared_count = cursor.fetchone()[0]

                # Then perform the delete
                cursor.execute(
                    "DELETE FROM cache WHERE timestamp < ?",
                    (expire_time,)
                )

                cleared_count = cleared_count + db_cleared_count
                self.conn.commit()
                self.logger.info(f"Cleared {cleared_count} expired cache entries")
            except Exception as e:
                self.logger.error(f"Error clearing expired cache entries: {str(e)}")

        return cleared_count

    def close(self) -> None:
        """Close the cache and release resources."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure resources are cleaned up when used as context manager."""
        self.close()