# VeritasLoop Production Readiness - Task List

## Overview
This task list is derived from the **VeritasLoop Production Readiness Improvements Plan**. It breaks down the plan into actionable tasks to prepare the application for a free public release.

---

## 🔴 Phase 1: CRITICAL Security Fixes (Week 1-2)

### Task 1.1: API Key Security Audit & Rotation
**Priority**: Urgent | **Est. Time**: 3 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] Verify `.env` is present in `.gitignore`.
- [x] Create a comprehensive `.env.example` file with placeholder values for all required and optional keys.
- [x] Update `docs/INSTALLATION.md` and `README.md` to emphasize that the `.env` file should never be committed to version control.
- [ ] **MANUAL ACTION REQUIRED**: Immediately rotate all API keys (OpenAI, Brave, News API, Reddit). This cannot be done automatically.
- [ ] **MANUAL ACTION REQUIRED**: Scan git history for any accidentally committed keys using a tool like BFG or `git filter-branch`. This is a destructive operation and should be done with care.

**Files Affected**: `.env`, `.gitignore`, `.env.example`, `docs/INSTALLATION.md`, `README.md`

---

### Task 1.2: Implement Secure CORS Policy
**Priority**: Urgent | **Est. Time**: 2 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] Modify `api/main.py` to replace the wildcard `allow_origins=["*"]` with an environment-based configuration.
- [x] Use `os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")` to read allowed origins.
- [x] Restrict `allow_methods` to `["GET", "POST"]`.
- [x] Restrict `allow_headers` to `["Content-Type"]`.
- [x] Add `ALLOWED_ORIGINS` to the `.env.example` file with a clear comment explaining its purpose.

**Files Affected**: `api/main.py`, `.env.example`

---

### Task 1.3: Add WebSocket Input Validation
**Priority**: Urgent | **Est. Time**: 3 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] In `api/main.py`, create a Pydantic `VerificationRequest` model to validate incoming WebSocket message data.
- [x] The model includes fields with constraints: `input` (str, length), `type` (regex), `max_iterations` (int, range), `language` (regex), etc.
- [x] In the `/ws/verify` endpoint, wrap the data parsing in a `try...except ValidationError` block.
- [x] On validation failure, send a JSON error message to the client and log the warning server-side.

**Files Affected**: `api/main.py`

---

### Task 1.4: Implement URL Validation
**Priority**: High | **Est. Time**: 2 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] In `src/utils/claim_extractor.py`, create a `validate_url(url: str) -> bool` function.
- [x] The function uses `urllib.parse.urlparse` to check for a valid scheme (`http`, `https` only) and network location (`netloc`).
- [x] It also enforces a reasonable length limit (`< 2048` characters).
- [x] Integrate `validate_url()` at the beginning of `extract_from_url()`, raising a `ValueError` for invalid URLs.
- [x] Ensure the error is caught and handled gracefully in the API layer.

**Files Affected**: `src/utils/claim_extractor.py`, `api/main.py`

---

### Task 1.5: Sanitize Error Messages
**Priority**: High | **Est. Time**: 3 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] Create a `sanitize_error_message` helper function in `api/server_utils.py`.
- [x] This function logs the full, detailed exception for debugging purposes.
- [x] It returns a generic, user-safe error message to the client based on the exception type (e.g., `ValueError` -> "Invalid input").
- [x] Refactor all `except` blocks in `api/main.py` to use this sanitization function before sending error responses.
- [x] Ensure no internal stack traces or implementation details are leaked to the frontend.

**Files Affected**: `api/main.py`, `src/cli.py`, `frontend/src/App.jsx`, `api/server_utils.py`

---

## 🟡 Phase 2: Configuration Management (Week 2-3)

### Task 2.1: Centralized Backend Configuration
**Priority**: High | **Est. Time**: 4 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] Create a new file `src/config/settings.py` using `pydantic-settings`.
- [x] Define a `Settings` class that inherits from `BaseSettings` to manage all environment variables (API hosts, ports, Phoenix config, CORS origins, etc.).
- [x] Configure it to load variables from a `.env` file.
- [x] Refactor `api/main.py` and any other relevant files to import and use the `settings` object instead of hardcoded values or direct `os.getenv` calls.
- [x] Update `.env.example` with all new configuration variables.

**Files Affected**: `src/config/settings.py` (new), `api/main.py`, `.env.example`, `requirements.txt`

---

### Task 2.2: Frontend Environment Configuration
**Priority**: High | **Est. Time**: 2 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] In `frontend/src/App.jsx`, replace the hardcoded `API_URL` with `import.meta.env.VITE_API_URL`.
- [x] Provide a fallback for local development (e.g., `|| 'ws://localhost:8000/ws/verify'`).
- [x] Create `frontend/.env.example` with `VITE_API_URL` and `VITE_ENVIRONMENT`.
- [x] Create `frontend/.env.development` and `frontend/.env.production` with appropriate values for the API URL.
- [x] Add `frontend/.env*` files to the main `.gitignore` (excluding `.env.example`).

**Files Affected**: `frontend/src/App.jsx`, `frontend/.env.example` (new), `frontend/.env.development` (new), `frontend/.env.production` (new), `.gitignore`

---

### Task 2.3: Environment Variable Validation on Startup
**Priority**: Medium | **Est. Time**: 2 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] Create a new file `src/config/env_validator.py`.
- [x] Implement a function `validate_required_env_vars()` that checks for the presence of critical keys (`OPENAI_API_KEY`, `BRAVE_SEARCH_API_KEY`).
- [x] If a required key is missing, print an error and exit the application (`sys.exit(1)`).
- [x] The function should also check for optional keys (`NEWS_API_KEY`, etc.) and print a warning if they are missing.
- [x] In `api/main.py`, create a startup event handler (`@app.on_event("startup")`) and call the validation function.

**Files Affected**: `src/config/env_validator.py` (new), `api/main.py`

---

## 🟡 Phase 3: Error Handling & Stability (Week 3-4)

### Task 3.1: Add HTTP Request Timeouts
**Priority**: High | **Est. Time**: 2 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] Add a `REQUEST_TIMEOUT` variable to the `src/config/settings.py` file (e.g., 10 seconds).
- [x] Update all `requests.get()` and `requests.post()` calls in the toolset (`src/tools/*.py`) to include `timeout=settings.request_timeout`.
- [x] As a security best practice, also add `allow_redirects=False` to these requests to prevent redirect attacks.
- [x] Ensure that `requests.exceptions.Timeout` is handled gracefully.

**Files Affected**: `src/config/settings.py`, `src/tools/search_tools.py`, `src/tools/content_tools.py`

---

### Task 3.2: Implement LLM Error Handling
**Priority**: High | **Est. Time**: 2 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] In `src/agents/pro_agent.py` and `src/agents/contra_agent.py`, wrap all `self.llm.invoke()` calls in a `try...except` block.
- [x] On exception, log the error and create a fallback `DebateMessage` with a user-friendly error content (e.g., "Unable to generate argument...") and set `confidence` to 0.
- [x] Ensure the agent's failure does not crash the entire verification process.

**Files Affected**: `src/agents/pro_agent.py`, `src/agents/contra_agent.py`

---

### Task 3.3: Add Frontend Error Boundary
**Priority**: Medium | **Est. Time**: 2 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] Create a new React component `frontend/src/components/ErrorBoundary.jsx`.
- [x] Implement a class component with `getDerivedStateFromError` and `componentDidCatch` to handle rendering errors.
- [x] The error boundary should render a fallback UI with a "Something went wrong" message and a button to reload the page.
- [x] In `frontend/src/main.jsx`, wrap the main `<App />` component with `<ErrorBoundary>`.

**Files Affected**: `frontend/src/components/ErrorBoundary.jsx` (new), `frontend/src/main.jsx`

---

### Task 3.4: Implement WebSocket Reconnection Logic
**Priority**: Medium | **Est. Time**: 3 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] In `frontend/src/App.jsx`, modify the `startVerification` function to include reconnection logic.
- [x] Create a `connectWebSocket` function that can be called recursively on failure.
- [x] Use a retry counter (`retryCount`) and a maximum number of retries (`MAX_RETRIES`).
- [x] On `socket.onerror`, increment the counter and use `setTimeout` to attempt reconnection after a delay (`RETRY_DELAY`).
- [x] Update the UI to inform the user about the reconnection attempt (e.g., "Reconnecting... (1/3)").
- [x] If all retries fail, show a permanent "Connection Failed" message.

**Files Affected**: `frontend/src/App.jsx`

---

### Task 3.5: Implement Cache Size Limits
**Priority**: Medium | **Est. Time**: 2 hours | **Status**: ✅ COMPLETED

**Implementation**:
- [x] In `src/utils/tool_manager.py`, change the cache dictionaries (`url_cache`, `search_cache`) to `collections.OrderedDict`.
- [x] Define a `MAX_CACHE_SIZE` constant (e.g., 1000).
- [x] Before adding a new item to a cache, check if the cache size has reached the limit.
- [x] If the limit is reached, use `cache.popitem(last=False)` to remove the oldest item (LRU behavior).

**Files Affected**: `src/utils/tool_manager.py`

---

## 🟢 Phase 4: Code Quality & Polish (Week 5-6)

### Task 4.1: Remove Production Console Statements
**Priority**: Low | **Est. Time**: 1 hour

**Implementation**:
- [ ] Scan `frontend/**/*.jsx` files for `console.log`, `console.warn`, and `console.error`.
- [ ] Remove them or wrap them in a development-only check: `if (import.meta.env.VITE_ENVIRONMENT === 'development') { ... }`.
- [ ] Consider integrating a proper logging service for production monitoring if needed.

**Files Affected**: `frontend/src/App.jsx`, potentially other components.

---

### Task 4.2: Replace `print()` with Structured Logging
**Priority**: Medium | **Est. Time**: 2 hours

**Implementation**:
- [ ] In backend Python files, replace all `print()` statements with the appropriate `logger` calls (`logger.info`, `logger.warning`, `logger.debug`).
- [ ] Ensure a logger instance is created at the top of each module: `logger = logging.getLogger(__name__)`.
- [ ] This ensures consistent, structured logging that can be configured centrally.

**Files Affected**: `src/tools/search_tools.py`, and any other files using `print()`.

---

### Task 4.3: Add Accessibility (ARIA) Attributes
**Priority**: Medium | **Est. Time**: 4 hours

**Implementation**:
- [ ] Audit the React components in `frontend/src/components/` for accessibility issues.
- [ ] Add ARIA roles and attributes (e.g., `role="region"`, `aria-label`, `aria-live="polite"`, `role="dialog"`, `aria-modal="true"`).
- [ ] Ensure all interactive elements are keyboard-accessible and have clear focus states.
- [ ] Use `htmlFor` on labels to link them to form inputs.
- [ ] Run an accessibility audit using browser developer tools (e.g., Lighthouse, axe DevTools).

**Files Affected**: `frontend/src/components/ConfigPanel.jsx`, `frontend/src/components/VerdictReveal.jsx`, `frontend/src/components/DebateStream.jsx`

---

### Task 4.4: Update Frontend README
**Priority**: Low | **Est. Time**: 1 hour

**Implementation**:
- [ ] Replace the generic Vite README in `frontend/README.md` with project-specific information.
- [ ] Include sections on Tech Stack, Development instructions (`npm run dev`), Build process (`npm run build`), and Configuration (`.env` file usage).
- [ ] Briefly describe the purpose of each major component.

**Files Affected**: `frontend/README.md`

---

## 🟢 Phase 5: Additional Improvements (Week 5-8)

### Task 5.1: Implement Loading States & Timeouts
**Priority**: Medium | **Est. Time**: 2 hours

**Implementation**:
- [ ] In `frontend/src/App.jsx`, add a `useEffect` hook that sets a timeout (e.g., 5 minutes) when `isProcessing` becomes true. If the timeout is reached, update the status and close the WebSocket.
- [ ] Create and implement simple CSS-based skeleton loading components to show while waiting for the first messages from the agents.

**Files Affected**: `frontend/src/App.jsx`

---

### Task 5.2: WebSocket Authentication (Optional)
**Priority**: Low | **Est. Time**: 3 hours

**Implementation**:
- [ ] *This is optional and only needed if user accounts are introduced.*
- [ ] If implemented, modify the WebSocket endpoint in `api/main.py` to expect a token in the query parameters.
- [ ] Add a `verify_token` function and close the connection with code 1008 if the token is invalid.
- [ ] On the frontend, append the token to the WebSocket URL when connecting.

**Files Affected**: `api/main.py`, `frontend/src/App.jsx`

---

### Task 5.3: Implement Rate Limiting (Optional)
**Priority**: Low | **Est. Time**: 3 hours

**Implementation**:
- [ ] *This is optional but recommended for a public service to prevent abuse.*
- [ ] Add `slowapi` to `requirements.txt`.
- [ ] In `api/main.py`, create a `Limiter` instance using `get_remote_address` as the key function.
- [ ] Apply the limiter to the WebSocket endpoint using the `@limiter.limit("10/minute")` decorator.
- [ ] Add the `RateLimitExceeded` exception handler to the FastAPI app.

**Files Affected**: `api/main.py`, `requirements.txt`