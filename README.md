# VeritasLoop

<div align="center">

**A Multi-Agent News Verification System Through Adversarial Debate**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![LangChain](https://img.shields.io/badge/LangChain-1.1.2-orange.svg)](https://github.com/langchain-ai/langchain)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.30+-red.svg)](https://github.com/langchain-ai/langgraph)

[Features](#-key-features) • [Installation](docs/INSTALLATION.md) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](docs/ARCHITECTURE.md)

</div>

---

## 📢 Latest Updates

**Version 0.2.0 - December 2025**
- ✨ **New React Web UI**: Modern, professional single-page application with real-time WebSocket streaming
- 🚀 **FastAPI Backend**: High-performance API server with WebSocket support for real-time communication
- 🎨 **Glassmorphism Design**: Cyber-courtroom aesthetic with smooth animations and visual effects
- 🔄 **Real-Time Updates**: Live agent status indicators and progressive message rendering
- ⚙️ **Configurable Parameters**: Adjust max iterations and max searches directly from the UI
- 📱 **Responsive Design**: Optimized for desktop and tablet devices
- 🎭 **Dramatic Verdict Reveal**: Full-screen modal with color-coded results and detailed analysis
- 🔧 **Developer Experience**: Hot Module Replacement (HMR) for instant development feedback

**Previous Releases:**
- Version 0.1.0 - Streamlit web UI, CLI interface, and core multi-agent system

---

<div align="center">

![React Web UI](docs/images/react-ui-main.png)

*The modern React-based web interface with real-time WebSocket streaming and cyber-courtroom aesthetic*

</div>

---

## Overview

**VeritasLoop** is an advanced adversarial multi-agent system that verifies news authenticity through structured dialectical debate. Rather than relying on traditional single-pass fact-checking, VeritasLoop simulates a courtroom scenario where:

- **PRO Agent** 🛡️: An institutional analyst that defends claims using authoritative sources (government, academic, major news)
- **CONTRA Agent** 🔍: A skeptical investigator that challenges claims, identifying contradictions and missing context
- **JUDGE Agent** ⚖️: An impartial evaluator that analyzes the full debate and delivers a nuanced, structured verdict

This adversarial approach reduces confirmation bias, exposes conflicting evidence transparently, and produces nuanced verdicts in **five categories** rather than simple true/false labels.

### Why VeritasLoop?

Traditional fact-checking suffers from several limitations:

- **Single-perspective bias**: One analyst may miss counter-evidence
- **Binary outcomes**: True/false labels miss important nuance
- **Black-box reasoning**: Users don't see the verification process
- **Limited source diversity**: Often relies on single databases

VeritasLoop addresses these through:

- **Adversarial validation**: Two opposing agents ensure balanced analysis
- **Transparent debate**: Full reasoning and sources exposed to users
- **Nuanced verdicts**: Five-category classification system (True, False, Partially True, Missing Context, Cannot Verify)
- **Multi-source verification**: Web search, news APIs, social sentiment, fact-check databases

---

## 🎯 Key Features

### Core Capabilities

- **🎭 Adversarial Multi-Agent Architecture**: Three specialized agents (PRO, CONTRA, JUDGE) working through LangGraph state orchestration
- **🔄 Dialectical Debate Process**: Up to 3 rounds of structured argumentation with rebuttals and defenses
- **🎨 Nuanced Verdict System**: Five-category classification (True, False, Partially True, Missing Context, Cannot Verify)
- **📚 Multi-Source Verification**:
  - Brave Search API (primary web search)
  - DuckDuckGo (scraping fallback)
  - NewsAPI (news aggregation)
  - Reddit API via PRAW (social sentiment)
- **🔗 Flexible Input**: Supports both raw text claims and URL extraction
- **🇮🇹 Italian Language Support**: Native Italian output with comprehensive summaries
- **💾 Smart Caching**: 1-hour TTL cache to reduce redundant API calls
- **📊 Source Reliability Assessment**: Automatic classification (High/Medium/Low) based on domain authority

### User Interfaces

- **🎨 React Web UI** (Recommended): Modern, professional single-page application with real-time WebSocket streaming, smooth animations, and glassmorphism design
- **🖥️ Streamlit Web UI** (Legacy): Alternative interface with real-time debate streaming (maintained for compatibility)
- **⚡ Command-Line Interface**: Fast, scriptable verification with JSON export
- **🔧 Programmatic API**: Direct Python integration for custom workflows

### Observability & Debugging

- **🔍 Arize Phoenix Integration**: Visual tracing of agent interactions and LLM calls
- **📈 Performance Metrics**: Detailed tracking of API calls, cache performance, and timing
- **🗄️ Persistent Traces**: SQLite database storage for historical analysis
- **📊 Real-time Monitoring**: Watch agent reasoning and tool calls in action

---

## 🚀 Quick Start

### Web Interface (Recommended)

#### React Web UI (Modern SPA)

```bash
# Terminal 1: Start the FastAPI backend
uvicorn api.main:app --reload --port 8000

# Terminal 2: Start the React frontend
cd frontend
npm install  # Only needed the first time
npm run dev
```

Open **http://localhost:5173** to access the modern web interface with real-time updates.

**See [Usage Guide](docs/USAGE.md) for detailed instructions.**

#### Streamlit Web UI (Legacy)

```bash
# Option 1: Use launcher script
./launch_streamlit.sh  # Linux/Mac
launch_streamlit.bat   # Windows

# Option 2: Direct launch
streamlit run app.py
```

Open **http://localhost:8501** for the Streamlit interface.

### Command-Line Interface

```bash
# Verify a text claim
uv run python -m src.cli --input "L'ISTAT ha dichiarato che l'inflazione è al 5%"

# Verify a news article URL
uv run python -m src.cli --input "https://www.ansa.it/sito/notizie/..."

# Show detailed debate transcript
uv run python -m src.cli --input "..." --verbose

# Save results to JSON
uv run python -m src.cli --input "..." --output results.json

# Enable visual tracing with Phoenix
uv run python -m src.cli --input "..." --trace --verbose
```

### Example Output

```
═════════════════════════════════════════════════════════════════
✅  VERDETTO: VERO
   Confidenza: 85%
═════════════════════════════════════════════════════════════════

📝 Sintesi:
La notizia riporta un dato reale confermato da fonti ufficiali dell'ISTAT.
Il tasso di inflazione del 5% corrisponde ai dati pubblicati nel rapporto
mensile di gennaio 2024...

📊 Analisi:
  Punti di forza PRO:
    • Fonti istituzionali autorevoli (ISTAT, Banca d'Italia)
    • Dati statistici verificabili e tracciabili
  ...

📚 Fonti Principali (8 verificate):
  [1] ISTAT - Inflazione Report Gennaio 2024
      https://www.istat.it/it/archivio/288969
      Affidabilità: Alta 🟢
  ...

⏱️  Metadata:
  • Tempo di elaborazione: 42.3 secondi
  • Round di dibattito: 2
  • Fonti totali analizzate: 23
```

---

## 📖 Documentation

### Core Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation and setup instructions
- **[Usage Guide](docs/USAGE.md)** - How to use all interfaces (Web, CLI, API)
- **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical system design and data models
- **[React UI Guide](docs/REACT_UI.md)** - Modern web interface architecture
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment strategies
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and development workflows

### Additional Resources

- **[LOGGING.md](docs/LOGGING.md)** - Logging system documentation
- **[PLANNING.md](PLANNING.md)** - Project planning and roadmap
- **[TASK.md](TASK.md)** - Detailed task breakdown and status
- **[STREAMLIT_GUIDE.md](docs/STREAMLIT_GUIDE.md)** - Streamlit UI usage guide
- **[PHOENIX_ENHANCEMENT_SUMMARY.md](PHOENIX_ENHANCEMENT_SUMMARY.md)** - Phoenix integration details

### Quick Reference

#### Verdict Categories

| Verdict | Italian | Description |
|---------|---------|-------------|
| ✅ **TRUE** | `VERO` | Substantially accurate and supported by strong evidence |
| ❌ **FALSE** | `FALSO` | Demonstrably false with credible contradictory evidence |
| ⚠️ **PARTIALLY TRUE** | `PARZIALMENTE_VERO` | Contains truth but misleading or exaggerated |
| 🔍 **MISSING CONTEXT** | `CONTESTO_MANCANTE` | Technically accurate but misleading without context |
| ❓ **CANNOT VERIFY** | `NON_VERIFICABILE` | Insufficient credible evidence to confirm or deny |

#### CLI Options

```bash
uv run python -m src.cli [OPTIONS]

Required:
  --input, -i TEXT        The claim text or URL to verify

Optional:
  --output, -o PATH       Save verdict to JSON file
  --verbose, -v           Show detailed debate transcript
  --trace                 Enable Phoenix observability
  --debug                 Enable debug-level logging
  --no-cache              Disable caching
  --help                  Show help message
```

---

## 🏗️ Architecture

VeritasLoop uses a LangGraph-orchestrated state machine with three specialized agents:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INPUT PROCESSING                                             │
│    Extract core claim + entities (LLM)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. PARALLEL RESEARCH                                            │
│    PRO Research (institutional) | CONTRA Research (fact-check)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. DEBATE ROUNDS (up to 3 iterations)                           │
│    CONTRA rebuttal → PRO defense → Loop                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. JUDGE EVALUATION                                             │
│    Analyze debate → Generate structured verdict                 │
└─────────────────────────────────────────────────────────────────┘
```

**See [Architecture Overview](docs/ARCHITECTURE.md) for detailed technical documentation.**

---

## 🛠️ Development

### Project Structure

```
veritasloop/
├── api/                        # FastAPI backend with WebSocket
├── frontend/                   # React Web UI
├── src/                        # Core Python backend
│   ├── agents/                 # PRO, CONTRA, JUDGE agents
│   ├── orchestrator/           # LangGraph state machine
│   ├── tools/                  # Search, content, news APIs
│   └── utils/                  # Caching, logging, utilities
├── tests/                      # Comprehensive test suite
├── docs/                       # Documentation
└── data/phoenix/              # Phoenix traces database
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_pro_agent.py -v
```

**Target**: Maintain >80% code coverage

### Contributing

We welcome contributions! Please see [Development Guide](docs/DEVELOPMENT.md) for:

- Development setup
- Code style guidelines
- Testing requirements
- Git workflow
- Pull request process

---

## 📊 Performance & Metrics

VeritasLoop tracks comprehensive metrics:

- **Processing Time**: 30-90 seconds typical
- **API Calls**: Logged per tool (search, content, news)
- **Cache Performance**: Hit/miss ratios
- **Token Usage**: By agent and total
- **Source Quality**: Reliability distribution

**See [Usage Guide](docs/USAGE.md#performance--metrics) for details.**

---

## 🔍 Observability

### Arize Phoenix Integration

Visual tracing of the entire verification process:

```bash
# Enable tracing
uv run python -m src.cli --input "..." --trace --verbose

# Access Phoenix UI
# Open http://localhost:6006
```

**Features:**
- Visual trace timeline
- Agent reasoning inspection
- LLM prompt/response viewer
- Tool call monitoring
- Performance metrics

**See [Usage Guide](docs/USAGE.md#observability--debugging) for detailed Phoenix usage.**

---

## 🚢 Deployment

### Quick Deploy

**Docker Compose (Full Stack):**
```bash
docker-compose up -d
```

**Individual Services:**
```bash
# Backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend (after npm run build)
# Serve frontend/dist/ with Nginx
```

**See [Deployment Guide](docs/DEPLOYMENT.md) for production strategies including:**
- Docker deployment
- Nginx configuration
- SSL/TLS setup
- Environment variables
- Security considerations
- Monitoring & logging

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Read [Development Guide](docs/DEVELOPMENT.md)
2. Fork the repository
3. Create a feature branch
4. Write tests for new functionality
5. Follow code style (Black for Python, ESLint for JS)
6. Submit a pull request

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain** and **LangGraph** for agent orchestration
- **Anthropic** for Claude language models
- **OpenAI** for GPT models
- **Arize Phoenix** for observability infrastructure
- **Brave Search** for high-quality search API
- **Streamlit** for rapid UI prototyping

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/veritasloop/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/veritasloop/discussions)
- **Documentation**: See [docs/](docs/) directory

---

<div align="center">

**Built with ❤️ for transparent, adversarial news verification**

[⬆ Back to Top](#veritasloop)

</div>
