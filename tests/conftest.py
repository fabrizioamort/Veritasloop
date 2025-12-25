import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set dummy API keys for testing to prevent `get_llm` from crashing during import/collection
# if it is called somewhere.
os.environ.setdefault("OPENAI_API_KEY", "dummy-key-for-tests")
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-key-for-tests")
os.environ.setdefault("BRAVE_SEARCH_API_KEY", "dummy-key")
os.environ.setdefault("NEWS_API_KEY", "dummy-key")
os.environ.setdefault("REDDIT_CLIENT_ID", "dummy-id")
os.environ.setdefault("REDDIT_CLIENT_SECRET", "dummy-secret")
