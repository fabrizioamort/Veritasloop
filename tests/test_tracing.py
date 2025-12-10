"""
Tests for Phoenix tracing integration.
"""

import pytest
from unittest.mock import patch, MagicMock


def test_enable_tracing_success():
    """Test that tracing can be enabled successfully."""
    from src.orchestrator.graph import enable_tracing

    # Mock the Phoenix imports
    with patch("src.orchestrator.graph.register") as mock_register, \
         patch("src.orchestrator.graph.LangChainInstrumentor") as mock_instrumentor:

        # Setup mocks
        mock_tracer_provider = MagicMock()
        mock_register.return_value = mock_tracer_provider
        mock_instrumentor_instance = MagicMock()
        mock_instrumentor.return_value = mock_instrumentor_instance

        # Call enable_tracing
        result = enable_tracing()

        # Verify it was called correctly
        assert result is True
        mock_register.assert_called_once()
        mock_instrumentor_instance.instrument.assert_called_once_with(
            tracer_provider=mock_tracer_provider
        )


def test_enable_tracing_import_error():
    """Test that tracing gracefully handles missing dependencies."""
    from src.orchestrator.graph import enable_tracing

    # Mock ImportError
    with patch("src.orchestrator.graph.register", side_effect=ImportError("phoenix not found")):
        result = enable_tracing()

        # Should return False but not crash
        assert result is False


def test_enable_tracing_general_error():
    """Test that tracing gracefully handles unexpected errors."""
    from src.orchestrator.graph import enable_tracing

    # Mock a generic exception
    with patch("src.orchestrator.graph.register", side_effect=Exception("Unexpected error")):
        result = enable_tracing()

        # Should return False but not crash
        assert result is False


def test_graph_runs_without_tracing():
    """Test that the graph works normally without tracing enabled."""
    from src.orchestrator.graph import get_app
    from src.models.schemas import Claim, Entities

    # Get the app without enabling tracing
    app = get_app()

    # Verify it compiles and returns a valid graph
    assert app is not None
    # The app should be a compiled graph
    assert hasattr(app, 'invoke')


def test_start_phoenix_server_import_error():
    """Test that Phoenix server start handles missing dependencies gracefully."""
    from src.cli import start_phoenix_server

    # Mock ImportError
    with patch("src.cli.px", side_effect=ImportError("phoenix not found")):
        result = start_phoenix_server(verbose=False)

        # Should return None but not crash
        assert result is None


def test_start_phoenix_server_success():
    """Test that Phoenix server can be started successfully."""
    from src.cli import start_phoenix_server

    # Mock phoenix
    with patch("src.cli.px") as mock_px:
        mock_session = MagicMock()
        mock_px.launch_app.return_value = mock_session

        result = start_phoenix_server(verbose=False)

        # Should return the session
        assert result == mock_session
        mock_px.launch_app.assert_called_once()


def test_cli_trace_flag_integration():
    """Test that the CLI accepts and processes the --trace flag."""
    import sys
    from unittest.mock import patch

    # Mock the verification function and Phoenix
    with patch("src.cli.run_verification") as mock_run, \
         patch("src.cli.setup_logging"), \
         patch("src.cli.get_logger"), \
         patch("src.cli.print_banner"):

        # Simulate CLI args with --trace
        test_args = [
            "src.cli",
            "--input", "Test claim",
            "--trace",
            "--no-banner"
        ]

        with patch.object(sys, "argv", test_args):
            try:
                from src.cli import main
                main()
            except SystemExit:
                pass  # Expected after completion

            # Verify run_verification was called with enable_trace=True
            assert mock_run.called
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs.get("enable_trace") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
