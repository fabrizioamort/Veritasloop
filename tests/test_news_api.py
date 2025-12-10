# test_news_api.py
import os
import unittest
from unittest.mock import patch, MagicMock
from src.tools import news_api

class TestNewsApi(unittest.TestCase):

    @patch('src.tools.news_api.NewsApiClient')
    def test_search_news_success(self, mock_news_api_client):
        """
        Test that search_news returns a list of articles on a successful API call.
        """
        # Arrange
        mock_api_instance = MagicMock()
        mock_api_instance.get_everything.return_value = {
            "articles": [
                {"title": "Test Article 1", "content": "Content 1"},
                {"title": "Test Article 2", "content": "Content 2"},
            ]
        }
        mock_news_api_client.return_value = mock_api_instance
        os.environ["NEWS_API_KEY"] = "test_key"

        # Act
        articles = news_api.search_news("test query", "2024-01-01")

        # Assert
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["title"], "Test Article 1")
        mock_api_instance.get_everything.assert_called_once_with(
            q="test query",
            from_param="2024-01-01",
            language="it",
            sort_by="relevancy",
            page_size=10
        )

    @patch('src.tools.news_api.NewsApiClient')
    def test_search_news_api_error(self, mock_news_api_client):
        """
        Test that search_news returns an empty list when the API call fails.
        """
        # Arrange
        mock_api_instance = MagicMock()
        mock_api_instance.get_everything.side_effect = Exception("API Error")
        mock_news_api_client.return_value = mock_api_instance
        os.environ["NEWS_API_KEY"] = "test_key"

        # Act
        articles = news_api.search_news("test query", "2024-01-01")

        # Assert
        self.assertEqual(len(articles), 0)

if __name__ == '__main__':
    unittest.main()
