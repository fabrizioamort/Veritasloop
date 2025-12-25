import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from newspaper import Article, ArticleException

# Load environment variables from .env file
load_dotenv()

# Try to import LLM classes, handling potential missing packages
try:
    from langchain_anthropic import ChatAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from langchain_openai import ChatOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from src.models.schemas import Claim

# Configure logging
logger = logging.getLogger(__name__)

def validate_url(url: str) -> bool:
    """Validate URL is well-formed and uses safe protocols."""
    try:
        result = urlparse(url)
        # Only allow http/https, must have domain, and reasonable length
        return all([
            result.scheme in ('http', 'https'),
            result.netloc,
            len(url) < 2048
        ])
    except:
        return False

def get_llm():
    """
    Factory function to get the appropriate LLM based on available keys and packages.
    Prioritizes Anthropic (Claude) as per planning, then OpenAI.
    """
    if HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY"):
        return ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0
        )
    elif HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(
            model="gpt-5-nano",
            temperature=0
        )
    elif os.getenv("OPENAI_API_KEY"): # Fallback if langchain-openai not found but key exists (using community/deprecated)
         from langchain.chat_models import ChatOpenAI as LegacyChatOpenAI
         return LegacyChatOpenAI(model="gpt-5-mini", temperature=0)

    # If we are here, we might have issues.
    # For now, let's assume one is available or raise error
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
         raise ValueError("No API keys found for Anthropic or OpenAI. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")

    raise ImportError("Could not import LangChain LLM classes. Ensure langchain-anthropic or langchain-openai is installed.")


def extract_from_text(text: str) -> Claim:
    """
    Extracts a structured Claim object from raw text using an LLM.

    Args:
        text (str): The input text containing the claim.

    Returns:
        Claim: The extracted structured claim.
    """
    llm = get_llm()

    # Use structured output for better reliability with modern LLMs
    # This method is more reliable than PydanticOutputParser
    structured_llm = llm.with_structured_output(Claim)

    system_prompt = """You are an expert news analyst and fact-checker.
Your task is to extract a single, verifiable core claim from the provided text.
Identify key entities (people, places, dates, organizations) and categorize the claim.

Instructions:
1. **Core Claim**: Extract the main factual assertion. It must be a single sentence, neutral in tone, and verifiable.
   If the text contains multiple claims, focus on the most significant or controversial one.
2. **Entities**: List all relevant people, places, specific dates/years, and organizations mentioned.
3. **Category**: Classify the claim into one of: politics, health, economy, science, or other.
4. **raw_input**: Set this to the input text provided.

Return the data in the correct format matching the Claim schema.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}"),
    ])

    chain = prompt | structured_llm

    try:
        # The structured LLM will return a Claim object directly
        extracted_claim: Claim = chain.invoke({"text": text})

        # Override raw_input to ensure it matches exactly what was passed
        extracted_claim.raw_input = text

        return extracted_claim

    except Exception as e:
        logger.error(f"Error during claim extraction: {e}")
        # Return a fallback or re-raise. For now, re-raise to be handled by caller or test.
        raise e


def extract_from_url(url: str) -> Claim:
    """
    Extracts a claim from a URL by first downloading and parsing the article.

    Args:
        url (str): The URL of the article.

    Returns:
        Claim: The extracted structured claim.
    """
    if not validate_url(url):
        raise ValueError("Invalid URL format or protocol. Please provide a valid http/https URL.")

    try:
        article = Article(url)
        article.download()
        article.parse()

        # Combine title and text for better context, but keep it reasonable length if needed
        full_text = f"{article.title}\n\n{article.text}"

        # If text is too long, we might want to truncate, but LLMs handle large context well nowadays.
        # Let's limit to first 5000 chars to be safe on tokens/cost if it's huge.
        if len(full_text) > 10000:
             full_text = full_text[:10000]

        logger.info(f"Extracted text from {url} (length: {len(full_text)})")

        claim = extract_from_text(full_text)
        # We might want to store the URL in the raw_input or a separate field if we modify the model later.
        # For now, TASK says: "raw_input: Original text or URL".
        # So we can set raw_input to the URL?
        # schema says raw_input is str.
        # Task 1.2 says: "Extract headline and body -> Pass to extract_from_text()"
        # So extract_from_text returns a Claim with raw_input=full_text.
        # We should probably update raw_input to be the URL for tracking purposes?
        # The schema definition for raw_input is "Original text or URL".
        # Let's set it to the URL since that was the input to THIS function.
        claim.raw_input = url

        return claim

    except ArticleException as e:
        logger.error(f"Failed to fetch article from {url}: {e}")
        raise ValueError(f"Could not fetch content from URL: {url}") from e
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        raise e
