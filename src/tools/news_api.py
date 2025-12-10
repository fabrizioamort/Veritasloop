# a news_api.py file
import os
from newsapi import NewsApiClient

def search_news(query: str, from_date: str) -> list[dict]:
    """
    Searches for news articles using the NewsAPI.

    Args:
        query (str): The search query.
        from_date (str): The starting date for the search (YYYY-MM-DD).

    Returns:
        list[dict]: A list of news articles.
    """
    newsapi = NewsApiClient(api_key=os.environ["NEWS_API_KEY"])

    try:
        all_articles = newsapi.get_everything(
            q=query,
            from_param=from_date,
            language="it",
            sort_by="relevancy",
            page_size=10
        )
        return all_articles["articles"]
    except Exception as e:
        print(f"Error searching news: {e}")
        return []
