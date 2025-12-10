"""
Unit tests for the search tools module.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.tools.search_tools import search


class TestSearchTools(unittest.TestCase):
    @patch("src.tools.search_tools.requests.get")
    def test_brave_search_success(self, mock_get):
        """Test brave_search with a successful API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Brave Search",
                        "url": "https://brave.com/search",
                        "description": "Brave Search is a private search engine.",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"BRAVE_SEARCH_API_KEY": "test_key"}):
            results = search("brave search", tool="brave")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Brave Search")

    @patch("src.tools.search_tools.requests.get")
    def test_duckduckgo_search_success(self, mock_get):
        """Test duckduckgo_search with a successful HTML response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <div class="result">
            <a class="result__a" href="https://duckduckgo.com">DuckDuckGo</a>
            <a class="result__snippet">Private search engine.</a>
            <a class="result__url" href="https://duckduckgo.com"></a>
        </div>
        """
        mock_get.return_value = mock_response

        results = search("duckduckgo", tool="duckduckgo")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "DuckDuckGo")

    def test_google_pse_factcheck_not_implemented(self):
        """Test that google_pse_factcheck raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            search("test", tool="google_pse")

    def test_search_unknown_tool(self):
        """Test that search raises ValueError for an unknown tool."""
        with self.assertRaises(ValueError):
            search("test", tool="unknown")


if __name__ == "__main__":
    unittest.main()
