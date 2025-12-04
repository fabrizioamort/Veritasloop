# VeritasLoop - Implementation Task List

## Overview
This task list is designed to deliver an MVP of the VeritasLoop system. Tasks are ordered by dependency and priority.

---

## 🏗️ Phase 0: Project Setup (Day 1)

### Task 0.1: Environment & Dependencies
**Priority**: Critical | **Est. Time**: 2 hours

- [ ] Create project repository with Git
- [ ] Initialize Python virtual environment (3.11+)
- [ ] Create `requirements.txt` with core dependencies:
  ```
  langchain>=0.1.0
  langgraph>=0.0.30
  anthropic>=0.18.0
  beautifulsoup4>=4.12.0
  newspaper3k>=0.2.8
  python-dotenv>=1.0.0
  requests>=2.31.0
  pydantic>=2.0.0
  redis>=5.0.0 (optional)
  ```
- [ ] Create `.env.example` with required API keys:
  ```
  OPENAI_API_KEY=
  GEMINI_API_KEY=
  BRAVE_SEARCH_API_KEY=
  NEWS_API_KEY=
  REDDIT_CLIENT_ID=
  REDDIT_CLIENT_SECRET=
  ```
- [ ] Set up `.gitignore` (Python, API keys, cache files)
- [ ] Create project structure:
   - [x] Create project repository with Git
   - [x] Initialize Python virtual environment (3.11+)
   - [x] Create `requirements.txt` with core dependencies:
    ```
    langchain>=0.1.0
    langgraph>=0.0.30
    anthropic>=0.18.0
    beautifulsoup4>=4.12.0
    newspaper3k>=0.2.8
    python-dotenv>=1.0.0
    requests>=2.31.0
    pydantic>=2.0.0
    redis>=5.0.0 (optional)
    ```
   - [x] Create `.env.example` with required API keys:
    ```
    OPENAI_API_KEY=
    GEMINI_API_KEY=
    BRAVE_SEARCH_API_KEY=
    NEWS_API_KEY=
    REDDIT_CLIENT_ID=
    REDDIT_CLIENT_SECRET=
    ```
   - [x] Set up `.gitignore` (Python, API keys, cache files)
   - [x] Create project structure:
    ```
    veritasloop/
    ├── src/
    │   ├── agents/
    │   ├── tools/
    │   ├── orchestrator/
    │   ├── models/
    │   └── utils/
    ├── tests/
    ├── data/
    │   └── sample_claims/
    ├── logs/
    └── notebooks/ (for experiments)
    ```
  ```
  veritasloop/
  ├── src/
  │   ├── agents/
  │   ├── tools/
  │   ├── orchestrator/
  │   ├── models/
  │   └── utils/
  ├── tests/
  ├── data/
  │   └── sample_claims/
  ├── logs/
  └── notebooks/ (for experiments)
  ```

**Deliverable**: Runnable Python environment with structure

---

## 📊 Phase 1: Data Models & Core Infrastructure

### Task 1.1: Define Pydantic Models
**Priority**: Critical | **Est. Time**: 3 hours

**File**: `src/models/schemas.py`

- [ ] Create `Claim` model:
  - `id`, `raw_input`, `core_claim`, `entities`, `category`
- [ ] Create `Source` model:
  - `url`, `title`, `snippet`, `reliability`, `timestamp`, `agent`
- [ ] Create `DebateMessage` model:
  - `round`, `agent`, `message_type`, `content`, `sources`, `confidence`
- [ ] Create `Verdict` model (full JSON schema from planning)
- [ ] Create `GraphState` model for LangGraph:
  - `claim`, `messages`, `pro_sources`, `contra_sources`, `round_count`
- [ ] Add validation methods (e.g., URL validation, date parsing)
- [ ] Write unit tests for each model

**Deliverable**: `schemas.py` with typed models

---

### Task 1.2: Claim Extraction Module
**Priority**: Critical | **Est. Time**: 4 hours

**File**: `src/utils/claim_extractor.py`

- [ ] Create `extract_from_text(text: str) -> Claim`:
  - Use LLM to identify core verifiable statement
  - Extract entities (people, places, dates, orgs)
  - Categorize claim type
- [ ] Create `extract_from_url(url: str) -> Claim`:
  - Fetch article with `newspaper3k`
  - Extract headline and body
  - Pass to `extract_from_text()`
- [ ] Handle edge cases:
  - Paywalled content
  - Invalid URLs
  - Multiple claims in one article
- [ ] Write tests with 5 sample claims (political, health, economy, science, general)

**Test Cases**:
1. Simple text: "L'ISTAT ha dichiarato che l'inflazione è al 5%"
2. Complex URL: Reuters article with multiple facts
3. Ambiguous claim: Opinion vs fact separation

**Deliverable**: Working claim extractor with tests

---

### Task 1.3: Tool Manager & Caching
**Priority**: High | **Est. Time**: 3 hours

**File**: `src/utils/tool_manager.py`

- [ ] Create `ToolManager` class:
  ```python
  class ToolManager:
      def __init__(self):
          self.url_cache = {}
          self.search_cache = {}
      
      def get_url(self, url: str, agent: str) -> str:
          # Check cache, fetch if needed
      
      def search_web(self, query: str, tool: str) -> List[Dict]:
          # Check cache, search if needed
      
      def clear_cache(self):
          # Clear for new claim
  ```
- [ ] Implement cache expiration (TTL: 1 hour)
- [ ] Add logging for cache hits/misses
- [ ] Write unit tests

**Deliverable**: `ToolManager` with caching

---

## 🔧 Phase 2: Tool Integration

### Task 2.1: Web Search Tools
**Priority**: Critical | **Est. Time**: 4 hours

**File**: `src/tools/search_tools.py`

- [ ] Implement `brave_search(query: str, count: int = 10) -> List[Dict]`:
  - API key from env
  - Parse response to standard format
  - Handle rate limits (429 errors)
- [ ] Implement `duckduckgo_search(query: str) -> List[Dict]`:
  - Fallback when Brave fails
  - HTML parsing (no API key needed)
- [ ] Implement `google_pse_factcheck(query: str) -> List[Dict]`:
  - Restrict to fact-checking domains
  - Return existing fact-checks if found
- [ ] Create unified interface:
  ```python
  def search(query: str, tool: str = "brave") -> List[Dict]
  ```
- [ ] Write integration tests (mock API responses)

**Deliverable**: Working search functions

---

### Task 2.2: Content Extraction Tools
**Priority**: Critical | **Est. Time**: 3 hours

**File**: `src/tools/content_tools.py`

- [ ] Implement `fetch_article(url: str) -> Dict`:
  - Use `newspaper3k` for article extraction
  - Fallback to `BeautifulSoup` if newspaper fails
  - Extract: title, text, publish_date, authors
- [ ] Implement `assess_source_reliability(url: str) -> str`:
  - Domain whitelist for "high" (gov, major news)
  - Check domain age, HTTPS
  - Return: "high", "medium", "low"
- [ ] Handle paywalls gracefully (return snippet)
- [ ] Write tests with 5 different source types

**Deliverable**: Article extraction with reliability scoring

---

### Task 2.3: News & Social APIs
**Priority**: Medium | **Est. Time**: 4 hours

**Files**: `src/tools/news_api.py`, `src/tools/reddit_api.py`

**NewsAPI Integration**:
- [ ] Implement `search_news(query: str, from_date: str) -> List[Dict]`:
  - Filter by language (Italian)
  - Sort by relevancy
  - Extract articles
- [ ] Handle free tier limits (100 req/day)

**Reddit Integration**:
- [ ] Implement `search_reddit(query: str, subreddits: List[str]) -> List[Dict]`:
  - Use PRAW library
  - Search relevant subreddits: ["italy", "news", "worldnews"]
  - Extract top comments
- [ ] Parse sentiment from comments

**Deliverable**: News and social search functions

---

### Task 2.4: Academic Search (Optional for MVP)
**Priority**: Low | **Est. Time**: 2 hours

**File**: `src/tools/academic_tools.py`

- [ ] Implement `search_arxiv(query: str) -> List[Dict]`:
  - For scientific claims
  - Return paper titles, abstracts, URLs
- [ ] Mark as "academic source" for JUDGE scoring

**Deliverable**: ArXiv search (can be skipped if time-constrained)

---

## 🤖 Phase 3: Agent Implementation

### Task 3.1: Base Agent Class
**Priority**: Critical | **Est. Time**: 3 hours

**File**: `src/agents/base_agent.py`

- [ ] Create `BaseAgent` abstract class:
  ```python
  class BaseAgent:
      def __init__(self, llm, tool_manager):
          self.llm = llm
          self.tools = tool_manager
      
      def think(self, state: GraphState) -> DebateMessage:
          # To be implemented by subclasses
          pass
      
      def search(self, query: str, strategy: str):
          # Tier-based search logic
          pass
  ```
- [ ] Implement tiered search strategy
- [ ] Add logging for agent actions
- [ ] Write base tests

**Deliverable**: Reusable base agent class

---

### Task 3.2: PRO Agent Implementation
**Priority**: Critical | **Est. Time**: 4 hours

**File**: `src/agents/pro_agent.py`

- [ ] Create `ProAgent(BaseAgent)`:
  - Personality: Institutional, formal
  - Search priority: Government → News → Academic
- [ ] Write system prompt:
  ```
  You are a meticulous institutional analyst.
  Your goal: Find authoritative sources supporting the claim.
  If claim seems false, find the original source of misinformation.
  Never fabricate evidence.
  ```
- [ ] Implement `think()` method:
  - Generate search queries
  - Call tools based on claim category
  - Compile argument with sources
  - Return `DebateMessage`
- [ ] Add source citation validation
- [ ] Test with 3 sample claims (true, false, ambiguous)

**Deliverable**: Working PRO agent

---

### Task 3.3: CONTRA Agent Implementation
**Priority**: Critical | **Est. Time**: 4 hours

**File**: `src/agents/contra_agent.py`

- [ ] Create `ContraAgent(BaseAgent)`:
  - Personality: Skeptical investigator
  - Search priority: FactCheck → Social → Blogs
- [ ] Write system prompt:
  ```
  You are a critical fact-checker.
  Your goal: Find contradictory evidence or missing context.
  If claim is TRUE, identify:
  - Exaggerations in framing
  - Missing important context
  - Biased presentation
  Do not deny clear evidence.
  ```
- [ ] Implement `think()` method with rebuttal logic
- [ ] Add fallacy detection helpers:
  - Ad hominem checker
  - Straw man detector
- [ ] Test with same 3 claims as PRO

**Deliverable**: Working CONTRA agent

---

### Task 3.4: JUDGE Agent Implementation
**Priority**: Critical | **Est. Time**: 5 hours

**File**: `src/agents/judge_agent.py`

- [ ] Create `JudgeAgent(BaseAgent)`:
  - Personality: Impartial, analytical
  - No search tools (only evaluates existing evidence)
- [ ] Write system prompt with verdict categories:
  ```
  You are an impartial Supreme Court judge.
  Evaluate the debate between PRO and CONTRA.
  Verdict options:
  - VERO (True)
  - FALSO (False)
  - PARZIALMENTE_VERO (Partially True)
  - CONTESTO_MANCANTE (Missing Context)
  - NON_VERIFICABILE (Cannot Verify)
  
  Provide confidence score (0-100) based on:
  - Source quality and independence
  - Logical consistency
  - Evidence strength
  ```
- [ ] Implement `evaluate()` method:
  - Parse full debate history
  - Verify source citations match claims
  - Detect logical fallacies
  - Generate `Verdict` object
- [ ] Add structured output parsing (JSON mode)
- [ ] Test with complete debate transcripts

**Deliverable**: Working JUDGE agent with verdict generation

---

## 🎭 Phase 4: Orchestration with LangGraph

### Task 4.1: Define State Graph
**Priority**: Critical | **Est. Time**: 4 hours

**File**: `src/orchestrator/graph.py`

- [ ] Create graph nodes:
  1. `extract_claim`: Parse input
  2. `pro_research`: PRO initial search
  3. `contra_research`: CONTRA initial search
  4. `debate_round`: Iterative rebuttals
  5. `judge_verdict`: Final evaluation
- [ ] Define edges and conditional routing:
  ```python
  graph = StateGraph(GraphState)
  graph.add_node("extract", extract_claim)
  graph.add_node("pro", pro_agent.think)
  graph.add_node("contra", contra_agent.think)
  graph.add_node("debate", debate_round)
  graph.add_node("judge", judge_agent.evaluate)
  
  graph.add_edge(START, "extract")
  graph.add_edge("extract", "pro")
  graph.add_edge("extract", "contra")
  graph.add_conditional_edges(
      "debate",
      should_continue,  # Check if max rounds reached
      {True: "debate", False: "judge"}
  )
  ```
- [ ] Implement `should_continue()` logic:
  - Max 3 rounds
  - Early stop if agents reach consensus
- [ ] Compile graph

**Deliverable**: Executable LangGraph

---

### Task 4.2: Debate Round Logic
**Priority**: Critical | **Est. Time**: 3 hours

**File**: `src/orchestrator/debate.py`

- [ ] Implement `debate_round(state: GraphState) -> GraphState`:
  ```python
  def debate_round(state):
      # CONTRA reads PRO's last argument
      contra_rebuttal = contra_agent.rebut(state.messages[-1])
      state.messages.append(contra_rebuttal)
      
      # PRO reads CONTRA's rebuttal
      pro_defense = pro_agent.defend(contra_rebuttal)
      state.messages.append(pro_defense)
      
      state.round_count += 1
      return state
  ```
- [ ] Add turn management (who speaks next)
- [ ] Implement convergence detection:
  - If both agents cite same sources → early stop
- [ ] Log each round to file

**Deliverable**: Debate orchestration logic

---

### Task 4.3: End-to-End Integration Test
**Priority**: Critical | **Est. Time**: 3 hours

**File**: `tests/test_full_pipeline.py`

- [ ] Create test with known true claim:
  - "Il terremoto in Emilia del 2012 ha avuto magnitudo 5.9"
- [ ] Create test with known false claim:
  - "L'ISTAT ha dichiarato che l'Italia ha 100 milioni di abitanti"
- [ ] Create test with ambiguous claim:
  - "Le tasse sono aumentate nel 2024"
- [ ] Run full pipeline for each
- [ ] Validate:
  - Graph completes without errors
  - Verdict format is valid JSON
  - Sources are real URLs
- [ ] Measure execution time

**Deliverable**: Passing integration tests

---

## 🖥️ Phase 5: CLI Interface

### Task 5.1: Command-Line Interface
**Priority**: High | **Est. Time**: 3 hours

**File**: `src/cli.py`

- [ ] Create CLI with `argparse`:
  ```bash
  python cli.py --input "text or url" --verbose
  ```
- [ ] Options:
  - `--input`: Claim text or URL
  - `--output`: Save verdict to JSON file
  - `--verbose`: Show debate transcript
  - `--no-cache`: Disable caching
- [ ] Display progress:
  - "Extracting claim..."
  - "PRO researching... (found 5 sources)"
  - "Debate round 1/3..."
  - "Judge evaluating..."
- [ ] Pretty-print verdict:
  ```
  ═══════════════════════════════════════
  VERDETTO: PARZIALMENTE_VERO
  Confidenza: 75%
  ═══════════════════════════════════════
  
  Sintesi: La notizia riporta un dato reale...
  
  Fonti Principali:
  [1] https://... (Affidabilità: Alta)
  [2] https://... (Affidabilità: Media)
  ```
- [ ] Add error handling with helpful messages

**Deliverable**: Working CLI

---

### Task 5.2: Logging & Debugging
**Priority**: Medium | **Est. Time**: 2 hours

**File**: `src/utils/logger.py`

- [ ] Set up structured logging:
  - INFO: High-level progress
  - DEBUG: Tool calls, API requests
  - ERROR: Failures with stack traces
- [ ] Log to both console and file:
  - `logs/veritasloop_{date}.log`
- [ ] Add performance metrics:
  - Time per agent
  - API call counts
  - Token usage
- [ ] Create log analyzer script

**Deliverable**: Comprehensive logging

---

## 🌐 Phase 6: Web Interface with Streamlit

### Task 6.1: Basic Streamlit App
**Priority**: Medium | **Est. Time**: 4 hours

**File**: `app.py`

- [ ] Create Streamlit layout:
  ```python
  st.title("🔍 VeritasLoop - Verifica Notizie")
  
  input_type = st.radio("Input Type", ["Testo", "URL"])
  claim_input = st.text_area() if text else st.text_input()
  
  if st.button("Verifica"):
      with st.spinner("Analizzando..."):
          result = run_verification(claim_input)
      
      st.json(result)
  ```
- [ ] Add input validation
- [ ] Display loading states
- [ ] Show verdict with color coding:
  - VERO: Green
  - FALSO: Red
  - PARZIALMENTE_VERO: Yellow

**Deliverable**: Basic Streamlit UI

---

### Task 6.2: Three-Column Debate View
**Priority**: Medium | **Est. Time**: 5 hours

**File**: `app.py` (enhanced)

- [ ] Create three columns:
  ```python
  col_pro, col_center, col_contra = st.columns([1, 1, 1])
  
  with col_pro:
      st.markdown("### 🛡️ PRO Agent")
      for msg in pro_messages:
          st.info(msg.content)
  
  with col_center:
      st.markdown("### ⚖️ Arena")
      st.progress(round / max_rounds)
  
  with col_contra:
      st.markdown("### 🔍 CONTRA Agent")
      for msg in contra_messages:
          st.warning(msg.content)
  ```
- [ ] Add source preview tooltips:
  - Hover over citation → Show snippet
- [ ] Animate debate progression:
  - Use `st.empty()` to update in real-time
- [ ] Add collapsible sections for full transcripts

**Deliverable**: Interactive debate visualization

---

### Task 6.3: Export & Sharing Features
**Priority**: Low | **Est. Time**: 2 hours

- [ ] Add "Download Report (PDF)" button:
  - Use `reportlab` or `weasyprint`
  - Include verdict, sources, full transcript
- [ ] Add "Copy Permalink" button:
  - Generate shareable URL (requires backend)
  - Store verdict in database (optional)
- [ ] Add social sharing:
  - Twitter share with verdict summary

**Deliverable**: Export functionality

---

## 🧪 Phase 7: Testing & Refinement (Days 16-18)

### Task 7.1: Create Test Dataset
**Priority**: High | **Est. Time**: 3 hours

**File**: `data/test_claims.json`

- [ ] Collect 30 diverse claims:
  - 10 Politics (Italian focus)
  - 5 Health/Science
  - 5 Economy
  - 5 General news
  - 5 Viral social media claims
- [ ] For each, include:
  - Claim text
  - Expected verdict (manual research)
  - Key sources (manual)
- [ ] Format as JSON array

**Deliverable**: Curated test dataset

---

### Task 7.2: Batch Testing & Analysis
**Priority**: High | **Est. Time**: 4 hours

**File**: `scripts/batch_test.py`

- [ ] Create script to run all test claims
- [ ] Compare:
  - System verdict vs expected verdict
  - System sources vs manual sources
- [ ] Calculate metrics:
  - Accuracy: % correct verdicts
  - Precision/Recall for each category
  - Average confidence score
  - Average processing time
- [ ] Generate report:
  ```
  Accuracy: 87% (26/30 correct)
  
  By Category:
  - Politics: 85%
  - Health: 90%
  - Economy: 80%
  
  Avg Time: 2m 34s
  Avg Sources: 8.3 per claim
  ```

**Deliverable**: Performance benchmark report

---

### Task 7.3: Prompt Tuning
**Priority**: High | **Est. Time**: 5 hours

- [ ] Review failed test cases
- [ ] Identify common issues:
  - PRO too defensive on false claims?
  - CONTRA too aggressive on true claims?
  - JUDGE confidence scores miscalibrated?
- [ ] Refine agent prompts iteratively:
  - Add examples of good reasoning
  - Clarify when to concede
  - Adjust source weighting instructions
- [ ] Re-run tests until >85% accuracy

**Deliverable**: Optimized prompts

---

### Task 7.4: Error Handling & Edge Cases
**Priority**: Medium | **Est. Time**: 3 hours

- [ ] Handle edge cases:
  - No search results found
  - All sources paywalled
  - Contradictory claims in same article
  - Non-news content (ads, spam)
- [ ] Add fallback logic:
  - If all tools fail → Verdict: NON_VERIFICABILE
  - If timeout → Return partial results
- [ ] Add user-friendly error messages
- [ ] Write tests for each edge case

**Deliverable**: Robust error handling

---

## 📚 Phase 8: Documentation & Polish

### Task 8.1: User Documentation
**Priority**: Medium | **Est. Time**: 3 hours

**File**: `README.md`

- [ ] Add sections:
  - Project overview
  - Installation guide
  - Quick start examples
  - Configuration options
  - API usage (if applicable)
  - Troubleshooting
  - Contributing guidelines
- [ ] Add screenshots of UI
- [ ] Include example verdicts

**Deliverable**: Comprehensive README

---

### Task 8.2: Code Documentation
**Priority**: Medium | **Est. Time**: 2 hours

- [ ] Add docstrings to all functions:
  ```python
  def search_web(query: str, tool: str) -> List[Dict]:
      """
      Search the web using specified tool.
      
      Args:
          query: Search query string
          tool: Tool name ("brave", "duckduckgo", "google_pse")
      
      Returns:
          List of search results with url, title, snippet
      
      Raises:
          APIError: If all tools fail
      """
  ```
- [ ] Generate API docs with Sphinx or pdoc
- [ ] Add inline comments for complex logic

**Deliverable**: Well-documented codebase

---

### Task 8.3: Performance Optimization
**Priority**: Low | **Est. Time**: 3 hours

- [ ] Profile slow functions:
  - Use `cProfile` or `line_profiler`
- [ ] Optimize:
  - Parallelize PRO/CONTRA initial research
  - Reduce redundant LLM calls
  - Compress cache data
- [ ] Add async/await for I/O operations
- [ ] Test improved speed

**Target**: <2 minutes per claim

**Deliverable**: Optimized performance

---

## 🚀 Phase 9: Deployment Preparation (Optional)

### Task 9.1: Docker Containerization
**Priority**: Low | **Est. Time**: 2 hours

**Files**: `Dockerfile`, `docker-compose.yml`

- [ ] Create Dockerfile:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY src/ ./src/
  CMD ["streamlit", "run", "app.py"]
  ```
- [ ] Add docker-compose for Redis
- [ ] Test local container

**Deliverable**: Dockerized app

---

### Task 9.2: Cloud Deployment (Optional)
**Priority**: Low | **Est. Time**: 3 hours

- [ ] Choose platform:
  - Streamlit Cloud (free, easy)
  - Railway (Dockerfile support)
  - Render (free tier)
- [ ] Set up environment variables
- [ ] Deploy and test
- [ ] Set up custom domain (optional)

**Deliverable**: Live public URL

---

## 📊 Summary Timeline

| Phase | Days | Focus |
|-------|------|-------|
| 0 - Setup | 1 | Environment, structure |
| 1 - Data Models | 2-3 | Schemas, claim extraction |
| 2 - Tools | 4-5 | Search APIs, content fetch |
| 3 - Agents | 6-8 | PRO, CONTRA, JUDGE |
| 4 - Orchestration | 9-11 | LangGraph integration |
| 5 - CLI | 12 | Command-line interface |
| 6 - Web UI | 13-15 | Streamlit app |
| 7 - Testing | 16-18 | Benchmarks, tuning |
| 8 - Polish | 19-20 | Documentation, optimization |
| 9 - Deploy | 21+ | Docker, cloud (optional) |

**Total Estimated Time**: 80-100 hours
---

## 🎯 Quick Start Path (Minimum Viable Product)

If you need to deliver a working demo quickly, follow this reduced path:

1. ✅ Task 0.1 - Setup (2h)
2. ✅ Task 1.1 - Data Models (3h)
3. ✅ Task 1.2 - Claim Extraction (4h)
4. ✅ Task 2.1 - Brave Search only (2h)
5. ✅ Task 3.2 - PRO Agent (4h)
6. ✅ Task 3.3 - CONTRA Agent (4h)
7. ✅ Task 3.4 - JUDGE Agent (5h)
8. ✅ Task 4.1 - Basic Graph (3h)
9. ✅ Task 5.1 - Simple CLI (2h)

**Total**: ~30 hours → Working prototype in 1 week

---

## 📝 Notes

- Prioritize tasks marked "Critical" for MVP
- "Medium" tasks enhance quality
- "Low" tasks are nice-to-have
- Adjust timeline based on your familiarity with LangGraph
- Consider pair programming for complex tasks (agents, graph)
- Test incrementally - don't wait until the end!