"""
Tests for Phoenix tracing integration.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


def test_enable_tracing_success():
    """Test that tracing can be enabled successfully."""
    from src.orchestrator.graph import enable_tracing

    # Mock the Phoenix imports inside the function
    with patch("phoenix.otel.register") as mock_register, \
         patch("openinference.instrumentation.langchain.LangChainInstrumentor") as mock_instrumentor:

        # Setup mocks
        mock_tracer_provider = MagicMock()
        mock_register.return_value = mock_tracer_provider
        mock_instrumentor_instance = MagicMock()
        mock_instrumentor.return_value = mock_instrumentor_instance

        # Call enable_tracing
        result = enable_tracing()

        # Verify it was called correctly
        assert result is True
        mock_register.assert_called_once_with(
            project_name="veritasloop",
            endpoint="http://localhost:6006/v1/traces"
        )
        mock_instrumentor_instance.instrument.assert_called_once_with(
            tracer_provider=mock_tracer_provider
        )


def test_enable_tracing_import_error():
    """Test that tracing gracefully handles missing dependencies."""
    from src.orchestrator.graph import enable_tracing

    # Mock ImportError when trying to import phoenix.otel
    with patch("builtins.__import__", side_effect=ImportError("phoenix not found")):
        result = enable_tracing()

        # Should return False but not crash
        assert result is False


def test_enable_tracing_general_error():
    """Test that tracing gracefully handles unexpected errors."""
    from src.orchestrator.graph import enable_tracing

    # Mock a generic exception during register
    with patch("phoenix.otel.register", side_effect=Exception("Unexpected error")):
        result = enable_tracing()

        # Should return False but not crash
        assert result is False


def test_graph_runs_without_tracing():
    """Test that the graph works normally without tracing enabled."""
    from src.orchestrator.graph import get_app

    # Get the app without enabling tracing
    app = get_app()

    # Verify it compiles and returns a valid graph
    assert app is not None
    # The app should be a compiled graph
    assert hasattr(app, 'invoke')


def test_start_phoenix_server_import_error(capsys):
    """Test that Phoenix server start handles missing dependencies gracefully."""
    # We need to reload src.cli to get fresh imports for this test
    # The capsys fixture will handle stdout/stderr properly
    import importlib
    if 'src.cli' in sys.modules:
        importlib.reload(sys.modules['src.cli'])

    from src.cli import start_phoenix_server

    # Mock ImportError when trying to import phoenix
    with patch("builtins.__import__", side_effect=ImportError("phoenix not found")):
        result = start_phoenix_server(verbose=False)

        # Should return None but not crash
        assert result is None


def test_start_phoenix_server_success(capsys):
    """Test that Phoenix server can be started successfully."""
    import importlib
    if 'src.cli' in sys.modules:
        importlib.reload(sys.modules['src.cli'])

    from src.cli import start_phoenix_server

    # Mock phoenix module and its functions
    mock_px = MagicMock()
    mock_session = MagicMock()
    mock_px.launch_app.return_value = mock_session

    # Mock Path.mkdir to avoid creating actual directories
    with patch("src.cli.check_phoenix_running", return_value=False), \
         patch.dict("sys.modules", {"phoenix": mock_px}), \
         patch("pathlib.Path.mkdir"):

        result = start_phoenix_server(verbose=False)

        # Should return the session
        assert result == mock_session
        mock_px.launch_app.assert_called_once()


def test_start_phoenix_server_already_running(capsys):
    """Test that start_phoenix_server detects existing Phoenix instance."""
    import importlib
    if 'src.cli' in sys.modules:
        importlib.reload(sys.modules['src.cli'])

    from src.cli import start_phoenix_server

    # Mock that Phoenix is already running
    with patch("src.cli.check_phoenix_running", return_value=True):
        result = start_phoenix_server(verbose=False)

        # Should return True indicating Phoenix is available
        assert result is True


def test_cli_trace_flag_integration(capsys):
    """Test that the CLI accepts and processes the --trace flag."""
    import importlib
    if 'src.cli' in sys.modules:
        importlib.reload(sys.modules['src.cli'])

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
