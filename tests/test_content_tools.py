"""
Unit tests for the content extraction tools.
"""

import unittest
from unittest.mock import MagicMock, patch

from newspaper import ArticleException

from src.tools.content_tools import assess_source_reliability, fetch_article


class TestContentTools(unittest.TestCase):

    @patch("src.tools.content_tools.Article")
    def test_fetch_article_newspaper_success(self, MockArticle):
        """Test fetch_article using newspaper3k successfully."""
        mock_instance = MockArticle.return_value
        mock_instance.title = "Test Title"
        mock_instance.text = "Test article text."
        mock_instance.authors = ["John Doe"]
        mock_instance.publish_date = "2024-01-01"

        result = fetch_article("http://example.com")

        self.assertEqual(result["title"], "Test Title")
        self.assertEqual(result["text"], "Test article text.")
        self.assertEqual(result["authors"], ["John Doe"])
        self.assertEqual(result["publish_date"], "2024-01-01")
        mock_instance.download.assert_called_once()
        mock_instance.parse.assert_called_once()

    @patch("src.tools.content_tools.Article")
    @patch("src.tools.content_tools.requests.get")
    def test_fetch_article_fallback_success(self, mock_requests_get, MockArticle):
        """Test fetch_article falling back to BeautifulSoup successfully."""
        # Make newspaper3k fail
        MockArticle.side_effect = ArticleException()

        # Mock requests.get for the fallback
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><head><title>Fallback Title</title></head><body><p>This is a paragraph.</p></body></html>"
        mock_requests_get.return_value = mock_response

        result = fetch_article("http://example.com")

        self.assertEqual(result["title"], "Fallback Title")
        self.assertIn("This is a paragraph.", result["text"])
        self.assertEqual(result["authors"], [])
        self.assertIsNone(result["publish_date"])

    def test_assess_source_reliability(self):
        """Test the assess_source_reliability function with various URLs."""
        # High reliability
        self.assertEqual(assess_source_reliability("https://www.reuters.com/article/idUSKBN2A41M5"), "high")
        self.assertEqual(assess_source_reliability("https://www.ansa.it/sito/notizie/politica/2024/01/01/test_a123.html"), "high")
        self.assertEqual(assess_source_reliability("https://www.salute.gov.it/portale/nuovocoronavirus/dettaglioNotizieNuovoCoronavirus.jsp"), "high")

        # Medium reliability (HTTPS but not in whitelist)
        self.assertEqual(assess_source_reliability("https://www.randomblog.com/news"), "medium")

        # Low reliability (no HTTPS or no URL)
        self.assertEqual(assess_source_reliability("http://unsecure-site.net"), "low")
        self.assertEqual(assess_source_reliability(""), "low")
        self.assertEqual(assess_source_reliability(None), "low")

if __name__ == "__main__":
    unittest.main()
