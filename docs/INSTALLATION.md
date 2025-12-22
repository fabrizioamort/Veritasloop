# Installation Guide

Complete installation instructions for VeritasLoop.

## Prerequisites

### Backend Requirements
- **Python 3.12+** (required for modern type hints and performance)
- **API Keys** (at least one LLM provider):
  - OpenAI API key, or
  - Anthropic API key (for Claude)
- **Search API** (required):
  - Brave Search API key (primary, 2000 free queries/month)
- **Optional APIs** (enhance functionality):
  - NewsAPI key (100 free requests/day)
  - Reddit client ID and secret

### Frontend Requirements (for React Web UI)
- **Node.js 18+** (LTS version recommended)
- **npm** or **yarn** package manager (comes with Node.js)

## Step-by-Step Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/veritasloop.git
cd veritasloop
```

### 2. Backend Setup

#### Using `uv` (recommended for faster installs)
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

#### Or using standard `pip`
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file and add your API keys:
```bash
cp .env.example .env
```

> **⚠️ SECURITY WARNING**
> The `.env` file contains your secret API keys. **NEVER** commit this file to Git or share it publicly. The `.gitignore` file is already configured to ignore it, but you must ensure it remains private.

Edit `.env` and add at minimum:
```bash
# Required: At least one LLM provider
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Required: Primary search API
BRAVE_SEARCH_API_KEY=...

# Optional: Enhanced features
NEWS_API_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

### 4. Verify backend installation
```bash
uv run python -m src.cli --help
```

### 5. Frontend Setup (for React Web UI)

```bash
cd frontend
npm install
```

This will install all React dependencies including:
- React 19.2.0
- Vite 7.2.4
- Tailwind CSS 4.1.17
- Framer Motion 12.23.25
- Lucide React 0.556.0

### 6. Verify frontend installation
```bash
npm run dev
```

The frontend dev server should start on http://localhost:5173

## Dependencies

### Backend (Python)

**Core Framework**
- **langchain==1.1.2**: LLM tooling and prompt management
- **langchain-core==1.1.1**: Core LangChain abstractions
- **langchain-openai==1.1.0**: OpenAI integration
- **langgraph>=0.0.30**: State machine orchestration
- **anthropic>=0.18.0**: Anthropic Claude API
- **pydantic>=2.0.0**: Data validation and serialization

**API Server**
- **fastapi>=0.124.0**: Modern web framework for building APIs
- **uvicorn>=0.38.0**: ASGI server for FastAPI
- **websockets>=15.0.1**: WebSocket protocol implementation

**Search & Content**
- **beautifulsoup4>=4.12.0**: HTML parsing
- **newspaper3k>=0.2.8**: Article extraction
- **requests>=2.31.0**: HTTP client

**External APIs**
- **newsapi-python>=0.2.7**: News aggregation
- **praw>=7.7.1**: Reddit API wrapper

**Web Interface (Legacy)**
- **streamlit>=1.28.0**: Interactive web UI

**Observability**
- **arize-phoenix>=4.0.0**: Visual tracing and debugging
- **openinference-instrumentation-langchain>=0.1.0**: LangChain instrumentation

**Development**
- **pytest**: Testing framework
- **pytest-mock**: Mocking utilities
- **python-dotenv>=1.0.0**: Environment variable management

### Frontend (React)

**Core**
- **react@19.2.0**: UI library
- **react-dom@19.2.0**: React DOM renderer

**Build Tools**
- **vite@7.2.4**: Next-generation frontend build tool
- **@vitejs/plugin-react@5.1.1**: React plugin for Vite

**Styling**
- **tailwindcss@4.1.17**: Utility-first CSS framework
- **@tailwindcss/postcss@4.1.17**: Tailwind PostCSS plugin
- **postcss@8.5.6**: CSS processing tool
- **autoprefixer@10.4.22**: PostCSS plugin to parse CSS and add vendor prefixes

**UI Libraries**
- **framer-motion@12.23.25**: Animation library for React
- **lucide-react@0.556.0**: Beautiful & consistent icon toolkit

**Development**
- **eslint@9.39.1**: JavaScript linter
- **eslint-plugin-react-hooks@7.0.1**: ESLint rules for React Hooks
- **eslint-plugin-react-refresh@0.4.24**: ESLint plugin for React Fast Refresh

## Environment Variables

See `.env.example` for the complete list. Required variables:

```bash
# LLM Provider (at least one required)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Search API (required)
BRAVE_SEARCH_API_KEY=...

# Optional: News & Social
NEWS_API_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
```

## Troubleshooting

### Backend Issues

**Python version error**
```bash
# Check Python version
python --version  # Should be 3.12 or higher

# If using pyenv
pyenv install 3.12.0
pyenv local 3.12.0
```

**Missing dependencies**
```bash
# Clear cache and reinstall
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

### Frontend Issues

**Node version error**
```bash
# Check Node version
node --version  # Should be 18.x or higher

# If using nvm
nvm install 18
nvm use 18
```

**npm install fails**
```bash
# Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### API Key Issues

**Invalid API key**
- Verify keys are correctly copied (no extra spaces)
- Check key format (OpenAI starts with `sk-`, Anthropic starts with `sk-ant-`)
- Ensure keys have not expired

**Rate limit errors**
- Brave Search: Free tier has 2000 queries/month
- NewsAPI: Free tier has 100 requests/day
- Consider upgrading to paid tiers for production use

## Next Steps

After installation, proceed to:
- [Usage Guide](USAGE.md) - Learn how to use VeritasLoop
- [Development Guide](DEVELOPMENT.md) - Set up development environment
- [Architecture Overview](ARCHITECTURE.md) - Understand the system
