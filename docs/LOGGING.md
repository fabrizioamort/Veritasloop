# VeritasLoop Logging System

## Overview

VeritasLoop implements a comprehensive logging and performance monitoring system that tracks all operations, API calls, cache performance, and execution metrics throughout the verification pipeline.

## Features

- **Structured Logging**: Consistent log format with module, request ID, and claim ID tracking
- **Performance Metrics**: Automatic tracking of operation timings, API calls, cache hits/misses, and token usage
- **Multi-Level Logging**: Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **File & Console Output**: Simultaneous logging to daily log files and console
- **Context Management**: Thread-safe request context for distributed tracing
- **Log Analysis**: Built-in script for analyzing and visualizing log data

## Quick Start

### Basic Usage

```python
from src.utils.logger import setup_logging, get_logger

# Setup logging (call once at application startup)
setup_logging(level="INFO", enable_console=True, enable_file=True)

# Get a logger for your module
logger = get_logger(__name__)

# Use the logger
logger.info("Processing started")
logger.debug("Detailed debug information")
logger.warning("Something unexpected happened")
logger.error("An error occurred", exc_info=True)
```

### Performance Tracking

```python
from src.utils.logger import log_performance, init_metrics, get_metrics

# Initialize metrics for the current request
metrics = init_metrics()

# Track performance of an operation
with log_performance("claim_extraction"):
    result = extract_claim(text)

# Manually record metrics
metrics.add_api_call("brave_search")
metrics.add_cache_hit()
metrics.add_tokens("PRO", 150)

# Get metrics summary
from src.utils.logger import log_metrics_summary
summary = log_metrics_summary()
```

### Request Context

```python
from src.utils.logger import set_request_context, clear_request_context

# Set context at the start of a request
set_request_context(claim_id="claim_abc123", request_id="req_xyz789")

# All logs in this thread will include these IDs
logger.info("Processing claim")  # Will include claim_id and request_id

# Clear context when done
clear_request_context()
```

## CLI Usage

### Enable Debug Logging

```bash
# Run with debug logging enabled
python -m src.cli --input "..." --debug

# Run with verbose output and debug logging
python -m src.cli --input "..." --verbose --debug
```

### Export Metrics

When using `--verbose` and `--output`, metrics are automatically exported to a separate JSON file:

```bash
python -m src.cli --input "..." --output results.json --verbose

# Creates:
# - results.json (verification results)
# - results.metrics.json (performance metrics)
```

## Log File Format

Logs are stored in `logs/veritasloop_YYYYMMDD.log` with the following format:

```
YYYY-MM-DD HH:MM:SS | LEVEL    | module.name                    | req:request_id | claim:claim_id | message
```

Example:
```
2024-12-07 14:32:15 | INFO     | src.orchestrator.graph         | req:1733582735 | claim:abc123   | Starting claim extraction
2024-12-07 14:32:16 | INFO     | src.agents.pro_agent           | req:1733582735 | claim:abc123   | PRO research complete
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (API requests, cache operations, internal state)
- **INFO**: High-level progress messages (phase transitions, completions)
- **WARNING**: Unexpected situations that don't prevent execution
- **ERROR**: Errors that prevent specific operations from completing
- **CRITICAL**: Severe errors that may prevent the entire system from functioning

## Performance Metrics

The system automatically tracks:

### Timings
- Operation durations (min, max, average)
- Per-phase execution times
- Agent thinking times
- Tool execution times

### API Calls
- Number of calls per tool (brave_search, news_api, etc.)
- API success/failure rates

### Cache Performance
- Cache hits and misses
- Hit rate percentage
- Cache size

### Token Usage
- Total tokens consumed
- Tokens per agent (PRO, CONTRA, JUDGE)
- Average tokens per operation

### Errors
- Error count by type
- Error messages and timestamps
- Stack traces for debugging

## Log Analysis

Use the provided log analyzer script to extract insights:

```bash
# Analyze today's logs
python scripts/analyze_logs.py

# Analyze specific date
python scripts/analyze_logs.py --date 20241207

# Analyze all logs
python scripts/analyze_logs.py --all

# Export analysis to JSON
python scripts/analyze_logs.py --export analysis.json
```

### Analysis Output

The analyzer provides:
- Total log entries and unique claims processed
- Log level distribution
- Top modules by activity
- Performance metrics (avg/min/max timings)
- Cache hit rate
- API call statistics
- Error summary

## Best Practices

### 1. Use Appropriate Log Levels

```python
# Good
logger.debug(f"Searching with query: {query}")
logger.info("Verification completed successfully")
logger.warning("Using fallback API due to rate limit")
logger.error("Failed to fetch URL", exc_info=True)

# Bad
logger.info(f"Debug info: {internal_state}")  # Should be DEBUG
logger.error("User entered invalid input")    # Should be WARNING
```

### 2. Use Context Managers for Performance Tracking

```python
# Good - automatic timing and error handling
with log_performance("operation_name"):
    do_work()

# Bad - manual timing (error-prone)
start = time.time()
do_work()
duration = time.time() - start
metrics.add_timing("operation_name", duration)
```

### 3. Include Relevant Context in Log Messages

```python
# Good - includes context
logger.info(
    "Search completed",
    extra={"tool": "brave", "results_count": len(results)}
)

# Bad - missing context
logger.info("Search completed")
```

### 4. Set Request Context Early

```python
# Good - set at the start of request processing
set_request_context(claim_id=claim.id, request_id=f"req_{timestamp}")
# ... all subsequent logs will include these IDs

# Bad - forget to set context
# Logs will have "-" for claim_id and request_id
```

### 5. Clean Up Sensitive Data

```python
# Good - truncate or mask sensitive data
logger.debug(f"API key configured: {api_key[:8]}...")

# Bad - log full secrets
logger.debug(f"API key: {api_key}")  # Security risk!
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Enable/disable console logging
LOG_CONSOLE=true

# Enable/disable file logging
LOG_FILE=true

# Custom log directory
LOG_DIR=./custom_logs
```

### Programmatic Configuration

```python
from src.utils.logger import setup_logging

setup_logging(
    level="DEBUG",              # Log level
    log_dir="./my_logs",        # Custom directory
    enable_console=True,        # Console output
    enable_file=True            # File output
)
```

## Troubleshooting

### Logs Not Being Created

1. Check that the `logs/` directory exists and is writable
2. Verify `setup_logging()` is called before any logging
3. Check file permissions

### Performance Metrics Not Tracking

1. Ensure `init_metrics()` is called at request start
2. Verify operations use `log_performance()` context manager
3. Check that metrics are retrieved in the same thread

### Log File Size Growing Too Large

1. Logs rotate daily automatically (one file per day)
2. Use log level INFO or WARNING in production (avoid DEBUG)
3. Implement log archival/cleanup for old files

### Missing Context in Logs

1. Call `set_request_context()` early in request processing
2. Ensure context is set in the same thread
3. Check that logger uses the ContextFilter

## Architecture

### Components

1. **logger.py**: Core logging module
   - `setup_logging()`: Initialize logging system
   - `get_logger()`: Get logger instance
   - `PerformanceMetrics`: Metrics tracking class
   - `log_performance()`: Context manager for timing

2. **ContextFilter**: Adds request context to log records

3. **PerformanceMetrics**: Thread-local metrics storage

4. **analyze_logs.py**: Log analysis script

### Integration Points

- **CLI** ([src/cli.py](src/cli.py:32)): Initializes logging and metrics
- **Orchestrator** ([src/orchestrator/graph.py](src/orchestrator/graph.py:17)): Logs phase transitions
- **Agents** ([src/agents/base_agent.py](src/agents/base_agent.py)): Log agent operations
- **Tools** ([src/utils/tool_manager.py](src/utils/tool_manager.py:8)): Track API and cache operations

## Examples

### Complete Request Workflow

```python
from src.utils.logger import (
    setup_logging,
    get_logger,
    set_request_context,
    init_metrics,
    log_performance,
    log_metrics_summary,
)

# 1. Setup (once at startup)
setup_logging(level="INFO")
logger = get_logger(__name__)

# 2. Initialize request
metrics = init_metrics()
set_request_context(claim_id="claim_123", request_id="req_456")

# 3. Track operations
with log_performance("claim_extraction"):
    claim = extract_claim(text)

with log_performance("verification"):
    # Track API calls
    metrics.add_api_call("brave_search")

    # Track cache
    metrics.add_cache_hit()

    # Track tokens
    metrics.add_tokens("PRO", 150)

    result = verify_claim(claim)

# 4. Log summary
summary = log_metrics_summary(logger)

# 5. Clean up
clear_request_context()
```

## Future Enhancements

- [ ] Distributed tracing with OpenTelemetry
- [ ] Metrics export to Prometheus/Grafana
- [ ] Real-time log streaming
- [ ] Log aggregation for multi-instance deployments
- [ ] Automated anomaly detection
- [ ] Performance regression testing

## Support

For issues or questions about the logging system:
1. Check this documentation
2. Review test cases in `tests/test_logger.py`
3. Examine log files in `logs/`
4. Run the log analyzer for insights
