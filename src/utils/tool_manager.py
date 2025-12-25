import hashlib
import time
from collections import OrderedDict
from typing import Any

from src.tools.search_tools import search
from src.utils.logger import get_logger, get_metrics

logger = get_logger(__name__)

class ToolManager:
    """
    Manages tool usage, including web searches and URL fetching, with integrated caching.

    Attributes:
        url_cache (OrderedDict): A cache for storing the content of fetched URLs (LRU).
        search_cache (OrderedDict): A cache for storing the results of web searches (LRU).
        ttl (int): The time-to-live for cache entries in seconds.
        max_cache_size (int): Maximum number of entries per cache (default: 1000).
    """

    MAX_CACHE_SIZE = 1000  # Maximum cache entries

    def __init__(self, ttl: int = 3600):
        """
        Initializes the ToolManager with a specified time-to-live for cache entries.

        Args:
            ttl (int): The time-to-live for cache entries in seconds. Defaults to 3600 (1 hour).
        """
        self.url_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.search_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.ttl = ttl

    def _add_to_cache(self, cache: OrderedDict, key: str, value: Any) -> None:
        """
        Add an item to cache with size limit enforcement (LRU eviction).

        Args:
            cache: The cache OrderedDict to add to
            key: The cache key
            value: The value to cache
        """
        # Check if cache is full
        if len(cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (FIFO/LRU)
            evicted_key = next(iter(cache))
            cache.pop(evicted_key)
            logger.debug(f"Cache full, evicted oldest entry: {evicted_key[:50]}...")

        # Add new entry
        cache[key] = value

    def get_url(self, url: str, agent: str) -> str:
        """
        Fetches the content of a URL, using a cache to avoid redundant requests.

        This method is a placeholder and should be implemented with actual web fetching logic.

        Args:
            url (str): The URL to fetch.
            agent (str): The name of the agent requesting the URL.

        Returns:
            str: The content of the URL.
        """
        timestamp = time.time()
        if url in self.url_cache and (timestamp - self.url_cache[url]['timestamp']) < self.ttl:
            logger.debug(f"Cache hit for URL: {url}", extra={"agent": agent})

            # Track cache hit in metrics
            metrics = get_metrics()
            if metrics:
                metrics.add_cache_hit()

            return self.url_cache[url]['content']

        logger.info(f"Cache miss for URL: {url}, fetching content", extra={"agent": agent})

        # Track cache miss in metrics
        metrics = get_metrics()
        if metrics:
            metrics.add_cache_miss()

        # Placeholder for actual URL fetching logic
        content = f"Content of {url} fetched by {agent}"
        self._add_to_cache(self.url_cache, url, {'content': content, 'timestamp': timestamp})
        return content

    def search_web(self, query: str, tool: str) -> list[dict]:
        """
        Performs a web search, using a cache to avoid redundant searches.

        Args:
            query (str): The search query.
            tool (str): The search tool to use (e.g., 'brave', 'duckduckgo', 'google_pse_factcheck').

        Returns:
            List[Dict]: A list of search results.
        """
        timestamp = time.time()
        query_hash = hashlib.sha256(f"{query}_{tool}".encode()).hexdigest()

        if query_hash in self.search_cache and (timestamp - self.search_cache[query_hash]['timestamp']) < self.ttl:
            logger.debug(
                "Cache hit for search",
                extra={"query": query[:50], "tool": tool}
            )

            # Track cache hit in metrics
            metrics = get_metrics()
            if metrics:
                metrics.add_cache_hit()

            return self.search_cache[query_hash]['results']

        logger.info(
            "Cache miss for search, executing query",
            extra={"query": query[:50], "tool": tool}
        )

        # Track cache miss in metrics
        metrics = get_metrics()
        if metrics:
            metrics.add_cache_miss()

        # Use the actual search implementation
        try:
            results = search(query, tool=tool, count=10)

            # Track API call in metrics
            if metrics:
                metrics.add_api_call(tool)

            logger.info(
                "Search completed successfully",
                extra={"tool": tool, "results_count": len(results)}
            )
        except NotImplementedError:
            # Fallback to brave if the tool is not implemented
            logger.warning(f"Tool '{tool}' not implemented, falling back to 'brave'")
            results = search(query, tool="brave", count=10)

            # Track API call in metrics
            if metrics:
                metrics.add_api_call("brave")
        except Exception as e:
            logger.error(f"Search failed with tool '{tool}': {e}", exc_info=True)

            # Track error in metrics
            if metrics:
                metrics.add_error(f"search_{tool}", str(e))

            results = []

        self._add_to_cache(self.search_cache, query_hash, {'results': results, 'timestamp': timestamp})
        return results

    def clear_cache(self):
        """
        Clears the URL and search caches.
        """
        url_count = len(self.url_cache)
        search_count = len(self.search_cache)

        self.url_cache.clear()
        self.search_cache.clear()

        logger.info(
            "Caches cleared",
            extra={"url_entries": url_count, "search_entries": search_count}
        )
