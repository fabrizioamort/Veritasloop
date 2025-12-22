# VeritasLoop Production Readiness Improvements Plan

## Executive Summary

**Timeline**: 1-2 months
**Release Type**: Free public service (no authentication required)
**Deployment**: Platform-agnostic configuration
**Approach**: Balanced focus on security, stability, and polish

### Current Status
✅ **Strengths**: Well-architected multi-agent system, clean code organization, comprehensive documentation
⚠️ **Critical Issues**: Exposed API keys, unrestricted CORS, missing input validation
📋 **Improvements Needed**: 23 items across security, stability, and polish

### What This Plan Covers
1. **Security** (6 critical fixes): API key rotation, CORS configuration, input validation, error sanitization
2. **Stability** (7 improvements): HTTP timeouts, LLM error handling, reconnection logic, cache limits
3. **Polish** (10 enhancements): Accessibility, loading states, proper logging, keyboard navigation

### Quick Win Priorities
🔴 **Do First** (Week 1): Rotate API keys, fix CORS, add input validation
🟡 **Do Next** (Week 2-4): Error handling, timeouts, reconnection logic
🟢 **Do Last** (Week 5-8): Accessibility, testing, documentation

## Overview
This plan addresses security, stability, professionalism, and polish improvements needed before public release. The codebase is well-architected but has critical security issues and missing production configurations that must be resolved.

**Key Finding**: The application has excellent architecture but needs hardening for production use. No major refactoring required—only targeted improvements to existing code.

## Phase 1: CRITICAL Security Fixes (Must Do Before Any Public Release)

### 1.1 API Key Security (URGENT - Do First)
**Problem**: Exposed API keys in .env file that may be committed to git
**Files**: `.env`, `.gitignore`

**Actions**:
1. Verify `.env` is in `.gitignore` (already should be, but confirm)
2. Immediately rotate ALL API keys:
   - OpenAI API key
   - Brave Search API key
   - News API key
   - Reddit client ID/secret
3. Remove `.env` from git history if committed (use `git filter-branch` or BFG)
4. Create comprehensive `.env.example` with placeholder values
5. Update documentation to emphasize never committing `.env`

### 1.2 CORS Configuration
**Problem**: `allow_origins=["*"]` allows any website to access the API
**Files**: `api/main.py` (lines 73-77)

**Changes**:
```python
# Replace existing CORS config with environment-based configuration
import os

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # From environment variable
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Explicit methods only
    allow_headers=["Content-Type"],  # Explicit headers only
    max_age=3600,
)
```

Add to `.env.example`:
```
ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com
```

### 1.3 Input Validation - WebSocket
**Problem**: No validation of WebSocket message inputs
**Files**: `api/main.py` (lines 86-99)

**Changes**:
1. Create Pydantic model for request validation:
```python
from pydantic import BaseModel, Field, validator

class VerificationRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=10000)
    type: str = Field(default="Text", regex="^(Text|URL)$")
    max_iterations: int = Field(default=3, ge=1, le=10)
    max_searches: int = Field(default=-1, ge=-1, le=100)
    language: str = Field(default="Italian", regex="^(Italian|English)$")
    proPersonality: str = Field(default="ASSERTIVE", regex="^(PASSIVE|ASSERTIVE|AGGRESSIVE)$")
    contraPersonality: str = Field(default="ASSERTIVE", regex="^(PASSIVE|ASSERTIVE|AGGRESSIVE)$")
```

2. Use in WebSocket handler:
```python
try:
    request_data = VerificationRequest(**json.loads(data))
except ValidationError as e:
    await websocket.send_json({
        "type": "error",
        "message": "Invalid request parameters"
    })
    logger.warning(f"Invalid request: {e}")
    return
```

### 1.4 URL Validation
**Problem**: User-submitted URLs not validated before fetching
**Files**: `src/utils/claim_extractor.py` (lines 88-102), `api/main.py` (lines 99-107)

**Changes**:
1. Add URL validation function in `claim_extractor.py`:
```python
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    """Validate URL is well-formed and uses safe protocols."""
    try:
        result = urlparse(url)
        # Only allow http/https, must have domain
        return all([
            result.scheme in ('http', 'https'),
            result.netloc,
            len(url) < 2048  # Prevent extremely long URLs
        ])
    except:
        return False
```

2. Use in `extract_from_url()`:
```python
def extract_from_url(url: str) -> Claim:
    if not validate_url(url):
        raise ValueError("Invalid URL format or protocol")

    try:
        article = Article(url)
        article.download()
        # ... rest of extraction
```

### 1.5 Error Message Sanitization
**Problem**: Raw exception messages leak internal details to users
**Files**: `api/main.py` (lines 116-124, 202), `src/cli.py`, `frontend/src/App.jsx`

**Changes**:
1. Create safe error message function in `api/main.py`:
```python
def sanitize_error_message(error: Exception, default: str = "An error occurred") -> str:
    """Return user-safe error message."""
    # Log detailed error
    logger.error(f"Detailed error: {error}", exc_info=True)

    # Return generic message to user
    safe_messages = {
        ValueError: "Invalid input provided",
        TimeoutError: "Request timed out, please try again",
        ConnectionError: "Unable to connect to external service",
    }

    return safe_messages.get(type(error), default)
```

2. Replace all error sends:
```python
# Instead of:
await websocket.send_json({
    "type": "error",
    "message": f"Failed to extract content: {str(e)}"
})

# Use:
await websocket.send_json({
    "type": "error",
    "message": sanitize_error_message(e, "Failed to process URL")
})
```

## Phase 2: Configuration Management

### 2.1 Backend Environment Configuration
**Problem**: Hardcoded values prevent production deployment
**Files**: Multiple files with hardcoded `localhost:6006`, `localhost:8000`

**Changes**:
1. Create `src/config/settings.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Phoenix Settings
    phoenix_enabled: bool = True
    phoenix_port: int = 6006
    phoenix_host: str = "localhost"

    # CORS
    allowed_origins: str = "http://localhost:5173"

    # Environment
    environment: str = "development"  # development, staging, production

    class Config:
        env_file = ".env"

settings = Settings()
```

2. Update `api/main.py` to use settings:
```python
from src.config.settings import settings

# Phoenix initialization
if settings.phoenix_enabled:
    phoenix_url = f"http://{settings.phoenix_host}:{settings.phoenix_port}"
    # ... phoenix setup with phoenix_url

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    # ...
)
```

3. Update `.env.example`:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Phoenix Observability
PHOENIX_ENABLED=true
PHOENIX_HOST=localhost
PHOENIX_PORT=6006

# CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost:5173

# Environment
ENVIRONMENT=development
```

### 2.2 Frontend Environment Configuration
**Problem**: Hardcoded API URL in React app
**Files**: `frontend/src/App.jsx` (line 10)

**Changes**:
1. Create `frontend/.env.example`:
```bash
VITE_API_URL=ws://localhost:8000/ws/verify
VITE_ENVIRONMENT=development
```

2. Update `App.jsx`:
```javascript
// Replace hardcoded URL
const API_URL = import.meta.env.VITE_API_URL || 'ws://localhost:8000/ws/verify';
```

3. Create `frontend/.env.development`:
```bash
VITE_API_URL=ws://localhost:8000/ws/verify
VITE_ENVIRONMENT=development
```

4. Create `frontend/.env.production`:
```bash
VITE_API_URL=wss://your-domain.com/ws/verify
VITE_ENVIRONMENT=production
```

### 2.3 Environment Variable Validation
**Files**: `api/main.py`, new file `src/config/env_validator.py`

**Changes**:
1. Create `src/config/env_validator.py`:
```python
import os
import sys
from typing import List

def validate_required_env_vars() -> None:
    """Validate required environment variables on startup."""
    required = [
        'OPENAI_API_KEY',
        'BRAVE_SEARCH_API_KEY',
    ]

    optional = [
        'NEWS_API_KEY',
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
    ]

    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please check your .env file and ensure all required keys are set.")
        sys.exit(1)

    missing_optional = [var for var in optional if not os.getenv(var)]
    if missing_optional:
        print(f"WARNING: Missing optional environment variables: {', '.join(missing_optional)}")
        print("Some features may not work correctly.")
```

2. Call in `api/main.py` startup:
```python
from src.config.env_validator import validate_required_env_vars

@app.on_event("startup")
async def startup_event():
    validate_required_env_vars()
    # ... rest of startup
```

## Phase 3: Error Handling & Stability

### 3.1 HTTP Request Timeouts
**Problem**: No timeouts on external API calls
**Files**: `src/tools/search_tools.py`, `src/tools/content_tools.py`, `src/tools/news_api.py`

**Changes**:
1. Add timeout constant in `src/config/settings.py`:
```python
class Settings(BaseSettings):
    # ... existing settings
    request_timeout: int = 10  # seconds
```

2. Update all `requests.get()` calls:
```python
from src.config.settings import settings

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=settings.request_timeout,
    allow_redirects=False  # Security: prevent redirect attacks
)
```

**Files to update**:
- `src/tools/search_tools.py`: Lines 38, 70, 102, 134
- `src/tools/content_tools.py`: Line 37
- `src/tools/news_api.py`: API calls

### 3.2 LLM Error Handling in Agents
**Problem**: No try-catch around LLM calls in PRO/CONTRA agents
**Files**: `src/agents/pro_agent.py`, `src/agents/contra_agent.py`

**Changes**:
1. Wrap LLM calls in try-catch with fallback:
```python
# In pro_agent.py, initial_research() method
try:
    response = self.llm.invoke([
        SystemMessage(content=self.system_prompt),
        HumanMessage(content=prompt)
    ])
    content = response.content
except Exception as e:
    self.logger.error(f"LLM call failed in PRO agent: {e}")
    content = "Unable to generate argument due to technical difficulties."
    confidence = 0

# Similarly in contra_agent.py
```

2. Return degraded DebateMessage on failure:
```python
return DebateMessage(
    round=0,
    agent=AgentType.PRO,
    message_type=MessageType.ARGUMENT,
    content=content,  # Will be fallback message on error
    sources=sources,
    confidence=confidence  # Will be 0 on error
)
```

### 3.3 Frontend Error Boundary
**Problem**: No React Error Boundary for error isolation
**Files**: New file `frontend/src/components/ErrorBoundary.jsx`, `frontend/src/App.jsx`

**Changes**:
1. Create `ErrorBoundary.jsx`:
```javascript
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
          <div className="bg-red-500/10 backdrop-blur-xl border border-red-500/20 rounded-2xl p-8 max-w-md">
            <h2 className="text-2xl font-bold text-red-400 mb-4">Something went wrong</h2>
            <p className="text-gray-300 mb-4">The application encountered an error. Please refresh the page to try again.</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg text-white"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

2. Wrap App in `main.jsx`:
```javascript
import ErrorBoundary from './components/ErrorBoundary';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
```

### 3.4 WebSocket Reconnection Logic
**Problem**: No automatic reconnection on connection failure
**Files**: `frontend/src/App.jsx`

**Changes**:
```javascript
const MAX_RETRIES = 3;
const RETRY_DELAY = 3000; // 3 seconds

const startVerification = () => {
  let retryCount = 0;

  const connectWebSocket = () => {
    const socket = new WebSocket(API_URL);

    socket.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setStatusText('CONNECTION ERROR');

      // Retry logic
      if (retryCount < MAX_RETRIES) {
        retryCount++;
        setStatusText(`Reconnecting... (${retryCount}/${MAX_RETRIES})`);
        setTimeout(connectWebSocket, RETRY_DELAY);
      } else {
        setStatusText('CONNECTION FAILED');
        setIsProcessing(false);
      }
    };

    // ... rest of socket setup
  };

  connectWebSocket();
};
```

### 3.5 Cache Size Limits
**Problem**: Unbounded cache growth in ToolManager
**Files**: `src/utils/tool_manager.py`

**Changes**:
```python
from collections import OrderedDict

class ToolManager:
    MAX_CACHE_SIZE = 1000  # Maximum cache entries

    def __init__(self, ttl: int = 3600):
        # Use OrderedDict for LRU behavior
        self.url_cache: OrderedDict = OrderedDict()
        self.search_cache: OrderedDict = OrderedDict()
        self.ttl = ttl

    def _add_to_cache(self, cache: OrderedDict, key: str, value: Any):
        """Add to cache with size limit."""
        # Check size limit
        if len(cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (FIFO)
            cache.popitem(last=False)

        cache[key] = {
            'data': value,
            'timestamp': time.time()
        }
```

## Phase 4: Code Quality & Polish

### 4.1 Remove Console Statements
**Problem**: console.log/error in production code
**Files**: `frontend/src/App.jsx` (lines 55, 74, 80)

**Changes**:
1. Replace with proper logging or remove:
```javascript
// Option 1: Remove entirely
// console.log('Connected');

// Option 2: Use environment-conditional logging
const isDevelopment = import.meta.env.VITE_ENVIRONMENT === 'development';
if (isDevelopment) {
  console.log('WebSocket connected');
}

// Option 3: Use proper logging service (recommended for production)
// import { logger } from './utils/logger';
// logger.info('WebSocket connected');
```

### 4.2 Replace print() with Logger
**Problem**: Inconsistent logging (print vs logger)
**Files**: `src/tools/search_tools.py`

**Changes**:
```python
# At top of file
import logging
logger = logging.getLogger(__name__)

# Replace all print() calls
# Before:
print("Warning: BRAVE_SEARCH_API_KEY not found...")

# After:
logger.warning("BRAVE_SEARCH_API_KEY not found. Skipping Brave search.")
```

### 4.3 Add Accessibility (ARIA)
**Problem**: No accessibility attributes
**Files**: `frontend/src/components/*.jsx`

**Changes for ConfigPanel.jsx**:
```javascript
<div className="config-panel" role="region" aria-label="Configuration Panel">
  <h3 id="personality-heading">Agent Personalities</h3>

  <div role="group" aria-labelledby="personality-heading">
    <label htmlFor="pro-personality">PRO Agent:</label>
    <select
      id="pro-personality"
      value={proPersonality}
      onChange={(e) => setProPersonality(e.target.value)}
      aria-label="Select PRO agent personality"
    >
      <option value="PASSIVE">😌 Oliver (Passive)</option>
      {/* ... */}
    </select>
  </div>
</div>
```

**Changes for VerdictReveal.jsx**:
```javascript
<div
  className="verdict-modal-overlay"
  role="dialog"
  aria-modal="true"
  aria-labelledby="verdict-title"
>
  <div className="verdict-content" tabIndex={-1}>
    <h2 id="verdict-title">Final Verdict</h2>
    {/* ... */}
    <button
      onClick={onClose}
      aria-label="Close verdict modal"
    >
      Close
    </button>
  </div>
</div>
```

**Changes for DebateStream.jsx**:
```javascript
<div
  className="debate-stream"
  role="log"
  aria-live="polite"
  aria-label="Debate messages"
>
  {messages.map((msg, idx) => (
    <div key={idx} role="article" aria-label={`Message from ${msg.agent}`}>
      {/* ... */}
    </div>
  ))}
</div>
```

### 4.4 Update Frontend README
**Problem**: Generic Vite template README
**Files**: `frontend/README.md`

**Changes**:
Create project-specific README:
```markdown
# VeritasLoop Frontend

React-based web interface for the VeritasLoop news verification system.

## Tech Stack
- React 19.2.0
- Vite 7.2.4
- Tailwind CSS 4.1.17
- Framer Motion 12.23.25
- WebSocket for real-time communication

## Development

```bash
npm install
npm run dev  # Start dev server at http://localhost:5173
```

## Build

```bash
npm run build  # Output to dist/
npm run preview  # Preview production build
```

## Configuration

Copy `.env.example` to `.env` and configure:
- `VITE_API_URL`: WebSocket endpoint (default: ws://localhost:8000/ws/verify)

## Components
- `App.jsx`: Main application state and WebSocket management
- `ConfigPanel.jsx`: Personality and parameter configuration
- `AgentNode.jsx`: Visual agent representation
- `DebateStream.jsx`: Real-time message display
- `VerdictReveal.jsx`: Final verdict modal
- `ProgressTracker.jsx`: Debate progress visualization
```

## Phase 5: Additional Improvements

### 5.1 Loading States & Timeouts
**Files**: `frontend/src/App.jsx`

**Changes**:
1. Add timeout for verification:
```javascript
useEffect(() => {
  let timeoutId;

  if (isProcessing) {
    // Set 5-minute timeout
    timeoutId = setTimeout(() => {
      setStatusText('Verification timed out');
      setIsProcessing(false);
      if (ws) ws.close();
    }, 5 * 60 * 1000);
  }

  return () => clearTimeout(timeoutId);
}, [isProcessing, ws]);
```

2. Add skeleton loading states for agent nodes:
```javascript
{isProcessing && !agentStatus.pro && (
  <div className="skeleton-pulse">Loading PRO agent...</div>
)}
```

### 5.2 WebSocket Authentication (Optional)
**Files**: `api/main.py`, `frontend/src/App.jsx`

**Changes** (if authentication is needed):
1. Backend:
```python
@app.websocket("/ws/verify")
async def websocket_endpoint(websocket: WebSocket):
    # Check for token in query params or headers
    token = websocket.query_params.get("token")

    if not verify_token(token):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()
```

2. Frontend:
```javascript
const token = getAuthToken(); // From auth context
const socket = new WebSocket(`${API_URL}?token=${token}`);
```

### 5.3 Rate Limiting (Optional for production)
**Files**: New file `api/middleware.py`, `api/main.py`

**Implementation**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.websocket("/ws/verify")
@limiter.limit("10/minute")  # 10 verifications per minute per IP
async def websocket_endpoint(websocket: WebSocket):
    # ...
```

## Critical Files to Modify

### Security & Configuration (Phase 1-2):
1. `.env` - Rotate all keys
2. `.gitignore` - Verify .env is ignored
3. `api/main.py` - CORS, validation, error handling
4. `src/utils/claim_extractor.py` - URL validation
5. `src/config/settings.py` - New file for centralized config
6. `src/config/env_validator.py` - New file for env validation
7. `frontend/.env.example` - New file
8. `frontend/src/App.jsx` - Environment-based API URL

### Error Handling (Phase 3):
9. `src/agents/pro_agent.py` - LLM error handling
10. `src/agents/contra_agent.py` - LLM error handling
11. `src/tools/search_tools.py` - Timeouts, logging
12. `src/utils/tool_manager.py` - Cache limits
13. `frontend/src/components/ErrorBoundary.jsx` - New file
14. `frontend/src/main.jsx` - Wrap with ErrorBoundary

### Code Quality (Phase 4):
15. `frontend/src/App.jsx` - Remove console.log, reconnection
16. `frontend/src/components/ConfigPanel.jsx` - ARIA labels
17. `frontend/src/components/VerdictReveal.jsx` - ARIA modal
18. `frontend/src/components/DebateStream.jsx` - ARIA live region
19. `frontend/README.md` - Update with project info

## Testing Strategy

After implementing changes:
1. Test with invalid inputs (empty strings, extremely long inputs, invalid URLs)
2. Test with missing API keys (graceful degradation)
3. Test WebSocket disconnection/reconnection
4. Test CORS with different origins
5. Test timeout scenarios
6. Run accessibility audit with axe DevTools
7. Test mobile responsive design
8. Load test with multiple simultaneous requests

## Deployment Checklist

Before production deployment:
- [ ] All API keys rotated and secured
- [ ] CORS configured with production domain
- [ ] Environment variables set in hosting platform
- [ ] Error messages sanitized
- [ ] Input validation implemented
- [ ] Timeouts configured
- [ ] Frontend built with production config
- [ ] Accessibility tested
- [ ] Mobile responsiveness verified
- [ ] Performance tested under load
- [ ] Logging configured for production
- [ ] Monitoring/alerting set up

## Priority Order (1-2 Month Timeline, Free Public Service)

**Week 1-2: CRITICAL Security & Configuration**
1. ✅ Rotate API keys (.env security) - IMMEDIATE
2. ✅ Fix CORS configuration
3. ✅ Add input validation (WebSocket + URL)
4. ✅ Sanitize error messages
5. ✅ Environment-based configuration (backend + frontend)
6. ✅ Environment variable validation on startup

**Week 3-4: Stability & Error Handling**
7. ✅ Add HTTP timeouts to all external API calls
8. ✅ LLM error handling in PRO/CONTRA agents
9. ✅ Frontend Error Boundary
10. ✅ WebSocket reconnection logic
11. ✅ Cache size limits in ToolManager
12. ✅ Replace print() with proper logger
13. ✅ Remove console.log statements from frontend

**Week 5-6: Professional Polish**
14. ✅ Add accessibility (ARIA labels, semantic HTML)
15. ✅ Loading states and verification timeout
16. ✅ Update frontend README.md
17. ✅ Focus trap for VerdictReveal modal
18. ✅ Keyboard navigation support

**Week 7-8: Testing & Documentation**
19. ✅ Manual testing with edge cases
20. ✅ Accessibility audit with axe DevTools
21. ✅ Mobile responsive testing
22. ✅ Update deployment documentation
23. ✅ Create deployment checklist

**SKIPPED (Not needed for free public service):**
- ❌ Authentication/Authorization (no user accounts)
- ❌ Rate limiting (can add later if abused)
- ❌ Usage analytics (privacy-first approach)
- ❌ Payment integration
