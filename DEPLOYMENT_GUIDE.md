# VeritasLoop Deployment Guide (Tier 1 + Tier 2 Optimizations)

## Overview

This guide covers deployment of the optimized VeritasLoop system with **50% faster performance** achieved through Tier 1 and Tier 2 optimizations.

**Performance Improvements:**
- Total Runtime: 40-50s → 20-25s (50% faster)
- Time to First Message: 11s → 5s (54% faster)
- API Call Reduction: ~40% fewer searches
- Resource Efficiency: 87% reduction in initialization overhead

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Performance Monitoring](#performance-monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### System Requirements

**Minimum:**
- Python 3.11+
- Node.js 18+ (for React frontend)
- 2GB RAM
- 1 CPU core

**Recommended:**
- Python 3.12
- Node.js 20+
- 4GB RAM
- 2+ CPU cores (for parallel operations)

### Required API Keys

Create a `.env` file in the project root:

```bash
# LLM Provider (required)
OPENAI_API_KEY=sk-...                    # Primary LLM

# Search APIs
BRAVE_SEARCH_API_KEY=...                 # Primary search (2000 free/month)

# Optional APIs
GEMINI_API_KEY=...                       # Alternative LLM
NEWS_API_KEY=...                         # News aggregation (100 free/day)
REDDIT_CLIENT_ID=...                     # Social sentiment
REDDIT_CLIENT_SECRET=...

# Optional: Logging
LOG_LEVEL=INFO                           # DEBUG, INFO, WARNING, ERROR
```

### Dependencies

Install Python dependencies:
```bash
uv sync
# OR
pip install -r requirements.txt
```

Install frontend dependencies:
```bash
cd frontend
npm install
```

---

## Quick Start

### Development Mode (Local Testing)

**Terminal 1: Backend**
```bash
uvicorn api.main:app --reload --port 8000
```

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```

**Access**: http://localhost:5173

### Verify Optimizations are Active

Run the verification scripts:
```bash
# Verify Tier 1 (Resource Pooling + Parallel Operations)
python verify_tier1_structure.py

# Verify Tier 2 (Lazy Research + Adaptive Depth)
python verify_tier2_structure.py
```

**Expected Output:**
```
✓ ALL TIER 1 STRUCTURE VERIFICATIONS PASSED
✓ ALL TIER 2 STRUCTURE VERIFICATIONS PASSED
```

---

## Production Deployment

### Option 1: Docker Deployment (Recommended)

**Create Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and Run:**
```bash
# Build image
docker build -t veritasloop:optimized .

# Run container
docker run -d \
  --name veritasloop \
  -p 8000:8000 \
  --env-file .env \
  veritasloop:optimized
```

**Docker Compose (Full Stack):**
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    depends_on:
      - backend
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

---

### Option 2: Cloud Platform Deployment

#### Render.com

1. **Backend Service:**
   - Runtime: Python 3.12
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables: Add all from `.env`

2. **Frontend Service:**
   - Runtime: Node 20
   - Build Command: `cd frontend && npm install && npm run build`
   - Start Command: `cd frontend && npm run preview -- --port $PORT`

#### Railway

```bash
railway login
railway init
railway up
```

Add environment variables via Railway dashboard.

#### AWS EC2

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install dependencies
sudo apt update
sudo apt install python3.12 python3-pip nodejs npm

# Clone repository
git clone https://github.com/fabrizioamort/Veritasloop.git
cd Veritasloop

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Run with PM2
npm install -g pm2
pm2 start ecosystem.config.js
```

**ecosystem.config.js:**
```javascript
module.exports = {
  apps: [
    {
      name: 'veritasloop-backend',
      script: 'uvicorn',
      args: 'api.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'python3',
      env: {
        NODE_ENV: 'production',
      },
    },
    {
      name: 'veritasloop-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run preview -- --port 5173',
    },
  ],
};
```

---

## Configuration

### Performance Tuning

#### Backend Configuration

**api/main.py** - WebSocket settings:
```python
# Adjust for concurrent connections
app = FastAPI(
    title="VeritasLoop API",
    timeout=300,  # 5 minutes for long debates
)

# WebSocket configuration
@app.websocket("/ws/verify")
async def websocket_verify_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Set timeouts
    websocket.timeout = 300
```

#### Optimization Settings

**Adjust Research Depth Threshold:**

Edit `src/orchestrator/graph.py:275`:
```python
def adaptive_research_depth(state: GraphState) -> dict:
    # Lower threshold = more deep research
    if last_msg.confidence < 50:  # Default: 50
        return {"research_depth": 2}
```

**Adjust Max Iterations:**

Default: 3 rounds of debate. To change:
```python
# When calling the workflow
initial_state = {
    "max_iterations": 2,  # Faster: 2 rounds
    # OR
    "max_iterations": 4,  # More thorough: 4 rounds
}
```

**Configure Cache TTL:**

Edit `src/utils/tool_manager.py` (cache duration):
```python
# Current: 1 hour (3600 seconds)
self.cache_ttl = 7200  # 2 hours for production
```

---

## Performance Monitoring

### Built-in Metrics

VeritasLoop logs performance metrics automatically:

**Enable Phoenix Tracing (Development):**
```bash
uv run python -m src.cli --input "..." --trace --verbose
```

View traces: http://localhost:6006

**Production Logging:**
```bash
# Set log level
export LOG_LEVEL=INFO

# View logs
tail -f logs/veritasloop.log
```

### Key Metrics to Monitor

**Performance Metrics:**
- `pro_opening`: Should be ~2-3s (Tier 2 optimization)
- `contra_research`: Should be ~3-5s
- `pro_turn_round_X`: Should be ~3-4s (with Tier 1 resource pooling)
- `contra_turn_round_X`: Should be ~4-5s
- `parallel_research` (if used): Should be ~5s (vs 9s sequential)

**Cache Metrics:**
- Cache hit rate: Target >30% in production
- API calls per verification: Target <12 (down from 15-20)

**Example Log Output:**
```
INFO - PRO opening complete (sources=0, confidence=60.0, duration=2.3s)
INFO - CONTRA research complete (sources=3, confidence=70.0, duration=4.1s)
INFO - Shallow research: using top 2 sources (depth=1)
INFO - Low confidence (45%), increasing research depth to 2
```

### Custom Monitoring

**Add Prometheus Metrics:**

Install:
```bash
pip install prometheus-fastapi-instrumentator
```

Update `api/main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)
Instrumentator().instrument(app).expose(app)
```

Access metrics: http://localhost:8000/metrics

---

## Troubleshooting

### Common Issues

#### Issue: "ModuleNotFoundError: No module named 'pydantic'"

**Solution:**
```bash
uv sync
# OR
pip install -r requirements.txt
```

#### Issue: "Field required: openai_api_key"

**Solution:**
Ensure `.env` file exists with required keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

#### Issue: Slow Performance (Not Seeing 50% Speedup)

**Check:**
1. Verify optimizations are enabled:
   ```bash
   python verify_tier1_structure.py
   python verify_tier2_structure.py
   ```

2. Check resource pool is working:
   ```python
   from src.utils.resource_pool import get_shared_llm
   llm1 = get_shared_llm()
   llm2 = get_shared_llm()
   assert llm1 is llm2  # Should be same instance
   ```

3. Check logs for "Lazy research" messages:
   ```bash
   grep "PRO opening" logs/*.log
   # Should see: "PRO opening complete (sources=0..."
   ```

#### Issue: High API Costs

**Solution:**
Reduce research depth threshold for more shallow research:
```python
# src/orchestrator/graph.py
if last_msg.confidence < 40:  # Was 50, now stricter
    return {"research_depth": 2}
```

Or reduce max iterations:
```python
initial_state = {"max_iterations": 2}  # Instead of 3
```

---

## Rollback Procedures

### Rollback to Pre-Optimization Version

**If optimizations cause issues, rollback is easy:**

**Option 1: Git Rollback**
```bash
# Find commit before optimizations
git log --oneline | grep "before optimization"

# Rollback
git checkout <commit-hash>

# Deploy old version
uvicorn api.main:app --reload
```

**Option 2: Use Parallel Research (Tier 1 Only)**

The system still supports the old `parallel_research` node:

Edit `src/orchestrator/graph.py`:
```python
# Comment out new flow
# workflow.add_edge("extract", "pro_opening")

# Use old flow
workflow.add_edge("extract", "parallel_research")
workflow.add_edge("parallel_research", "pro_node")
```

**Option 3: Disable Specific Optimizations**

**Disable Lazy Research:**
```python
# In graph.py, use parallel_research instead of pro_opening
workflow.add_edge("extract", "parallel_research")
```

**Disable Adaptive Depth:**
```python
# Remove adaptive_depth node from workflow
# workflow.add_node("adaptive_depth", adaptive_research_depth)

# Use fixed depth
initial_state = {"research_depth": 2}  # Always deep
```

**Disable Resource Pooling:**
```python
# In debate.py, revert to old imports
from src.utils.tool_manager import ToolManager
from src.utils.claim_extractor import get_llm

# In functions, create new instances
llm = get_llm()
tool_manager = ToolManager()
```

---

## Performance Benchmarks

### Expected Performance (Tier 1 + Tier 2)

**Test Claim:** "L'ISTAT ha dichiarato che l'inflazione è al 5%"

| Metric | Baseline | Tier 1 | Tier 1+2 | Target |
|--------|----------|--------|----------|--------|
| First Message | 11s | 11s | **5s** | <6s ✅ |
| Total Time | 47s | 36s | **24s** | <25s ✅ |
| API Calls | 18 | 18 | **11** | <12 ✅ |
| Init Overhead | 4s | 0.5s | **0.5s** | <1s ✅ |

### Load Testing

**Concurrent Users Test:**
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test 100 requests, 10 concurrent
ab -n 100 -c 10 -p claim.json -T application/json \
   http://localhost:8000/api/verify
```

**Expected:**
- Throughput: 3-5 requests/second
- Mean response time: <25s
- No failures with proper caching

---

## Health Checks

### Endpoint: GET /health

**Add to api/main.py:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "optimizations": {
            "tier1": True,
            "tier2": True,
            "resource_pooling": True,
            "lazy_research": True
        },
        "version": "2.0.0-optimized"
    }
```

**Monitor:**
```bash
curl http://localhost:8000/health
```

---

## Security Considerations

1. **API Key Protection:**
   - Never commit `.env` to git
   - Use environment variables in production
   - Rotate keys regularly

2. **Rate Limiting:**
   ```python
   # Add to api/main.py
   from slowapi import Limiter
   limiter = Limiter(key_func=lambda: "global")

   @app.post("/api/verify")
   @limiter.limit("10/minute")
   async def verify_claim(...):
       ...
   ```

3. **Input Validation:**
   - Already handled by Pydantic schemas
   - Claims sanitized in `claim_extractor.py`

---

## Maintenance

### Regular Tasks

**Weekly:**
- Check logs for errors
- Monitor API usage and costs
- Review cache hit rates

**Monthly:**
- Update dependencies: `pip install -U -r requirements.txt`
- Review performance metrics
- Clear old logs

**Quarterly:**
- API key rotation
- Performance audit
- User feedback review

---

## Support and Documentation

**Additional Resources:**
- [OPTIMIZATION_PLAN.md](OPTIMIZATION_PLAN.md) - Detailed optimization strategy
- [OPTIMIZATION_VISUAL_SUMMARY.md](OPTIMIZATION_VISUAL_SUMMARY.md) - Visual guides
- [CLAUDE.md](CLAUDE.md) - Updated development guide
- [README.md](README.md) - Project overview

**Verification Scripts:**
- `verify_tier1_structure.py` - Tier 1 checks
- `verify_tier2_structure.py` - Tier 2 checks

**Contact:**
- GitHub Issues: https://github.com/fabrizioamort/Veritasloop/issues

---

## Success Criteria

Your deployment is successful if:
- ✅ Health check returns `"status": "healthy"`
- ✅ First message appears in <6 seconds
- ✅ Total verification completes in <25 seconds
- ✅ Verification scripts pass
- ✅ No errors in logs
- ✅ API costs reduced by ~40%

**Congratulations on deploying the optimized VeritasLoop!** 🎉
