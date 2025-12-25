"""
Centralized logging configuration for VeritasLoop.

This module provides:
- Structured logging with consistent formatting
- File and console output handlers
- Performance metrics tracking
- Request-scoped context management
- Log level configuration per module

Example:
    >>> from src.utils.logger import get_logger, log_performance
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing claim", extra={"claim_id": "123"})
    >>>
    >>> with log_performance("claim_extraction"):
    ...     result = extract_claim(text)
"""

import json
import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

# Thread-local storage for request context
_thread_local = threading.local()


class PerformanceMetrics:
    """
    Track performance metrics during request processing.

    Metrics tracked:
    - Execution time per operation
    - API call counts
    - Cache hit/miss ratios
    - Token usage
    """

    def __init__(self):
        """Initialize performance metrics tracker."""
        self.metrics: dict[str, Any] = {
            "timings": {},
            "api_calls": {},
            "cache": {"hits": 0, "misses": 0},
            "tokens": {"total": 0, "by_agent": {}},
            "errors": []
        }
        self.start_time = time.time()

    def add_timing(self, operation: str, duration: float):
        """
        Record operation timing.

        Args:
            operation: Name of the operation (e.g., "pro_research")
            duration: Time taken in seconds
        """
        if operation not in self.metrics["timings"]:
            self.metrics["timings"][operation] = []
        self.metrics["timings"][operation].append(duration)

    def add_api_call(self, tool: str):
        """
        Increment API call counter.

        Args:
            tool: Name of the tool/API (e.g., "brave_search")
        """
        if tool not in self.metrics["api_calls"]:
            self.metrics["api_calls"][tool] = 0
        self.metrics["api_calls"][tool] += 1

    def add_cache_hit(self):
        """Record a cache hit."""
        self.metrics["cache"]["hits"] += 1

    def add_cache_miss(self):
        """Record a cache miss."""
        self.metrics["cache"]["misses"] += 1

    def add_tokens(self, agent: str, count: int):
        """
        Record token usage.

        Args:
            agent: Agent name (e.g., "PRO", "CONTRA", "JUDGE")
            count: Number of tokens used
        """
        self.metrics["tokens"]["total"] += count
        if agent not in self.metrics["tokens"]["by_agent"]:
            self.metrics["tokens"]["by_agent"][agent] = 0
        self.metrics["tokens"]["by_agent"][agent] += count

    def add_error(self, error_type: str, message: str):
        """
        Record an error.

        Args:
            error_type: Type/category of error
            message: Error message
        """
        self.metrics["errors"].append({
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def get_summary(self) -> dict[str, Any]:
        """
        Get complete metrics summary.

        Returns:
            Dictionary with all metrics and computed statistics
        """
        total_time = time.time() - self.start_time

        # Compute average timings
        avg_timings = {}
        for op, times in self.metrics["timings"].items():
            avg_timings[op] = {
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "count": len(times)
            }

        # Compute cache hit rate
        total_cache = self.metrics["cache"]["hits"] + self.metrics["cache"]["misses"]
        cache_hit_rate = (
            self.metrics["cache"]["hits"] / total_cache * 100
            if total_cache > 0
            else 0
        )

        return {
            "total_time": total_time,
            "timings": avg_timings,
            "api_calls": self.metrics["api_calls"],
            "cache": {
                **self.metrics["cache"],
                "hit_rate": cache_hit_rate
            },
            "tokens": self.metrics["tokens"],
            "errors": self.metrics["errors"],
            "error_count": len(self.metrics["errors"])
        }


class ContextFilter(logging.Filter):
    """
    Logging filter that adds request context to log records.

    Adds claim_id and request_id to all log messages for tracing.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add context fields to the log record.

        Args:
            record: Log record to modify

        Returns:
            Always True to allow the record through
        """
        record.claim_id = getattr(_thread_local, "claim_id", "-")
        record.request_id = getattr(_thread_local, "request_id", "-")
        return True


def setup_logging(
    level: str = "INFO",
    log_dir: str | None = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """
    Configure logging for the entire application.

    This should be called once at application startup.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files (default: logs/)
        enable_console: Whether to log to console
        enable_file: Whether to log to file

    Example:
        >>> setup_logging(level="DEBUG", log_dir="logs")
    """
    # Create logs directory
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | "
            "req:%(request_id)s | claim:%(claim_id)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

    # Add file handler with rotation by date
    if enable_file:
        log_file = log_dir / f"veritasloop_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)

    # Set specific log levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("anthropic").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


def set_request_context(claim_id: str, request_id: str) -> None:
    """
    Set request context for current thread.

    This context will be added to all log messages in this thread.

    Args:
        claim_id: Unique identifier for the claim being processed
        request_id: Unique identifier for this request/session

    Example:
        >>> set_request_context("claim_abc123", "req_xyz789")
    """
    _thread_local.claim_id = claim_id
    _thread_local.request_id = request_id


def clear_request_context() -> None:
    """Clear request context for current thread."""
    _thread_local.claim_id = None
    _thread_local.request_id = None


def get_metrics() -> PerformanceMetrics | None:
    """
    Get performance metrics for current request.

    Returns:
        PerformanceMetrics instance or None if not initialized
    """
    return getattr(_thread_local, "metrics", None)


def init_metrics() -> PerformanceMetrics:
    """
    Initialize performance metrics for current request.

    Returns:
        New PerformanceMetrics instance
    """
    metrics = PerformanceMetrics()
    _thread_local.metrics = metrics
    return metrics


@contextmanager
def log_performance(operation: str, logger: logging.Logger | None = None):
    """
    Context manager to log operation performance.

    Automatically tracks execution time and logs start/end.

    Args:
        operation: Name of the operation being tracked
        logger: Optional logger instance (creates one if not provided)

    Yields:
        None

    Example:
        >>> with log_performance("claim_extraction"):
        ...     result = extract_claim(text)
    """
    if logger is None:
        logger = get_logger("performance")

    logger.debug(f"Starting: {operation}")
    start_time = time.time()

    try:
        yield
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Failed: {operation} (duration: {duration:.2f}s)",
            exc_info=True
        )

        # Record error in metrics
        metrics = get_metrics()
        if metrics:
            metrics.add_error(operation, str(e))

        raise
    else:
        duration = time.time() - start_time
        logger.info(f"Completed: {operation} (duration: {duration:.2f}s)")

        # Record timing in metrics
        metrics = get_metrics()
        if metrics:
            metrics.add_timing(operation, duration)


def log_metrics_summary(logger: logging.Logger | None = None) -> dict[str, Any]:
    """
    Log and return performance metrics summary.

    Args:
        logger: Optional logger instance

    Returns:
        Metrics summary dictionary

    Example:
        >>> summary = log_metrics_summary()
        >>> print(f"Total time: {summary['total_time']:.2f}s")
    """
    if logger is None:
        logger = get_logger("metrics")

    metrics = get_metrics()
    if not metrics:
        logger.warning("No metrics available")
        return {}

    summary = metrics.get_summary()

    logger.info("=" * 60)
    logger.info("PERFORMANCE METRICS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Processing Time: {summary['total_time']:.2f}s")

    if summary['timings']:
        logger.info("\nOperation Timings:")
        for op, stats in summary['timings'].items():
            logger.info(
                f"  {op}: avg={stats['avg']:.2f}s, "
                f"min={stats['min']:.2f}s, max={stats['max']:.2f}s, "
                f"count={stats['count']}"
            )

    if summary['api_calls']:
        logger.info("\nAPI Calls:")
        for tool, count in summary['api_calls'].items():
            logger.info(f"  {tool}: {count}")

    cache = summary['cache']
    if cache['hits'] + cache['misses'] > 0:
        logger.info(
            f"\nCache Performance: {cache['hits']} hits, {cache['misses']} misses "
            f"({cache['hit_rate']:.1f}% hit rate)"
        )

    if summary['tokens']['total'] > 0:
        logger.info(f"\nToken Usage: {summary['tokens']['total']} total")
        for agent, count in summary['tokens']['by_agent'].items():
            logger.info(f"  {agent}: {count}")

    if summary['errors']:
        logger.warning(f"\nErrors: {summary['error_count']}")
        for error in summary['errors']:
            logger.warning(f"  [{error['type']}] {error['message']}")

    logger.info("=" * 60)

    return summary


def save_metrics_to_file(
    output_path: str,
    metadata: dict[str, Any] | None = None
) -> None:
    """
    Save metrics summary to JSON file.

    Args:
        output_path: Path to output JSON file
        metadata: Optional additional metadata to include

    Example:
        >>> save_metrics_to_file("metrics.json", {"claim": "some claim"})
    """
    metrics = get_metrics()
    if not metrics:
        return

    summary = metrics.get_summary()

    output = {
        "timestamp": datetime.now().isoformat(),
        "metrics": summary
    }

    if metadata:
        output["metadata"] = metadata

    with Path(output_path).open('w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
