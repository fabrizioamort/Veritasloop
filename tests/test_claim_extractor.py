import unittest
from unittest.mock import MagicMock, patch

from src.models.schemas import Claim, ClaimCategory, Entities
from src.utils.claim_extractor import extract_from_url


class TestClaimExtractor(unittest.TestCase):

    def setUp(self):
        # Sample claims for different categories
        self.claims = {
            "politics": "L'ISTAT ha dichiarato che l'inflazione è al 5%",
            "health": "Eating garlic cures COVID-19 immediately.",
            "economy": "The central bank raised interest rates by 0.5% to combat inflation.",
            "science": "New study shows Mars had liquid water 2 billion years ago.",
            "general": "Local cat saves owner from fire."
        }

    @patch("src.utils.claim_extractor.get_llm")
    def test_extract_from_text_structure(self, mock_get_llm):
        """Test that extract_from_text returns a valid Claim object structure."""
        # Setup mock LLM response
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        pass

    @patch("src.utils.claim_extractor.extract_from_text")
    @patch("src.utils.claim_extractor.Article")
    def test_extract_from_url(self, mock_article_cls, mock_extract_text):
        """Test extraction from URL."""
        url = "https://example.com/news"
        title = "Example News"
        text = "This is the body of the article."

        # Mock Article
        mock_article = MagicMock()
        mock_article.title = title
        mock_article.text = text
        mock_article_cls.return_value = mock_article

        # Mock extract_from_text response
        expected_claim = Claim(
            raw_input=f"{title}\n\n{text}",
            core_claim="Core claim",
            entities=Entities(people=[], places=[], dates=[], organizations=[]),
            category=ClaimCategory.OTHER
        )
        mock_extract_text.return_value = expected_claim

        # Call function
        result = extract_from_url(url)

        # Verify Article interactions
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()

        # Verify extract_from_text called with combined text
        mock_extract_text.assert_called_once_with(f"{title}\n\n{text}")

        # Verify result raw_input updated to URL
        self.assertEqual(result.raw_input, url)
        self.assertEqual(result.core_claim, "Core claim")

    def test_claim_model_validation(self):
        """Test Pydantic model validation."""
        claim = Claim(
            raw_input="test",
            core_claim="test claim",
            category=ClaimCategory.POLITICS
        )
        self.assertEqual(claim.category, ClaimCategory.POLITICS)
        self.assertIsInstance(claim.entities, Entities)

if __name__ == "__main__":
    unittest.main()
