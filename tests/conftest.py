import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))

# Set dummy API keys for testing to prevent `get_llm` from crashing during import/collection
# if it is called somewhere.
os.environ.setdefault("OPENAI_API_KEY", "dummy-key-for-tests")
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-key-for-tests")
os.environ.setdefault("BRAVE_SEARCH_API_KEY", "dummy-key")
os.environ.setdefault("NEWS_API_KEY", "dummy-key")
os.environ.setdefault("REDDIT_CLIENT_ID", "dummy-id")
os.environ.setdefault("REDDIT_CLIENT_SECRET", "dummy-secret")
