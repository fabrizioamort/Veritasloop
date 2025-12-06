# VeritasLoop - Multi-Agent News Verification System

VeritasLoop is an adversarial multi-agent system that verifies news authenticity through dialectical debate. Instead of single-pass fact-checking, the system simulates a courtroom where a PRO agent defends the news, a CONTRA agent challenges it, and a JUDGE agent evaluates the arguments to deliver a nuanced verdict.

## Core Features Implemented

*   **Data Models**: Robust Pydantic models (`Claim`, `Source`, `DebateMessage`, `Verdict`) for structured data flow and validation.
*   **Claim Extractor**: An advanced utility (`src/utils/claim_extractor.py`) to automatically extract the core verifiable claim from a block of text or a URL.
*   **Tool Manager**: A caching system (`src/utils/tool_manager.py`) to avoid redundant API calls and web requests for the same URLs or search queries within a session.
*   **Web Search Tools**: A multi-layered search module (`src/tools/search_tools.py`) with a primary API-based tool (Brave Search) and a scraping-based fallback (DuckDuckGo).
*   **Content Extraction Tools**: A content extractor (`src/tools/content_tools.py`) that uses `newspaper3k` and a `BeautifulSoup` fallback to parse articles, along with a source reliability estimator.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd veritasloop
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    # Using uv
    uv venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    uv pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**
    Create a `.env` file by copying the `.env.example` and fill in the required API keys:
    ```bash
    cp .env.example .env
    # Now edit .env with your keys
    ```

## Usage

*Further implementation is required for a full user-facing interface. The following shows how the implemented tools can be used programmatically.*

```python
from src.tools.search_tools import search
from src.tools.content_tools import fetch_article, assess_source_reliability

# Example: Using the search tool
search_results = search("Italy inflation rate 2024", tool="brave")
for result in search_results:
    print(f"Title: {result['title']}\nURL: {result['url']}\n")

# Example: Using content extraction tools
if search_results:
    article_url = search_results[0]['url']
    
    reliability = assess_source_reliability(article_url)
    print(f"Source Reliability: {reliability}")

    article_content = fetch_article(article_url)
    if article_content:
        print(f"\nArticle Title: {article_content['title']}")
        print(f"Text Snippet: {article_content['text'][:200]}...")
```
