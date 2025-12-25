"""
Unit tests for the logging module.

Tests cover:
- Logger initialization and configuration
- Performance metrics tracking
- Context management
- Log performance decorator
"""

import logging
import tempfile
import time
from pathlib import Path

import pytest

from src.utils.logger import (
    PerformanceMetrics,
    clear_request_context,
    get_logger,
    get_metrics,
    init_metrics,
    log_metrics_summary,
    log_performance,
    save_metrics_to_file,
    set_request_context,
    setup_logging,
)


@pytest.fixture(autouse=True)
def cleanup_logging_handlers():
    """Cleanup all logging handlers after each test to prevent file locking on Windows."""
    yield
    # Close and remove all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics class."""

    def test_init_metrics(self):
        """Test metrics initialization."""
        metrics = PerformanceMetrics()

        assert metrics.metrics["timings"] == {}
        assert metrics.metrics["api_calls"] == {}
        assert metrics.metrics["cache"]["hits"] == 0
        assert metrics.metrics["cache"]["misses"] == 0
        assert metrics.metrics["tokens"]["total"] == 0
        assert metrics.metrics["errors"] == []

    def test_add_timing(self):
        """Test adding timing measurements."""
        metrics = PerformanceMetrics()

        metrics.add_timing("operation1", 1.5)
        metrics.add_timing("operation1", 2.0)
        metrics.add_timing("operation2", 0.5)

        assert len(metrics.metrics["timings"]["operation1"]) == 2
        assert metrics.metrics["timings"]["operation1"] == [1.5, 2.0]
        assert metrics.metrics["timings"]["operation2"] == [0.5]

    def test_add_api_call(self):
        """Test API call counting."""
        metrics = PerformanceMetrics()

        metrics.add_api_call("brave_search")
        metrics.add_api_call("brave_search")
        metrics.add_api_call("news_api")

        assert metrics.metrics["api_calls"]["brave_search"] == 2
        assert metrics.metrics["api_calls"]["news_api"] == 1

    def test_cache_tracking(self):
        """Test cache hit/miss tracking."""
        metrics = PerformanceMetrics()

        metrics.add_cache_hit()
        metrics.add_cache_hit()
        metrics.add_cache_miss()

        assert metrics.metrics["cache"]["hits"] == 2
        assert metrics.metrics["cache"]["misses"] == 1

    def test_token_tracking(self):
        """Test token usage tracking."""
        metrics = PerformanceMetrics()

        metrics.add_tokens("PRO", 100)
        metrics.add_tokens("CONTRA", 150)
        metrics.add_tokens("PRO", 50)

        assert metrics.metrics["tokens"]["total"] == 300
        assert metrics.metrics["tokens"]["by_agent"]["PRO"] == 150
        assert metrics.metrics["tokens"]["by_agent"]["CONTRA"] == 150

    def test_error_tracking(self):
        """Test error recording."""
        metrics = PerformanceMetrics()

        metrics.add_error("search_error", "API timeout")
        metrics.add_error("llm_error", "Rate limit exceeded")

        assert len(metrics.metrics["errors"]) == 2
        assert metrics.metrics["errors"][0]["type"] == "search_error"
        assert metrics.metrics["errors"][1]["message"] == "Rate limit exceeded"

    def test_get_summary(self):
        """Test metrics summary generation."""
        metrics = PerformanceMetrics()

        # Add some data
        metrics.add_timing("op1", 1.0)
        metrics.add_timing("op1", 2.0)
        metrics.add_api_call("brave")
        metrics.add_cache_hit()
        metrics.add_cache_miss()
        metrics.add_tokens("PRO", 100)

        summary = metrics.get_summary()

        assert "total_time" in summary
        assert "timings" in summary
        assert summary["timings"]["op1"]["avg"] == 1.5
        assert summary["timings"]["op1"]["min"] == 1.0
        assert summary["timings"]["op1"]["max"] == 2.0
        assert summary["api_calls"]["brave"] == 1
        assert summary["cache"]["hit_rate"] == 50.0  # 1 hit, 1 miss
        assert summary["tokens"]["total"] == 100


class TestLoggingSetup:
    """Test cases for logging setup and configuration."""

    def test_setup_logging_creates_log_dir(self):
        """Test that setup_logging creates the log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "test_logs"

            setup_logging(log_dir=str(log_dir), enable_console=False, enable_file=False)

            assert log_dir.exists()
            assert log_dir.is_dir()

    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_logger_levels(self):
        """Test logger respects level configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(level="WARNING", log_dir=tmpdir, enable_console=False, enable_file=False)
            logger = get_logger("test")

            # WARNING level should be enabled
            assert logger.isEnabledFor(logging.WARNING)
            # INFO level should be disabled
            assert not logger.isEnabledFor(logging.DEBUG)


class TestRequestContext:
    """Test cases for request context management."""

    def test_set_request_context(self):
        """Test setting request context."""
        set_request_context(claim_id="claim_123", request_id="req_456")
        # Context is thread-local, so we can't directly assert values
        # but we can verify it doesn't raise errors
        clear_request_context()

    def test_clear_request_context(self):
        """Test clearing request context."""
        set_request_context(claim_id="claim_123", request_id="req_456")
        clear_request_context()
        # Should not raise any errors


class TestMetricsManagement:
    """Test cases for metrics management."""

    def test_init_and_get_metrics(self):
        """Test metrics initialization and retrieval."""
        metrics = init_metrics()

        assert metrics is not None
        assert isinstance(metrics, PerformanceMetrics)

        # Get the same metrics instance
        retrieved_metrics = get_metrics()
        assert retrieved_metrics is metrics

    def test_metrics_thread_local(self):
        """Test that metrics are thread-local."""
        metrics1 = init_metrics()
        metrics1.add_api_call("test")

        # Same thread should get same instance
        metrics2 = get_metrics()
        assert metrics2 is metrics1
        assert metrics2.metrics["api_calls"]["test"] == 1


class TestLogPerformance:
    """Test cases for log_performance context manager."""

    def test_log_performance_basic(self):
        """Test basic performance logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=tmpdir, enable_console=False, enable_file=False)
            logger = get_logger("test")
            metrics = init_metrics()

            with log_performance("test_operation", logger):
                time.sleep(0.1)  # Simulate some work

            # Check that timing was recorded
            assert "test_operation" in metrics.metrics["timings"]
            assert len(metrics.metrics["timings"]["test_operation"]) == 1
            assert metrics.metrics["timings"]["test_operation"][0] >= 0.1

    def test_log_performance_with_error(self):
        """Test performance logging when operation fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=tmpdir, enable_console=False, enable_file=False)
            logger = get_logger("test")
            metrics = init_metrics()

            with pytest.raises(ValueError):
                with log_performance("failing_operation", logger):
                    raise ValueError("Test error")

            # Error should be recorded in metrics
            assert len(metrics.metrics["errors"]) == 1
            assert metrics.metrics["errors"][0]["type"] == "failing_operation"

    def test_log_performance_multiple_operations(self):
        """Test logging multiple operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=tmpdir, enable_console=False, enable_file=False)
            logger = get_logger("test")
            metrics = init_metrics()

            with log_performance("op1", logger):
                time.sleep(0.05)

            with log_performance("op2", logger):
                time.sleep(0.05)

            with log_performance("op1", logger):
                time.sleep(0.05)

            # Check both operations were tracked
            assert "op1" in metrics.metrics["timings"]
            assert "op2" in metrics.metrics["timings"]
            assert len(metrics.metrics["timings"]["op1"]) == 2
            assert len(metrics.metrics["timings"]["op2"]) == 1


class TestMetricsSummaryAndExport:
    """Test cases for metrics summary and export."""

    def test_log_metrics_summary(self):
        """Test metrics summary logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=tmpdir, enable_console=False, enable_file=False)
            logger = get_logger("test")
            metrics = init_metrics()

            # Add some test data
            metrics.add_timing("op1", 1.0)
            metrics.add_api_call("brave")
            metrics.add_cache_hit()

            summary = log_metrics_summary(logger)

            assert summary is not None
            assert "total_time" in summary
            assert "timings" in summary
            assert "api_calls" in summary
            assert "cache" in summary

    def test_save_metrics_to_file(self):
        """Test saving metrics to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=tmpdir, enable_console=False, enable_file=False)
            metrics = init_metrics()

            # Add some test data
            metrics.add_timing("test_op", 2.5)
            metrics.add_api_call("test_api")

            output_file = Path(tmpdir) / "test_metrics.json"
            save_metrics_to_file(
                str(output_file),
                metadata={"test": "data"}
            )

            # Verify file was created
            assert output_file.exists()

            # Verify content
            import json
            with open(output_file) as f:
                data = json.load(f)

            assert "timestamp" in data
            assert "metrics" in data
            assert "metadata" in data
            assert data["metadata"]["test"] == "data"
            assert data["metrics"]["timings"]["test_op"]["avg"] == 2.5


class TestLoggingIntegration:
    """Integration tests for the logging system."""

    def test_full_logging_workflow(self):
        """Test complete logging workflow from setup to export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            setup_logging(level="INFO", log_dir=tmpdir, enable_console=False, enable_file=False)
            logger = get_logger("integration_test")

            # Initialize metrics and context
            metrics = init_metrics()
            set_request_context(claim_id="test_claim", request_id="test_req")

            # Simulate some work with performance tracking
            with log_performance("claim_extraction", logger):
                time.sleep(0.05)

            with log_performance("pro_research", logger):
                metrics.add_api_call("brave_search")
                metrics.add_cache_miss()
                time.sleep(0.05)

            with log_performance("contra_research", logger):
                metrics.add_api_call("brave_search")
                metrics.add_cache_hit()
                time.sleep(0.05)

            # Log summary
            summary = log_metrics_summary(logger)

            # Verify summary
            assert summary["timings"]["claim_extraction"]["count"] == 1
            assert summary["timings"]["pro_research"]["count"] == 1
            assert summary["api_calls"]["brave_search"] == 2
            assert summary["cache"]["hits"] == 1
            assert summary["cache"]["misses"] == 1

            # Export metrics
            output_file = Path(tmpdir) / "integration_metrics.json"
            save_metrics_to_file(str(output_file))

            assert output_file.exists()

            # Clean up context
            clear_request_context()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
