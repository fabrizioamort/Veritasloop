import time
import unittest
import hashlib
from unittest.mock import patch, MagicMock
from src.utils.tool_manager import ToolManager

class TestToolManager(unittest.TestCase):
    """
    Unit tests for the ToolManager class.
    """

    def setUp(self):
        """
        Set up a new ToolManager instance for each test.
        """
        self.tool_manager = ToolManager(ttl=2)

    def test_get_url_cache_miss(self):
        """
        Test that get_url fetches new content on a cache miss.
        """
        url = "http://example.com"
        agent = "test_agent"
        content = self.tool_manager.get_url(url, agent)
        self.assertEqual(content, f"Content of {url} fetched by {agent}")
        self.assertIn(url, self.tool_manager.url_cache)

    def test_get_url_cache_hit(self):
        """
        Test that get_url returns cached content on a cache hit.
        """
        url = "http://example.com"
        agent = "test_agent"
        # First call to cache the content
        self.tool_manager.get_url(url, agent)
        # Second call should be a cache hit
        with patch('src.utils.tool_manager.logger') as mock_logger:
            content = self.tool_manager.get_url(url, agent)
            self.assertEqual(content, f"Content of {url} fetched by {agent}")
            # Verify debug log was called for cache hit
            mock_logger.debug.assert_called()

    @patch('src.utils.tool_manager.search')
    def test_search_web_cache_miss(self, mock_search):
        """
        Test that search_web performs a new search on a cache miss.
        """
        query = "test query"
        tool = "brave"
        mock_search.return_value = [{"title": f"Result for '{query}'", "url": "http://example.com"}]

        results = self.tool_manager.search_web(query, tool)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], f"Result for '{query}'")
        query_hash = hashlib.sha256(f"{query}_{tool}".encode()).hexdigest()
        self.assertIn(query_hash, self.tool_manager.search_cache)
        mock_search.assert_called_once_with(query, tool=tool, count=10)

    @patch('src.utils.tool_manager.search')
    def test_search_web_cache_hit(self, mock_search):
        """
        Test that search_web returns cached results on a cache hit.
        """
        query = "test query"
        tool = "brave"
        mock_search.return_value = [{"title": f"Result for '{query}'", "url": "http://example.com"}]

        # First call to cache the results
        self.tool_manager.search_web(query, tool)
        # Second call should be a cache hit
        with patch('src.utils.tool_manager.logger') as mock_logger:
            results = self.tool_manager.search_web(query, tool)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['title'], f"Result for '{query}'")
            # Verify debug log was called for cache hit
            mock_logger.debug.assert_called()

    def test_cache_expiration(self):
        """
        Test that the cache expires after the TTL.
        """
        url = "http://example.com"
        agent = "test_agent"
        # Cache the content
        self.tool_manager.get_url(url, agent)
        # Wait for the cache to expire
        time.sleep(3)
        # This call should be a cache miss
        with patch('src.utils.tool_manager.logger') as mock_logger:
            self.tool_manager.get_url(url, agent)
            # Verify info log was called for cache miss
            mock_logger.info.assert_called()

    @patch('src.utils.tool_manager.search')
    def test_clear_cache(self, mock_search):
        """
        Test that clear_cache clears both caches.
        """
        url = "http://example.com"
        agent = "test_agent"
        query = "test query"
        tool = "brave"
        mock_search.return_value = [{"title": "Test", "url": "http://test.com"}]

        self.tool_manager.get_url(url, agent)
        self.tool_manager.search_web(query, tool)
        self.assertIn(url, self.tool_manager.url_cache)
        self.assertNotEqual(len(self.tool_manager.search_cache), 0)

        self.tool_manager.clear_cache()

        self.assertEqual(len(self.tool_manager.url_cache), 0)
        self.assertEqual(len(self.tool_manager.search_cache), 0)

if __name__ == '__main__':
    unittest.main()
