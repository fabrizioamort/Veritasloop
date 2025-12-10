import os
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup

def brave_search(query: str, count: int = 10) -> List[Dict[str, Any]]:
    """
    Performs a search using the Brave Search API.

    Args:
        query (str): The search query.
        count (int): The number of results to return.

    Returns:
        List[Dict[str, Any]]: A list of search results, each containing
                             'url', 'title', and 'snippet'.
    """
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        print("Warning: BRAVE_SEARCH_API_KEY not found. Skipping Brave search.")
        return []

    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json"
    }
    params = {"q": query, "count": count}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        if "web" not in data or "results" not in data["web"]:
            return []

        results = [
            {
                "url": item.get("url"),
                "title": item.get("title"),
                "snippet": item.get("description"),
            }
            for item in data["web"]["results"]
        ]
        return results

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Brave Search API rate limit exceeded.")
        else:
            print(f"HTTP error during Brave search: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error during Brave search: {e}")
        return []

def duckduckgo_search(query: str, count: int = 10) -> List[Dict[str, Any]]:
    """
    Performs a search using DuckDuckGo and scrapes the results.
    This is a fallback and does not require an API key.

    Args:
        query (str): The search query.
        count (int): The number of results to return.

    Returns:
        List[Dict[str, Any]]: A list of search results.
    """
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for result in soup.find_all("div", class_="result", limit=count):
            title_element = result.find("a", class_="result__a")
            snippet_element = result.find("a", class_="result__snippet")
            url_element = result.find("a", class_="result__url")

            if title_element and snippet_element and url_element:
                results.append(
                    {
                        "title": title_element.get_text(strip=True),
                        "snippet": snippet_element.get_text(strip=True),
                        "url": url_element["href"],
                    }
                )
        return results

    except requests.exceptions.RequestException as e:
        print(f"Error during DuckDuckGo search: {e}")
        return []

def google_pse_factcheck(query: str, count: int = 10) -> List[Dict[str, Any]]:
    """
    Performs a search using a Google Programmable Search Engine
    configured for fact-checking websites.

    Args:
        query (str): The search query.
        count (int): The number of results to return.

    Returns:
        List[Dict[str, Any]]: A list of search results from fact-checking sources.
    """
    api_key = os.getenv("GOOGLE_PSE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_PSE_CX")

    if not api_key or not search_engine_id:
        print("Warning: GOOGLE_PSE_API_KEY or GOOGLE_PSE_CX not found. Skipping Google PSE search.")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": min(count, 10)  # Google PSE limits to 10 results per request
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        if "items" not in data:
            return []

        results = [
            {
                "url": item.get("link"),
                "title": item.get("title"),
                "snippet": item.get("snippet"),
            }
            for item in data["items"]
        ]
        return results

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Google PSE API rate limit exceeded.")
        else:
            print(f"HTTP error during Google PSE search: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error during Google PSE search: {e}")
        return []

def search(query: str, tool: str = "brave", count: int = 10) -> List[Dict[str, Any]]:
    """
    A unified interface to access different search tools.

    Args:
        query (str): The search query.
        tool (str): The search tool to use ('brave', 'duckduckgo', 'google_pse').
        count (int): The number of results to return.

    Returns:
        List[Dict[str, Any]]: A list of search results.

    Raises:
        ValueError: If an unknown tool is specified.
    """
    if tool == "brave":
        return brave_search(query, count=count)
    elif tool == "duckduckgo":
        return duckduckgo_search(query, count=count)
    elif tool == "google_pse":
        return google_pse_factcheck(query, count=count)
    else:
        raise ValueError(f"Unknown search tool: {tool}")
