# Development Guide

Guide for contributors and developers working on VeritasLoop.

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Git
- Code editor (VS Code recommended)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/veritasloop.git
cd veritasloop

# Backend setup
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# Copy environment template
cp .env.example .env
# Edit .env and add your API keys
```

### Development Tools

**Install development dependencies:**
```bash
# Python code quality tools
uv pip install black ruff mypy pytest pytest-cov

# Or add to requirements-dev.txt
```

**Recommended VS Code extensions:**
- Python (Microsoft)
- Pylance
- Black Formatter
- ESLint
- Prettier
- Tailwind CSS IntelliSense

## Project Structure

```
veritasloop/
├── api/                        # FastAPI backend
│   ├── main.py                 # WebSocket server
│   └── server_utils.py         # Utilities
│
├── frontend/                   # React Web UI
│   ├── src/
│   │   ├── components/         # React components
│   │   └── styles/             # CSS files
│   └── package.json
│
├── src/                        # Core Python backend
│   ├── cli.py                  # CLI entry point
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── agents/
│   │   ├── base_agent.py       # Base class
│   │   ├── pro_agent.py        # PRO agent
│   │   ├── contra_agent.py     # CONTRA agent
│   │   └── judge_agent.py      # JUDGE agent
│   ├── orchestrator/
│   │   ├── graph.py            # LangGraph state machine
│   │   └── debate.py           # Debate logic
│   ├── tools/
│   │   ├── search_tools.py     # Search APIs
│   │   ├── content_tools.py    # Content extraction
│   │   ├── news_api.py         # NewsAPI
│   │   └── reddit_api.py       # Reddit API
│   └── utils/
│       ├── tool_manager.py     # Caching
│       ├── claim_extractor.py  # LLM extraction
│       └── logger.py           # Logging
│
├── tests/                      # Test suite
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_full_pipeline.py
│
├── docs/                       # Documentation
│   ├── INSTALLATION.md
│   ├── USAGE.md
│   ├── ARCHITECTURE.md
│   ├── REACT_UI.md
│   └── DEPLOYMENT.md
│
└── data/                       # Runtime data
    └── phoenix/
        └── traces.db           # Phoenix traces
```

## Production Readiness Standards

As of Version 0.4.0, VeritasLoop follows enterprise-grade production standards:

### Security Requirements

- ✅ **Input Validation**: All external inputs validated with Pydantic
- ✅ **CORS Configuration**: No wildcards, environment-based origins
- ✅ **Error Sanitization**: Generic user messages, detailed server logs
- ✅ **Rate Limiting**: IP-based limits to prevent abuse
- ✅ **URL Validation**: Protocol and length checks before fetching
- ✅ **Timeout Protection**: 10-second HTTP timeouts, 5-minute verification timeout

### Stability Requirements

- ✅ **Error Handling**: Try-catch blocks around all external calls
- ✅ **Graceful Degradation**: Fallback messages on LLM failures
- ✅ **Cache Limits**: LRU eviction with 1000-entry maximum
- ✅ **Reconnection Logic**: WebSocket auto-retry (max 3 attempts)
- ✅ **Environment Validation**: Startup checks for required API keys

### Accessibility Requirements

- ✅ **ARIA Compliance**: All interactive elements have proper ARIA attributes
- ✅ **Keyboard Navigation**: Full keyboard accessibility
- ✅ **Screen Reader Support**: Descriptive labels and live regions
- ✅ **Loading States**: Skeleton loaders and status indicators

**When Contributing:**
- Maintain or improve these standards
- Add tests for new security features
- Document accessibility considerations
- Update error handling patterns

## Code Style & Standards

### Python (Backend)

**Style Guide**: PEP 8 with Black formatting

**Formatting:**
```bash
# Format all Python files
black src/ tests/ api/

# Check without modifying
black --check src/
```

**Linting:**
```bash
# Run ruff linter
ruff check src/ tests/ api/

# Auto-fix issues
ruff check --fix src/
```

**Type Checking:**
```bash
# Run mypy
mypy src/ --ignore-missing-imports
```

**Code Standards:**
- Use type hints for all function parameters and returns
- Add docstrings to all public functions and classes
- Maximum line length: 88 characters (Black default)
- Use Pydantic for data validation
- Prefer composition over inheritance
- **Production Standards (v0.4.0)**:
  - Use structured logging (`logger.error()`, not `print()`)
  - Wrap external calls in try-except with sanitized error messages
  - Add timeouts to all HTTP requests (`timeout=settings.request_timeout`)
  - Validate all user inputs with Pydantic models
  - Implement graceful degradation for optional features

**Example:**
```python
from typing import List, Optional
from pydantic import BaseModel

class Source(BaseModel):
    """Represents a source used in verification.

    Attributes:
        url: The source URL
        title: Page title
        reliability: Reliability level (high, medium, low)
    """
    url: str
    title: str
    reliability: str

def fetch_sources(query: str, max_results: int = 10) -> List[Source]:
    """Fetch sources for the given query.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of Source objects

    Raises:
        APIError: If the search API fails
    """
    # Implementation
    pass
```

### JavaScript/React (Frontend)

**Style Guide**: Airbnb JavaScript Style Guide (via ESLint)

**Formatting:**
```bash
cd frontend

# Run ESLint
npm run lint

# Auto-fix issues
npm run lint:fix
```

**Code Standards:**
- Use functional components with hooks (no class components)
- Use PropTypes or TypeScript for prop validation (future)
- Maximum line length: 100 characters
- Use meaningful variable names
- Prefer const over let, never use var

**Example:**
```javascript
import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * AgentNode displays the current status of an agent
 *
 * @param {Object} props
 * @param {string} props.agent - Agent identifier ('pro' or 'contra')
 * @param {string} props.status - Current status ('idle', 'thinking', 'speaking')
 */
function AgentNode({ agent, status }) {
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    setIsAnimating(status !== 'idle');
  }, [status]);

  return (
    <div className={`agent-node ${isAnimating ? 'animating' : ''}`}>
      {/* Component content */}
    </div>
  );
}

AgentNode.propTypes = {
  agent: PropTypes.oneOf(['pro', 'contra']).isRequired,
  status: PropTypes.oneOf(['idle', 'thinking', 'speaking']).isRequired,
};

export default AgentNode;
```

## Testing

### Backend Tests

**Run all tests:**
```bash
pytest
```

**Run specific test file:**
```bash
pytest tests/test_pro_agent.py
```

**Run with verbose output:**
```bash
pytest -v
```

**Run with coverage report:**
```bash
pytest --cov=src --cov-report=html
# View report: open htmlcov/index.html
```

**Test Structure:**
```python
import pytest
from src.agents.pro_agent import ProAgent

@pytest.fixture
def pro_agent():
    """Fixture that creates a PRO agent instance."""
    return ProAgent(model_name="gpt-4")

def test_pro_agent_initial_research(pro_agent):
    """Test that PRO agent performs initial research correctly."""
    claim = "Test claim"
    result = pro_agent.initial_research(claim)

    assert result is not None
    assert len(result.sources) > 0
    assert result.confidence > 0

def test_pro_agent_defense(pro_agent):
    """Test that PRO agent generates defense argument."""
    contra_rebuttal = "Counter-argument"
    defense = pro_agent.generate_defense(contra_rebuttal)

    assert defense is not None
    assert len(defense.content) > 0
```

**Coverage Target**: Maintain >80% code coverage

### Frontend Tests

**Future Enhancement**: Add frontend testing

**Recommended Tools:**
- **Unit Tests**: Vitest or Jest + React Testing Library
- **E2E Tests**: Playwright or Cypress
- **Component Tests**: Storybook

**Example test structure:**
```javascript
import { render, screen } from '@testing-library/react';
import AgentNode from './AgentNode';

describe('AgentNode', () => {
  test('renders with idle status', () => {
    render(<AgentNode agent="pro" status="idle" />);
    expect(screen.getByText(/PRO/i)).toBeInTheDocument();
  });

  test('shows animation when thinking', () => {
    const { container } = render(<AgentNode agent="pro" status="thinking" />);
    expect(container.firstChild).toHaveClass('animating');
  });
});
```

## Git Workflow

### Branching Strategy

**Main branches:**
- `main`: Production-ready code
- `develop`: Integration branch for features

**Feature branches:**
- `feature/agent-improvements`: New features
- `bugfix/cache-error`: Bug fixes
- `docs/update-readme`: Documentation updates

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(agents): add confidence scoring to CONTRA agent

Implement dynamic confidence calculation based on source
quality and contradiction strength.

Closes #42

---

fix(cache): prevent race condition in tool manager

Add locking mechanism to prevent concurrent cache updates
from corrupting data.

---

docs(readme): update installation instructions

Add troubleshooting section for common setup issues.
```

### Pull Request Process

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

3. **Run tests:**
   ```bash
   pytest --cov=src
   cd frontend && npm run lint
   ```

4. **Push to GitHub:**
   ```bash
   git push origin feature/my-feature
   ```

5. **Create Pull Request** with:
   - Clear title and description
   - Reference related issues
   - Screenshots (for UI changes)
   - Test results

6. **Code Review:**
   - Address reviewer feedback
   - Keep discussions respectful
   - Update PR based on comments

7. **Merge:**
   - Squash and merge (preferred)
   - Delete feature branch after merge

## Development Workflows

### Backend Development

**Run CLI in development:**
```bash
uv run python -m src.cli --input "test claim" --verbose --trace
```

**Run FastAPI server with auto-reload:**
```bash
uvicorn api.main:app --reload --port 8000
```

**Test WebSocket connection:**
```bash
# Install wscat: npm install -g wscat
wscat -c ws://localhost:8000/ws/verify

# Send test message:
{"input": "Test claim", "type": "Text", "max_iterations": 2, "max_searches": 5}
```

### Frontend Development

**Start dev server:**
```bash
cd frontend
npm run dev
```

**Build and preview:**
```bash
npm run build
npm run preview
```

**Component development:**
- Edit component in `src/components/`
- Changes auto-reload via Vite HMR
- Check browser console for errors

### Full Stack Development

**Terminal 1: Backend**
```bash
uvicorn api.main:app --reload --port 8000
```

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```

**Terminal 3: Phoenix (optional)**
```bash
phoenix serve --database-url "sqlite:///data/phoenix/traces.db"
```

## Debugging Tips

### Backend Debugging

**1. Enable verbose logging:**
```python
# In .env
LOG_LEVEL=DEBUG
```

**2. Use Python debugger:**
```python
import pdb; pdb.set_trace()  # Set breakpoint
```

**3. Phoenix traces:**
```bash
# Enable tracing
uv run python -m src.cli --input "..." --trace --verbose

# View traces at http://localhost:6006
```

**4. Print state:**
```python
# In graph.py or agents
print(f"Current state: {state}")
print(f"Messages: {state['messages']}")
```

### Frontend Debugging

**1. Browser DevTools:**
- Console: Check for JavaScript errors
- Network: Monitor WebSocket messages
- React DevTools: Inspect component state

**2. Console logging:**
```javascript
console.log('WebSocket message:', event);
console.log('Current state:', agentStatus);
```

**3. React DevTools:**
- Install React DevTools browser extension
- Inspect component props and state
- Profile performance

## Contributing Guidelines

### Before Contributing

1. **Check existing issues**: Avoid duplicate work
2. **Open discussion**: For major changes, open an issue first
3. **Read documentation**: Understand architecture

### Contribution Process

1. **Fork repository**
2. **Create feature branch**
3. **Make changes**:
   - Write code
   - Add tests
   - Update documentation
4. **Run tests**: Ensure all tests pass
5. **Format code**: Run Black/ESLint
6. **Commit changes**: Use conventional commits
7. **Push to fork**
8. **Create Pull Request**

### PR Requirements

**Must have:**
- ✅ All tests passing
- ✅ Code formatted (Black/ESLint)
- ✅ Type hints (Python) or PropTypes (React)
- ✅ Docstrings for new functions
- ✅ Updated documentation (if applicable)
- ✅ **Security checks (v0.4.0)**:
  - Input validation for user-provided data
  - Error sanitization (no internal details exposed)
  - Timeout configuration for external calls
  - ARIA attributes for new UI components (if applicable)

**Good to have:**
- Test coverage maintained or improved
- Screenshots for UI changes
- Performance benchmarks for optimizations
- Accessibility testing results
- Security audit for sensitive changes

### Code Review Checklist

**For Reviewers:**
- [ ] Code follows style guidelines
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Changes are backward compatible (or migration provided)

## Performance Optimization

### Profiling

**Python profiling:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = app.invoke(state)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

**React profiling:**
- Use React DevTools Profiler tab
- Identify slow components
- Optimize with React.memo, useMemo, useCallback

### Optimization Tips

**Backend:**
- Cache expensive operations (already implemented)
- Use async/await for I/O operations
- Minimize LLM token usage
- Batch API calls when possible

**Frontend:**
- Lazy load components
- Debounce user input
- Optimize re-renders with React.memo
- Use virtual scrolling for long lists

## Documentation

### Updating Docs

**When to update:**
- Adding new features
- Changing APIs or interfaces
- Fixing bugs that affect usage
- Improving explanations

**Where to update:**
- [`README.md`](../README.md): Overview and quick start
- [`docs/`](../docs/): Detailed guides
- Code comments: Complex logic
- Docstrings: All public functions

### Writing Good Docs

**Principles:**
- Clear and concise
- Include examples
- Explain the "why", not just the "what"
- Keep up-to-date with code

**Example:**
```markdown
## Feature Name

Brief description of what the feature does.

### Usage

```python
from src.module import function

result = function(param1, param2)
``‌`

### Parameters

- `param1` (str): Description of first parameter
- `param2` (int, optional): Description of second parameter. Default: 10

### Returns

- `Result`: Description of return value

### Example

```python
# Complete working example
result = function("test", max_results=5)
print(result)
``‌`
```

## Community

### Getting Help

- **Documentation**: Start here
- **GitHub Discussions**: Ask questions
- **GitHub Issues**: Report bugs
- **Code Review**: Learn from PR feedback

### Sharing Knowledge

- Answer questions in Discussions
- Review others' PRs
- Write blog posts about VeritasLoop
- Present at meetups/conferences

## Related Documentation

- [Installation Guide](INSTALLATION.md) - Setup instructions
- [Usage Guide](USAGE.md) - How to use VeritasLoop
- [Architecture Overview](ARCHITECTURE.md) - System design
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
