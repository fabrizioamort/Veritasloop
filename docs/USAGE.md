# Usage Guide

Complete guide to using VeritasLoop for news verification.

## Quick Start

### Web Interface (Recommended for First-Time Users)

#### React Web UI (Modern SPA - Recommended)

The new React-based web interface offers a professional, responsive experience with real-time updates:

```bash
# Terminal 1: Start the FastAPI backend
uvicorn api.main:app --reload --port 8000

# Terminal 2: Start the React frontend
cd frontend
npm install  # Only needed the first time
npm run dev
```

Open your browser to **http://localhost:5173** and you'll see:

- 🛡️ **PRO Zone** (left): PRO Agent status with visual indicators
- ⚖️ **Arena** (center): Real-time debate stream with configuration controls
- 🔍 **CONTRA Zone** (right): CONTRA Agent status with visual indicators

**Features:**
- Real-time WebSocket communication with smooth animations
- Glassmorphism UI with cyber-courtroom aesthetic
- Configurable parameters (max iterations, max searches)
- Full-screen verdict reveal with detailed analysis
- Responsive design for desktop and tablet
- **Production Features (v0.4.0)**:
  - ⏱️ 5-minute automatic timeout for long-running verifications
  - 🔄 Automatic WebSocket reconnection (max 3 retries)
  - 🎨 Skeleton loading states during initialization
  - 🛡️ Rate limiting protection (10 requests/minute per IP)
  - ♿ Full accessibility with ARIA attributes and keyboard navigation

**Example workflow:**

1. Select input type (TEXT or URL)
2. Configure parameters (optional): Max Iterations (1-10), Max Searches (-1 = unlimited)
3. Enter a claim like: `"L'ISTAT ha dichiarato che l'inflazione è al 5% nel 2024"`
4. Click **VERIFY** to start verification
5. Watch the agents' status change in real-time (idle → thinking → speaking)
6. Follow the debate stream in the center arena
7. View the final verdict in the dramatic reveal overlay

#### Streamlit Web UI (Legacy - Alternative)

The Streamlit interface is still fully functional and provides an alternative experience:

```bash
# Option 1: Use the launcher script (easiest)
./launch_streamlit.sh  # Linux/Mac
launch_streamlit.bat   # Windows

# Option 2: Direct launch
streamlit run app.py

# Option 3: Using uv
uv run streamlit run app.py
```

Open your browser to **http://localhost:8501** and you'll see:

- 🛡️ **PRO Column** (left): Arguments supporting the claim
- ⚖️ **Arena** (center): Progress tracking and debate status
- 🔍 **CONTRA Column** (right): Counter-arguments and contradictions

### Command-Line Interface

For scripting and automation:

```bash
# Verify a text claim
uv run python -m src.cli --input "L'ISTAT ha dichiarato che l'inflazione è al 5%"

# Verify a news article URL
uv run python -m src.cli --input "https://www.ansa.it/sito/notizie/..."

# Show detailed debate transcript
uv run python -m src.cli --input "..." --verbose

# Save results to JSON for integration
uv run python -m src.cli --input "..." --output results.json

# Enable visual tracing with Phoenix
uv run python -m src.cli --input "..." --trace --verbose
```

## CLI Options Reference

```bash
uv run python -m src.cli [OPTIONS]

Required:
  --input, -i TEXT        The claim text or URL to verify

Optional:
  --output, -o PATH       Save verdict to JSON file
  --verbose, -v           Show detailed debate transcript
  --trace                 Enable Phoenix observability (visual tracing)
  --debug                 Enable debug-level logging
  --no-cache              Disable caching for this verification
  --no-banner             Skip the ASCII art banner
  --help                  Show help message
```

## Programmatic Usage

Integrate VeritasLoop into your Python applications:

```python
import os
from datetime import datetime, timedelta
from src.tools.search_tools import search
from src.tools.content_tools import fetch_article, assess_source_reliability
from src.tools.news_api import search_news
from src.tools.reddit_api import search_reddit
from src.orchestrator.graph import get_app

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Example 1: Use individual tools
search_results = search("Italy inflation rate 2024", tool="brave")
for result in search_results:
    print(f"Title: {result['title']}\nURL: {result['url']}\n")

# Example 2: Assess source reliability
reliability = assess_source_reliability("https://www.istat.it/...")
print(f"Source Reliability: {reliability}")  # Output: "high"

# Example 3: Fetch and parse article content
article_content = fetch_article("https://www.ansa.it/...")
if article_content:
    print(f"Article Title: {article_content['title']}")
    print(f"Text: {article_content['text'][:200]}...")

# Example 4: Search news with NewsAPI
if os.getenv("NEWS_API_KEY"):
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    news_articles = search_news("ECB interest rates", from_date=one_month_ago)
    print(f"Found {len(news_articles)} news articles.")

# Example 5: Search Reddit for social sentiment
if os.getenv("REDDIT_CLIENT_ID"):
    reddit_posts = search_reddit("Italy government stability", subreddits=["worldnews", "europe"])
    print(f"Found {len(reddit_posts)} Reddit posts.")

# Example 6: Run full verification programmatically
app = get_app()
result = app.invoke({
    "claim": None,
    "messages": [],
    "pro_sources": [],
    "contra_sources": [],
    "round_count": 0,
    "verdict": None
}, {"raw_input": "Your claim here"})

print(f"Verdict: {result['verdict']['verdict']}")
print(f"Confidence: {result['verdict']['confidence_score']}%")
print(f"Summary: {result['verdict']['summary']}")
```

## Verdict Categories

VeritasLoop classifies claims into five nuanced categories:

| Verdict | Italian | Description | When Used |
|---------|---------|-------------|-----------|
| ✅ **TRUE** | `VERO` | Substantially accurate and supported by strong independent evidence | Core claim verified by multiple authoritative sources |
| ❌ **FALSE** | `FALSO` | Demonstrably false with credible contradictory evidence | Clear factual errors contradicted by reliable sources |
| ⚠️ **PARTIALLY TRUE** | `PARZIALMENTE_VERO` | Contains kernel of truth but misleading or exaggerated | Mixed evidence, some facts correct but context distorts meaning |
| 🔍 **MISSING CONTEXT** | `CONTESTO_MANCANTE` | Technically accurate but misleading without proper context | True data point but lacks essential background information |
| ❓ **CANNOT VERIFY** | `NON_VERIFICABILE` | Insufficient credible evidence to confirm or deny | Lack of authoritative sources or contradictory evidence |

## Example Output

```
═════════════════════════════════════════════════════════════════
✅  VERDETTO: VERO
   Confidenza: 85%
═════════════════════════════════════════════════════════════════

📝 Sintesi:
La notizia riporta un dato reale confermato da fonti ufficiali dell'ISTAT.
Il tasso di inflazione del 5% corrisponde ai dati pubblicati nel rapporto
mensile di gennaio 2024, con particolare riferimento all'indice dei prezzi
al consumo per l'intera collettività nazionale (NIC).

📊 Analisi:
  Punti di forza PRO:
    • Fonti istituzionali autorevoli (ISTAT, Banca d'Italia)
    • Dati statistici verificabili e tracciabili
    • Conferma da parte di multiple agenzie di stampa

  Punti di forza CONTRA:
    • Nessuna contraddizione significativa trovata
    • Necessità di contestualizzare il dato rispetto al periodo precedente

  Fatti condivisi:
    • L'ISTAT ha effettivamente pubblicato i dati sull'inflazione
    • Il valore del 5% è corretto per il periodo di riferimento

  Punti controversi:
    • Interpretazione del dato (tendenza positiva o negativa)

📚 Fonti Principali (8 verificate):
  [1] ISTAT - Inflazione Report Gennaio 2024
      https://www.istat.it/it/archivio/288969
      Affidabilità: Alta 🟢

  [2] Banca d'Italia - Bollettino Economico
      https://www.bancaditalia.it/...
      Affidabilità: Alta 🟢

  [3] ANSA - ISTAT conferma inflazione al 5%
      https://www.ansa.it/...
      Affidabilità: Alta 🟢

⏱️  Metadata:
  • Tempo di elaborazione: 42.3 secondi
  • Round di dibattito: 2
  • Fonti totali analizzate: 23
```

## Observability & Debugging

### Enable Phoenix Tracing

#### Method 1: CLI with Auto-Start (Easiest)

```bash
uv run python -m src.cli --input "Your claim" --trace --verbose
```

This will:
1. Automatically start Phoenix server (if not running)
2. Instrument all LangChain and agent operations
3. Display link to trace viewer: http://localhost:6006
4. Keep server running after verification for trace review

#### Method 2: Streamlit UI Toggle

In the Streamlit web interface:
1. Open the sidebar (click **>** icon if collapsed)
2. Enable **"Attiva Phoenix Tracing"** toggle
3. Phoenix server starts automatically
4. All verifications are traced
5. Access traces at http://localhost:6006

#### Method 3: Manual Phoenix Control (Advanced)

Start Phoenix manually in a separate terminal for more control:

```bash
# Start Phoenix with persistent storage (recommended)
phoenix serve --database-url "sqlite:///data/phoenix/traces.db"

# Then run verifications (traces automatically sent to running Phoenix)
uv run python -m src.cli --input "Your claim" --verbose
```

**Benefits of manual start:**
- Keep one Phoenix instance across multiple verification runs
- All traces accumulate in the same database
- Full control over server lifecycle
- Better for development and debugging sessions

### What You Can See in Phoenix

Once Phoenix is running, access **http://localhost:6006** to explore:

#### 1. Trace Timeline
Visual representation of the entire verification flow

#### 2. Agent Reasoning
Detailed view of each agent's decision-making

#### 3. LLM Interactions
Complete visibility into language model usage

#### 4. Tool Calls
Monitor all external API interactions

#### 5. Performance Metrics
Analyze system performance

#### 6. Multi-Agent Interactions
See how agents respond to each other

## Performance & Metrics

VeritasLoop automatically tracks comprehensive performance metrics:

### Tracked Metrics

- **Processing Time**: Total verification duration (typically 30-90 seconds)
- **API Calls**: Count per tool/API (search, content, news, Reddit)
- **Cache Performance**: Hit/miss ratios and time saved
- **Token Usage**: By agent and total
- **Source Counts**: Total sources checked vs. used in final verdict
- **Round Statistics**: Number of debate rounds completed

### Example Metrics

```json
{
  "processing_time_seconds": 61.4,
  "rounds_completed": 2,
  "total_sources_checked": 23,
  "sources_used_in_verdict": 8,
  "api_calls": {
    "brave_search": 6,
    "duckduckgo_search": 2,
    "content_fetch": 15,
    "news_api": 3,
    "reddit_api": 1
  },
  "cache_performance": {
    "hit_rate": 0.34,
    "time_saved_seconds": 12.7
  },
  "token_usage": {
    "pro_agent": 4521,
    "contra_agent": 5138,
    "judge_agent": 3287,
    "total": 12946
  }
}
```

## Production Features & Limitations

### Rate Limiting

VeritasLoop implements IP-based rate limiting to prevent abuse:

**Default Limits:**
- **10 verifications per minute** per IP address
- Automatic HTTP 429 response when limit exceeded
- Counter resets every 60 seconds

**What happens when rate limited:**
1. WebSocket connection rejected immediately
2. Error message displayed: "Rate limit exceeded. Please try again later."
3. Must wait until the next minute to retry

**For administrators:**
Adjust rate limit in `api/main.py`:
```python
@limiter.limit("20/minute")  # Change from default 10/minute
```

### Automatic Timeouts

**Verification Timeout:**
- Maximum execution time: **5 minutes**
- Automatic cleanup and WebSocket closure
- Status message: "VERIFICATION TIMED OUT"

**HTTP Request Timeout:**
- External API timeout: **10 seconds**
- Prevents hanging on slow or unresponsive services
- Automatic fallback to alternative search methods

**WebSocket Reconnection:**
- Maximum retry attempts: **3**
- Retry delay: **3 seconds** between attempts
- Status updates: "RECONNECTING... (1/3)", "(2/3)", "(3/3)"
- Final failure: "CONNECTION FAILED"

### Error Handling

VeritasLoop gracefully handles errors without exposing internal details:

**User-Facing Errors:**
- "Invalid input provided" (validation errors)
- "Failed to process the provided URL" (URL extraction errors)
- "An unexpected error occurred" (unhandled exceptions)

**Internal Logging:**
- Full error details logged server-side
- Stack traces preserved for debugging
- Error context included (request data, timestamps)

**LLM Failures:**
- Agent returns fallback message
- Confidence score set to 0%
- Debate continues with degraded quality
- Never causes full system failure

### Accessibility Features

**Keyboard Navigation:**
- `Tab`: Navigate between interactive elements
- `Enter`: Submit form or activate button
- `Escape`: Close modal dialogs
- `Arrow keys`: Navigate within select dropdowns

**Screen Reader Support:**
- All form inputs have descriptive labels
- Status announcements for verification progress
- ARIA live regions for dynamic content updates
- Modal dialogs properly announce when opened

**Visual Indicators:**
- Loading states with skeleton loaders
- Color-coded verdict categories
- Status text updates during processing
- Clear error messages

## Best Practices

### For CLI Usage

1. **Use `--verbose` for debugging**: See full debate transcript
2. **Save results with `--output`**: Keep verification records
3. **Enable tracing for complex cases**: Use `--trace` to debug issues
4. **Disable cache when testing**: Use `--no-cache` for fresh results
5. **Monitor for timeouts**: Long verifications may hit 5-minute limit

### For Web UI Usage

1. **Configure parameters wisely**:
   - Max iterations: 3 is usually optimal (1-5 range)
   - Max searches: -1 for unlimited, or 5-10 for faster results
2. **Review sources**: Check reliability indicators
3. **Analyze both sides**: Read PRO and CONTRA arguments
4. **Consider context**: Missing context verdicts need careful interpretation

### For Programmatic Usage

1. **Check API keys**: Verify environment variables are set
2. **Handle errors gracefully**: Wrap calls in try-except blocks
3. **Cache results**: Store verdicts for future reference
4. **Monitor performance**: Track token usage and API calls
5. **Respect rate limits**: Don't overwhelm external APIs

## Next Steps

- [Architecture Overview](ARCHITECTURE.md) - Understand how it works
- [React UI Guide](REACT_UI.md) - Learn about the modern web interface
- [Development Guide](DEVELOPMENT.md) - Contribute to the project
