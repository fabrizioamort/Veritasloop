# test_reddit_api.py
import os
import unittest
from unittest.mock import MagicMock, patch

from src.tools import reddit_api


class TestRedditApi(unittest.TestCase):

    @patch('src.tools.reddit_api.praw.Reddit')
    def test_search_reddit_success(self, mock_reddit):
        """
        Test that search_reddit returns a list of posts on a successful API call.
        """
        # Arrange
        mock_submission = MagicMock()
        mock_submission.title = "Test Post"
        mock_submission.url = "http://test.com"
        mock_submission.score = 10
        mock_submission.selftext = "This is a test post."
        mock_submission.comments.replace_more.return_value = []
        mock_submission.comments.list.return_value = []

        mock_subreddit = MagicMock()
        mock_subreddit.search.return_value = [mock_submission]

        mock_reddit_instance = MagicMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance

        os.environ["REDDIT_CLIENT_ID"] = "test_id"
        os.environ["REDDIT_CLIENT_SECRET"] = "test_secret"

        # Act
        results = reddit_api.search_reddit("test query", ["testsubreddit"])

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Post")
        mock_reddit_instance.subreddit.assert_called_once_with("testsubreddit")
        mock_subreddit.search.assert_called_once_with("test query", sort="relevance", time_filter="all")

    @patch('src.tools.reddit_api.praw.Reddit')
    def test_search_reddit_api_error(self, mock_reddit):
        """
        Test that search_reddit returns an empty list when the API call fails.
        """
        # Arrange
        mock_reddit_instance = MagicMock()
        mock_reddit_instance.subreddit.side_effect = Exception("API Error")
        mock_reddit.return_value = mock_reddit_instance

        os.environ["REDDIT_CLIENT_ID"] = "test_id"
        os.environ["REDDIT_CLIENT_SECRET"] = "test_secret"

        # Act
        results = reddit_api.search_reddit("test query", ["testsubreddit"])

        # Assert
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
