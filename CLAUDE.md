# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VeritasLoop is an adversarial multi-agent news verification system that uses LangGraph orchestration to simulate a courtroom debate between:
- **PRO Agent**: Defends claims using institutional sources
- **CONTRA Agent**: Challenges claims with fact-checking
- **JUDGE Agent**: Delivers nuanced 5-category verdicts

The system supports 3 personality styles per agent (Passive, Assertive, Aggressive), each with unique names and communication patterns.

## Development Commands

### Running the Application

**React Web UI (Modern, Recommended):**
```bash
# Terminal 1: Start FastAPI backend with WebSocket
uvicorn api.main:app --reload --port 8000

# Terminal 2: Start React frontend
cd frontend
npm install  # First time only
npm run dev  # Opens at http://localhost:5173
```

**Streamlit UI (Legacy):**
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

**Command-Line Interface:**
```bash
# Verify a text claim
uv run python -m src.cli --input "L'ISTAT ha dichiarato che l'inflazione è al 5%"

# Verify a URL
uv run python -m src.cli --input "https://www.ansa.it/sito/notizie/..."

# Verbose mode with debate transcript
uv run python -m src.cli --input "..." --verbose

# Enable Phoenix tracing
uv run python -m src.cli --input "..." --trace --verbose

# Save results to JSON
uv run python -m src.cli --input "..." --output results.json
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_pro_agent.py -v

# Run specific test function
pytest tests/test_agents.py::test_pro_agent_research -v
```

### Frontend Development

```bash
cd frontend

# Run linter
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend Code Quality

```bash
# Format Python code (Black)
black src/ tests/ api/

# Lint with Ruff
ruff check src/ tests/ api/

# Type checking with mypy
mypy src/ --ignore-missing-imports
```

### WebSocket Testing

```bash
# Install wscat globally
npm install -g wscat

# Connect to WebSocket endpoint
wscat -c ws://localhost:8000/ws/verify

# Send test message
{"input": "Test claim", "type": "Text", "max_iterations": 2, "max_searches": 5, "proPersonality": "ASSERTIVE", "contraPersonality": "ASSERTIVE"}
```

## Architecture

### Three-Agent System with Personalities

**PRO Agent** ([src/agents/pro_agent.py](src/agents/pro_agent.py)):
- **Oliver (PASSIVE)**: Cautious, tentative ("it seems", "perhaps")
- **Marcus (ASSERTIVE)**: Confident, persuasive, fact-based (default)
- **Victor (AGGRESSIVE)**: Forceful, confrontational, emotional

**CONTRA Agent** ([src/agents/contra_agent.py](src/agents/contra_agent.py)):
- **Sophie (PASSIVE)**: Polite, diplomatic, gentle questioning
- **Diana (ASSERTIVE)**: Professional, firm fact-checking (default)
- **Raven (AGGRESSIVE)**: Harsh, relentless, uncompromising

**JUDGE Agent** ([src/agents/judge_agent.py](src/agents/judge_agent.py)):
- No personality system
- Evaluates debate and assigns 5-category verdict

### Personality Configuration

All personality definitions are in [src/config/personalities.py](src/config/personalities.py):
- `Personality` enum: PASSIVE, ASSERTIVE, AGGRESSIVE
- `AGENT_NAMES`: Maps (agent_type, personality) → name
- `PRO_PROMPTS`: System prompts for each PRO personality
- `CONTRA_PROMPTS`: System prompts for each CONTRA personality
- Helper functions: `get_agent_name()`, `get_personality_prompt()`, `get_personality_config()`

**IMPORTANT**: Personality affects ONLY tone and communication style, NOT search strategy or evidence gathering.

### LangGraph Orchestration

The debate flow is managed in [src/orchestrator/graph.py](src/orchestrator/graph.py):

```
START → extract_claim → pro_research → contra_research →
pro_node → contra_node → should_continue? → [loop or judge] → END
```

**GraphState** (defined in [src/models/schemas.py](src/models/schemas.py)):
```python
{
    "claim": Claim,                           # Extracted structured claim
    "messages": Annotated[List[DebateMessage], operator.add],  # Append-only
    "pro_sources": List[Source],
    "contra_sources": List[Source],
    "round_count": int,                       # Current round (0-3)
    "verdict": Optional[dict],
    "max_iterations": int,                    # Default: 3
    "max_searches": int,                      # Default: -1 (unlimited)
    "language": str,                          # Default: "Italian"
    "pro_personality": str,                   # PASSIVE, ASSERTIVE, AGGRESSIVE
    "contra_personality": str                 # PASSIVE, ASSERTIVE, AGGRESSIVE
}
```

**Key Pattern**: `messages` uses `Annotated[List, operator.add]` so nodes append messages instead of replacing.

### Tool Manager & Caching

[src/utils/tool_manager.py](src/utils/tool_manager.py) provides centralized tool access with 1-hour TTL caching:
- **URL cache**: `{url: {content, timestamp}}`
- **Search cache**: `{query_hash: {results, timestamp}}`
- **Metrics tracking**: Cache hits/misses, API calls per tool

**Search hierarchy**:
1. Brave Search API (primary, requires `BRAVE_SEARCH_API_KEY`)
2. DuckDuckGo (fallback, no key required)

### Data Models

All models use Pydantic for validation ([src/models/schemas.py](src/models/schemas.py)):
- `Claim`: Structured claim with entities and category
- `Source`: URL with reliability assessment (high/medium/low)
- `DebateMessage`: Agent message with sources and confidence
- `Verdict`: Final verdict with 5-category classification
- `GraphState`: TypedDict for LangGraph state

### Verdict Categories

| Category | Italian | Description |
|----------|---------|-------------|
| TRUE | VERO | Substantially accurate, strong evidence |
| FALSE | FALSO | Demonstrably false, contradictory evidence |
| PARTIALLY_TRUE | PARZIALMENTE_VERO | Contains truth but misleading/exaggerated |
| MISSING_CONTEXT | CONTESTO_MANCANTE | Technically accurate but misleading without context |
| CANNOT_VERIFY | NON_VERIFICABILE | Insufficient evidence to confirm or deny |

## Critical Files & Their Responsibilities

### Core Backend

- [src/orchestrator/graph.py](src/orchestrator/graph.py): LangGraph workflow definition, node functions
- [src/orchestrator/debate.py](src/orchestrator/debate.py): `pro_turn()` and `contra_turn()` logic
- [src/config/personalities.py](src/config/personalities.py): All personality definitions (MUST update here when modifying personalities)
- [src/models/schemas.py](src/models/schemas.py): Pydantic data models, GraphState definition
- [src/utils/tool_manager.py](src/utils/tool_manager.py): Centralized caching and tool management
- [src/utils/claim_extractor.py](src/utils/claim_extractor.py): LLM-powered claim extraction from text/URLs

### API Layer

- [api/main.py](api/main.py): FastAPI app with WebSocket endpoint for real-time streaming
- [api/server_utils.py](api/server_utils.py): JSON serialization helpers for Pydantic/datetime/UUID

### Frontend

- [frontend/src/App.jsx](frontend/src/App.jsx): Main React component, WebSocket state management
- [frontend/src/components/ConfigPanel.jsx](frontend/src/components/ConfigPanel.jsx): Personality selector UI
- [frontend/src/components/AgentNode.jsx](frontend/src/components/AgentNode.jsx): Visual agent display with personality names
- [frontend/src/components/DebateStream.jsx](frontend/src/components/DebateStream.jsx): Real-time message rendering
- [frontend/src/components/VerdictReveal.jsx](frontend/src/components/VerdictReveal.jsx): Full-screen verdict modal

## Common Development Patterns

### Adding a New Personality

1. **Update enums** in [src/config/personalities.py](src/config/personalities.py):
   ```python
   class Personality(str, Enum):
       PASSIVE = "PASSIVE"
       ASSERTIVE = "ASSERTIVE"
       AGGRESSIVE = "AGGRESSIVE"
       NEW_STYLE = "NEW_STYLE"  # Add here
   ```

2. **Add agent names**:
   ```python
   AGENT_NAMES = {
       "PRO": {
           Personality.NEW_STYLE: "NewName",
       },
       "CONTRA": {
           Personality.NEW_STYLE: "NewName",
       }
   }
   ```

3. **Add system prompts** to `PRO_PROMPTS` and `CONTRA_PROMPTS` dicts

4. **Update frontend** [ConfigPanel.jsx](frontend/src/components/ConfigPanel.jsx) to include new personality option

### Modifying Agent Behavior

**Search strategies** are defined in [src/agents/base_agent.py](src/agents/base_agent.py):
- PRO: `"institutional"` strategy (gov, edu, major news)
- CONTRA: `"fact_check_first"` strategy (fact-checkers, blogs)

**Agent logic** is split:
- Initial research: In respective agent files (`pro_agent.py`, `contra_agent.py`)
- Turn-by-turn debate: In [src/orchestrator/debate.py](src/orchestrator/debate.py) (`pro_turn()`, `contra_turn()`)

### Adding Search Tools

1. **Create tool function** in [src/tools/search_tools.py](src/tools/search_tools.py)
2. **Register in ToolManager** [src/utils/tool_manager.py](src/utils/tool_manager.py) `search_web()` method
3. **Add caching logic** using existing cache patterns
4. **Update metrics tracking** to include new tool name

### Debugging Agent Behavior

**Enable Phoenix tracing**:
```bash
uv run python -m src.cli --input "..." --trace --verbose
# View traces at http://localhost:6006
```

**Check agent prompts**:
```python
from src.config.personalities import get_personality_prompt
prompt = get_personality_prompt("PRO", "AGGRESSIVE")
print(prompt)
```

**Inspect GraphState** during execution:
- Add `print(state)` statements in node functions
- Check `state["messages"]` for full debate history
- Verify `state["round_count"]` for iteration logic

## Environment Variables

Required API keys in `.env` (use `.env.example` as template):
```bash
OPENAI_API_KEY=           # For LLM calls (OpenAI GPT models)
GEMINI_API_KEY=           # Alternative LLM (optional)
BRAVE_SEARCH_API_KEY=     # Primary web search (2000 free/month)
NEWS_API_KEY=             # News aggregation (100 free/day)
REDDIT_CLIENT_ID=         # Social sentiment via PRAW
REDDIT_CLIENT_SECRET=     # PRAW authentication
```

**Optional**:
- `LOG_LEVEL=DEBUG` for verbose logging
- Phoenix traces stored in `data/phoenix/traces.db` automatically

## Testing Strategy

**Coverage Target**: >80% code coverage

**Test Organization** (in `tests/`):
- `test_*_agent.py`: Individual agent logic
- `test_tools.py`: Search and content extraction
- `test_schemas.py`: Pydantic model validation
- `test_tool_manager.py`: Caching behavior
- `test_full_pipeline.py`: End-to-end workflow

**Mock Patterns**:
```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_tool_manager():
    manager = Mock()
    manager.search_web.return_value = [{"url": "...", "title": "...", "snippet": "..."}]
    return manager
```

**Run subset of tests**:
```bash
pytest tests/test_pro_agent.py tests/test_contra_agent.py -v
```

## Frontend Architecture

**Tech Stack**: React 19 + Vite + Tailwind CSS 4 + Framer Motion

**WebSocket Communication**:
- Backend sends: `{type: "status"|"message"|"verdict"|"error", data: {...}}`
- Frontend updates: Agent status, message stream, final verdict

**State Management** (in [App.jsx](frontend/src/App.jsx)):
- `agentStatus`: Tracks PRO/CONTRA/JUDGE states (idle, thinking, speaking)
- `messages`: Debate message history
- `verdict`: Final verdict object
- `wsStatus`: WebSocket connection state

**Styling Conventions**:
- Glassmorphism: `backdrop-blur-xl` with semi-transparent backgrounds
- Animations: Framer Motion `motion.div` with stagger effects
- Icons: Lucide React (`Scale`, `Shield`, `Target`, etc.)
- Responsive: Tailwind breakpoints (`md:`, `lg:`)

## Important Implementation Notes

### GraphState Message Handling

**CRITICAL**: The `messages` field uses `operator.add` annotation:
```python
messages: Annotated[List[DebateMessage], operator.add]
```
This means:
- Multiple nodes can append messages to the same list
- NEVER reassign `state["messages"] = [...]` directly
- Return new messages to append: `return {"messages": [new_message]}`

### Personality System Independence

The personality system affects ONLY:
- System prompt content (tone, language style, rhetorical patterns)
- Agent display name (Oliver, Marcus, Victor, Sophie, Diana, Raven)

It does NOT affect:
- Search strategies (institutional vs fact-check)
- Source reliability assessment
- Number of searches performed
- Evidence gathering logic

### WebSocket Serialization

When sending data via WebSocket, use `serialize_for_json()` from [api/server_utils.py](api/server_utils.py):
```python
from api.server_utils import serialize_for_json
await websocket.send_json(serialize_for_json(verdict))
```
Handles: Pydantic models, datetime, UUID, nested structures

### Cache Invalidation

TTL cache expires after 1 hour. To force refresh:
```python
tool_manager = ToolManager(cache_ttl=0)  # Disable caching
```

### Italian Language Support

Default language is Italian. To change:
```python
state = {
    "language": "English",  # Change here
    # ... other fields
}
```
Affects: Agent output language, verdict summary language

## Related Documentation

- [README.md](README.md): Project overview and quick start
- [docs/INSTALLATION.md](docs/INSTALLATION.md): Setup instructions
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Detailed technical architecture
- [docs/USAGE.md](docs/USAGE.md): User guides for all interfaces
- [docs/REACT_UI.md](docs/REACT_UI.md): React frontend architecture
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): Contributing guidelines
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): Production deployment
- [PLANNING.md](PLANNING.md): Project roadmap
- [TASK.md](TASK.md): Task tracking

## Quick Reference Commands

```bash
# Full stack development
uvicorn api.main:app --reload                    # Terminal 1: Backend
cd frontend && npm run dev                        # Terminal 2: Frontend

# CLI verification with tracing
uv run python -m src.cli --input "claim" --trace --verbose

# Run tests with coverage
pytest --cov=src --cov-report=html

# Format code
black src/ tests/ api/

# Frontend linting
cd frontend && npm run lint
```
