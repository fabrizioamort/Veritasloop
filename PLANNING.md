# VeritasLoop - Multi-Agent News Verification System
## Planning Document

## 1. Executive Summary

VeritasLoop is an adversarial multi-agent system that verifies news authenticity through dialectical debate. Instead of single-pass fact-checking, the system simulates a courtroom where a PRO agent defends the news, a CONTRA agent challenges it, and a JUDGE agent evaluates the arguments to deliver a nuanced verdict.

**Core Innovation**: Transparent reasoning process that exposes conflicting evidence, reduces confirmation bias, and provides context-aware verdicts beyond binary true/false.

## 2. Project Scope

### In Scope (MVP - Version 1.0)
- ✅ Three-agent architecture (PRO, CONTRA, JUDGE)
- ✅ State graph orchestration with LangGraph
- ✅ Multi-source verification (5 tool integrations - exceeded target)
- ✅ Structured JSON output with confidence scoring
- ✅ CLI interface for testing
- ✅ Smart caching with 1-hour TTL
- ✅ Italian language support (primary)
- ✅ Support for text and URL inputs
- ✅ Streamlit interface for testing
- ✅ React + Vite interface for production
- ✅ FastAPI backend with WebSocket streaming
- ✅ Phoenix observability integration
- ✅ Comprehensive logging and performance metrics
- ✅ Agent personality system with 3 communication styles per agent
- ✅ Named agents with personality-based identities (6 unique characters)

### Out of Scope (Future Versions)
- ❌ Real-time video/audio verification
- ❌ Image reverse search (v1.1)
- ❌ Multi-language simultaneous support
- ❌ User authentication/database persistence
- ❌ Mobile app
- ❌ Browser extension

### Success Criteria
1. Process a news claim end-to-end in <3 minutes
2. Generate structured verdict with sources
3. Identify at least 3 relevant sources per agent
4. Produce coherent debate transcript
5. Handle 90% of common news formats without errors

## 3. Technical Architecture

### 3.1 Technology Stack

**Core Framework**
- **Python 3.11+**: Primary language
- **LangGraph**: State machine orchestration
- **LangChain**: LLM tooling and prompt management
- **OpenAI GPT 45.1**: Primary LLM (via Open API)
- **Gemini 2.5pro**: Secondary LLM (via Open API)

**State Management**
- **Python dict** (default): In-memory state for MVP
- **Redis** (optional not a priority): Distributed caching for production

**Search & Verification Tools**
- **Brave Search API**: Primary web search (free tier: 2000 queries/month)
- **DuckDuckGo HTML**: Backup search (no API key)
- **Google Programmable Search Engine (PSE)**: Fact-check databases
- **NewsAPI**: News aggregation (free tier: 100 requests/day)
- **PRAW (Reddit API)**: Social sentiment analysis
- **ArXiv API**: Scientific paper verification

**Data Extraction**
- **BeautifulSoup4**: HTML parsing
- **newspaper3k**: Article extraction
- **python-magic**: MIME type detection

**Frontend (Implemented)**
- **Streamlit**: Rapid prototyping UI (legacy/alternative interface)
- **React + Vite**: Production UI with real-time WebSocket updates
- **FastAPI**: Backend API server with WebSocket streaming

### 3.2 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Input Layer                      │
│  (CLI / Web Interface / API Endpoint)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Orchestrator (LangGraph)                    │
│  - State Management                                      │
│  - Turn Control                                          │
│  - Stop Conditions (max rounds: 3)                       │
└────┬─────────────┬─────────────┬────────────────────────┘
     │             │             │
     ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│ PRO     │  │ CONTRA  │  │ JUDGE    │
│ Agent   │  │ Agent   │  │ Agent    │
│         │  │         │  │          │
│ Tools:  │  │ Tools:  │  │ Tools:   │
│ - News  │  │ - Reddit│  │ - Source │
│ - Govt  │  │ - Social│  │   Verify │
│ - PSE   │  │ - Blogs │  │ - Logic  │
└────┬────┘  └────┬────┘  └────┬─────┘
     │            │            │
     └────────────┴────────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │   Shared Memory       │
      │  - Debate History     │
      │  - Source Cache       │
      │  - Metadata           │
      └───────────────────────┘
```

### 3.3 Data Flow

```
1. INPUT → Claim Extraction
   ├─ Parse URL or text
   ├─ Extract core claim (single verifiable statement)
   └─ Identify entities (who, what, when, where)

2. PHASE 1: Parallel Research (Round 0)
   ├─ PRO Agent: Search for corroboration
   └─ CONTRA Agent: Search for refutation
   
3. PHASE 2: Debate Loop (Rounds 1-3)
   ├─ CONTRA reads PRO's argument → Rebuttal
   ├─ PRO reads CONTRA's rebuttal → Defense
   └─ Repeat until consensus or max rounds

4. PHASE 3: Judgment
   ├─ JUDGE analyzes full transcript
   ├─ Evaluates source quality
   ├─ Detects logical fallacies
   └─ Produces structured verdict

5. OUTPUT → Structured Report (JSON)
```

## 4. Agent Specifications

### 4.0 Agent Personality System (Version 0.3.0)

**Overview**: Each PRO and CONTRA agent can adopt one of three communication styles, allowing users to customize debate dynamics while maintaining the same evidence-gathering capabilities.

**PRO Agent Personalities**:

| Personality | Name | Style | Example Language |
|------------|------|-------|------------------|
| **Passive** | Oliver | Cautious, tentative | "It seems...", "Perhaps...", "Possibly..." |
| **Assertive** | Marcus | Confident, persuasive | "The evidence clearly shows...", "Facts support..." *(default)* |
| **Aggressive** | Victor | Forceful, confrontational | "Absolutely true!", "Undeniable!", "Anyone can see..." |

**CONTRA Agent Personalities**:

| Personality | Name | Style | Example Language |
|------------|------|-------|------------------|
| **Passive** | Sophie | Polite, diplomatic | "I wonder if...", "Perhaps we should consider..." |
| **Assertive** | Diana | Professional, firm | "The data contradicts...", "Research shows..." *(default)* |
| **Aggressive** | Raven | Harsh, relentless | "Completely false!", "Pure manipulation!", "Let me expose..." |

**Implementation**:
- Personality selection affects only **tone and language style**
- Search strategies, source reliability, and evidence gathering remain unchanged
- Configured via React UI with visual selector (icons + names)
- Stored in GraphState and passed to agents during initialization
- Prompts dynamically loaded from `src/config/personalities.py`

**Technical Files**:
- `src/config/personalities.py` - Personality definitions and prompts
- `frontend/src/components/ConfigPanel.jsx` - UI selector
- `frontend/src/components/AgentNode.jsx` - Display personality-based names
- `src/agents/pro_agent.py` - Dynamic prompt loading
- `src/agents/contra_agent.py` - Dynamic prompt loading
- `src/orchestrator/graph.py` - Agent creation with personality
- `api/main.py` - WebSocket parameter handling

### 4.1 PRO Agent (The Defender)
**Role**: Institutional Analyst defending the claim

**Base Personality Traits** (Modified by personality selection):
- Formal, data-driven
- Trusts official sources
- Conservative in claims

**Search Strategy**:
1. Government databases (ISTAT, Ministeri)
2. Major news agencies (ANSA, Reuters, AFP)
3. Official press releases
4. Academic institutions

**Prompt Directives**:
```
You are a meticulous analyst defending the news claim.
Your goal is to find authoritative sources that corroborate the claim.
If the claim appears false, search for the ORIGINAL SOURCE of the misinformation
or any "kernel of truth" that may have been distorted.
Never fabricate. If you cannot find supporting evidence, acknowledge it.
```

**Output Format**:
- Argument text (max 300 words)
- List of sources with reliability scores
- Confidence level (0-100)

### 4.2 CONTRA Agent (The Skeptic)
**Role**: Investigative journalist challenging the claim

**Personality Traits**:
- Skeptical, detail-oriented
- Looks for omissions and context
- Challenges clickbait framing

**Search Strategy**:
1. Fact-checking databases (Snopes, PolitiFact, Bufale.net)
2. Social media sentiment (Reddit, Twitter via nitter)
3. Independent expert blogs
4. Reverse image search (v1.1)

**Prompt Directives**:
```
You are a critical fact-checker challenging the news claim.
Your goal is to find contradictory evidence, missing context, or logical flaws.
If the claim is TRUE, focus on:
- Exaggerations in framing
- Missing important context
- Biased presentation
Do not deny clear evidence. Your strength is in CONTEXT and NUANCE.
```

**Output Format**:
- Rebuttal text (max 300 words)
- List of contradictory sources
- Identified fallacies or omissions

### 4.3 JUDGE Agent (The Arbiter)
**Role**: Supreme Court justice evaluating arguments

**Personality Traits**:
- Impartial, analytical
- Focused on logical coherence
- Weighs source quality over quantity

**Evaluation Criteria**:
1. **Source Quality**: Domain authority, publication date, author credentials
2. **Logical Validity**: Absence of fallacies (ad hominem, straw man, false equivalence)
3. **Evidence Alignment**: Do sources actually support the claims?
4. **Consensus Level**: Do multiple independent sources agree?

**Prompt Directives**:
```
You are an impartial judge evaluating a debate on news veracity.
Analyze the arguments from PRO and CONTRA agents.
Your verdict must be one of:
- VERO (True)
- FALSO (False)
- PARZIALMENTE_VERO (Partially True)
- CONTESTO_MANCANTE (Missing Context)
- NON_VERIFICABILE (Cannot Verify)

Provide confidence score (0-100) and justify your decision with specific
references to sources and logical reasoning.
```

## 5. Tool Integration Strategy

### 5.1 Tiered Search Approach

**Tier 1: Fact-Check Direct** ✅ (0-10 seconds)
- Google PSE configured for fact-checking sites
- If existing fact-check found → Skip to verdict

**Tier 2: News & Official Sources** ✅ (10-30 seconds)
- NewsAPI for recent articles
- Government open data APIs
- Primary source verification

**Tier 3: Broad Web Search** ✅ (30-60 seconds)
- Brave Search for general web
- DuckDuckGo as backup
- Blog posts, PDFs, reports

**Tier 4: Social & Community** ✅ (60-90 seconds)
- Reddit API (PRAW) for grassroots debunking
- Nitter for Twitter sentiment (no API needed)

**Tier 5: Academic/Specialized** ❌ (90-120 seconds)
- ArXiv for scientific claims (deferred to v1.1)
- Semantic Scholar for research papers (deferred to v1.1)

### 5.2 Smart Caching System

**ToolManager Class**:
```python
class ToolManager:
    def __init__(self):
        self.url_cache = {}  # {url: content}
        self.search_cache = {}  # {query_hash: results}
    
    def get_url(self, url, agent_name):
        if url in self.url_cache:
            return self.url_cache[url]
        content = fetch(url)
        self.url_cache[url] = content
        return content
```

**Cache Invalidation**: Clear after each new claim processing

## 6. Data Models

### 6.1 Claim Structure
```json
{
  "id": "claim_uuid",
  "raw_input": "Original text or URL",
  "core_claim": "Single verifiable statement",
  "entities": {
    "people": ["Nome Cognome"],
    "places": ["Roma", "Italia"],
    "dates": ["2024-12-04"],
    "organizations": ["ISTAT"]
  },
  "category": "politics|health|economy|science|other"
}
```

### 6.2 Debate Message
```json
{
  "round": 1,
  "agent": "PRO",
  "message_type": "argument|rebuttal|defense",
  "content": "Text of the argument",
  "sources": [
    {
      "url": "https://...",
      "title": "Source title",
      "snippet": "Relevant excerpt",
      "reliability": "high|medium|low",
      "timestamp": "ISO8601"
    }
  ],
  "confidence": 85
}
```

### 6.3 Final Verdict
```json
{
  "verdict": "PARTIALLY_TRUE",
  "confidence_score": 75,
  "summary": "Brief explanation in Italian",
  "analysis": {
    "pro_strength": "High - Cited official decree",
    "contra_strength": "Medium - Identified missing context",
    "consensus_facts": [
      "Fact 1 agreed by both",
      "Fact 2 agreed by both"
    ],
    "disputed_points": [
      "Disagreement on impact to middle class"
    ]
  },
  "sources_used": [
    {
      "url": "...",
      "reliability": "high",
      "agent": "PRO",
      "relevance_score": 0.9
    }
  ],
  "metadata": {
    "processing_time_seconds": 87,
    "rounds_completed": 3,
    "total_sources_checked": 12
  }
}
```

## 7. Risk Mitigation

### 7.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucinations | High | JUDGE verifies source citations exist and match claims |
| API rate limits | Medium | Implement exponential backoff + fallback tools |
| Infinite debate loops | Medium | Hard limit of 3 rounds + convergence detection |
| Source unavailability | Medium | Multiple tool fallbacks per tier |
| Slow processing (>5 min) | Low | Async tool calls + timeout limits |

### 7.2 Ethical Considerations

**Bias in Agent Personas**:
- Risk: PRO always favors establishment, CONTRA always skeptical
- Mitigation: Rotate agent roles randomly, JUDGE checks for balanced source diversity

**Echo Chamber Effect**:
- Risk: Only Italian sources may miss international context
- Mitigation: Include international fact-checkers in Tier 1

**Misinformation Amplification**:
- Risk: Showing false claims in UI may spread them
- Mitigation: Clear verdict labels, collapsible debate transcripts

## 8. Performance Targets

### 8.1 Speed
- Claim extraction: <5 seconds
- Per-agent search: <30 seconds
- Full debate cycle: <3 minutes
- Total processing: <5 minutes

### 8.2 Quality
- Source relevance: >80% on manual review
- Verdict accuracy: >85% vs human fact-checkers
- False positive rate: <10%

### 8.3 Cost (API Usage)
- LLM tokens per claim: ~15k tokens (~$0.05)
- Search API calls: ~20 queries (~$0.02)
- Total cost per verification: ~$0.07

**Budget**: $50/month → ~700 verifications/month

## 9. Deployment Strategy

### Phase 1: Local Development (Week 1-2)
- CLI-only interface
- Local Redis or in-memory state
- Manual testing with 20 diverse claims

### Phase 2: Betatesting Testing (Week 3)
- Streamlit web interface
- Develop a polished UI with React +
- Analytics integration

## 10. Future Enhancements (Post-MVP)

**Version 1.1 - Enhanced Verification**
- Image reverse search integration
- PDF/document analysis
- Multi-claim extraction from articles

**Version 1.2 - Collaboration Features**
- User voting on verdicts
- Community source submissions
- Fact-checker dashboard

**Version 2.0 - Advanced Intelligence**
- Fine-tuned claim extraction model
- Custom source reliability scoring
- Historical claim database with vector search
- Automated trending news monitoring

## 11. Open Questions & Decisions Needed

1. **Primary Language Model**: Claude Sonnet 4 vs GPT-4o vs Mixtral?
   - Recommendation: Claude Sonnet 4 (better reasoning, lower hallucination)

2. **Debate Stop Condition**: Fixed 3 rounds or dynamic convergence?
   - Recommendation: Fixed 3 rounds for MVP, add convergence detection in v1.1

3. **Source Reliability Scoring**: Manual whitelist or algorithmic?
   - Recommendation: Hybrid - manual for Tier 1, algorithmic for rest

4. **Frontend Framework**: Streamlit (fast) or React (polished)?
   - Recommendation: Streamlit for MVP, React for public launch

5. **Verdict Categories**: 5 categories sufficient or expand?
   - Recommendation: Keep 5 for MVP, track edge cases for future expansion