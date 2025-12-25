"""
This module provides tools for extracting content from URLs and assessing
the reliability of the sources.
"""
import logging
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from newspaper import Article, ArticleException

from src.config.settings import settings

logger = logging.getLogger(__name__)

def fetch_article(url: str) -> dict[str, Any]:
    """
    Fetches and parses an article from a URL.

    It first tries to use the 'newspaper3k' library. If that fails,
    it falls back to a simple BeautifulSoup implementation.

    Args:
        url (str): The URL of the article to fetch.

    Returns:
        Dict[str, Any]: A dictionary containing the article's title, text,
                        authors, and publish_date. Returns an empty
                        dictionary if fetching fails completely.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {
            "title": article.title,
            "text": article.text,
            "authors": article.authors,
            "publish_date": article.publish_date,
        }
    except ArticleException:
        logger.warning(f"Newspaper3k failed for {url}. Falling back to BeautifulSoup.")
        try:
            response = requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=settings.request_timeout,
                allow_redirects=False
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            title = soup.find('title').get_text() if soup.find('title') else ''

            # A simple heuristic to get the main text content
            paragraphs = soup.find_all('p')
            text = '\n'.join([p.get_text() for p in paragraphs])

            return {
                "title": title,
                "text": text,
                "authors": [],
                "publish_date": None,
            }
        except requests.exceptions.Timeout:
            logger.error(f"Fetch article timed out after {settings.request_timeout}s for URL: {url}")
            return {}
        except requests.RequestException as e:
            logger.error(f"Could not fetch URL {url}: {e}")
            return {}

def assess_source_reliability(url: str) -> str:
    """
    Assesses the reliability of a source based on its URL.

    Args:
        url (str): The URL of the source to assess.

    Returns:
        str: A reliability score ("high", "medium", or "low").
    """
    if not url:
        return "low"

    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # Whitelist of high-reliability domains
    high_reliability_domains = [
        # Major International News
        "reuters.com", "apnews.com", "afp.com", "bbc.com", "nytimes.com",
        "wsj.com", "theguardian.com", "lemonde.fr", "elpais.com",
        # Major Italian News
        "ansa.it", "corriere.it", "repubblica.it", "lastampa.it", "ilsole24ore.com",
        # Government and Institutions
        "gov.it", "europa.eu", "istat.it", "protezionecivile.gov.it",
        "salute.gov.it", "mise.gov.it"
    ]

    # Check if the domain (or a subdomain of it) is in the high-reliability list
    if any(domain.endswith(d) for d in high_reliability_domains):
        return "high"

    # Basic checks for medium vs low
    if parsed_url.scheme == "https":
        return "medium"

    return "low"
