#!/usr/bin/env python3
"""
VeritasLoop Command-Line Interface.
Provides a user-friendly CLI for verifying news claims through adversarial agent debate.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure UTF-8 encoding for stdout on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.models.schemas import Claim, Entities, VerdictType
from src.orchestrator.graph import enable_tracing, get_app
from src.utils.claim_extractor import extract_from_url
from src.utils.logger import (
    get_logger,
    init_metrics,
    log_metrics_summary,
    save_metrics_to_file,
    set_request_context,
    setup_logging,
)

logger = get_logger(__name__)

# Global Phoenix session tracker
_phoenix_session = None


def print_banner():
    """Prints the VeritasLoop ASCII art banner."""
    # Try to print Unicode banner, fall back to ASCII if needed
    try:
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  ██╗   ██╗███████╗██████╗ ██╗████████╗ █████╗ ███████╗       ║
║  ██║   ██║██╔════╝██╔══██╗██║╚══██╔══╝██╔══██╗██╔════╝       ║
║  ██║   ██║█████╗  ██████╔╝██║   ██║   ███████║███████╗       ║
║  ╚██╗ ██╔╝██╔══╝  ██╔══██╗██║   ██║   ██╔══██║╚════██║       ║
║   ╚████╔╝ ███████╗██║  ██║██║   ██║   ██║  ██║███████║       ║
║    ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝       ║
║                                                               ║
║              L  O  O  P                                       ║
║                                                               ║
║          Multi-Agent News Verification System                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        print(banner)
    except UnicodeEncodeError:
        # Fallback to simple ASCII banner
        banner = """
===============================================================
                    VERITASLOOP
          Multi-Agent News Verification System
===============================================================
"""
        print(banner)


def print_progress(message: str, verbose: bool = False):
    """
    Prints a progress message to stdout.

    Args:
        message: The message to print.
        verbose: If True, print the message. Otherwise skip.
    """
    if verbose:
        print(f"  → {message}")


def print_verdict(result: dict, verbose: bool = False):
    """
    Pretty-prints the final verdict in a formatted way.

    Args:
        result: The result dictionary from the graph execution.
        verbose: If True, also print the debate transcript.
    """
    verdict_data = result.get("verdict")

    if not verdict_data:
        print("\n⚠️  No verdict was generated. The verification may have failed.")
        return

    # Extract verdict information
    verdict_type = verdict_data.get("verdict", "UNKNOWN")
    confidence = verdict_data.get("confidence_score", 0)
    summary = verdict_data.get("summary", "No summary available.")
    sources_used = verdict_data.get("sources_used", [])
    metadata = verdict_data.get("metadata", {})

    # Color-coded verdict display
    verdict_colors = {
        VerdictType.VERO.value: "✅",
        VerdictType.FALSO.value: "❌",
        VerdictType.PARZIALMENTE_VERO.value: "⚠️",
        VerdictType.CONTESTO_MANCANTE.value: "⚡",
        VerdictType.NON_VERIFICABILE.value: "❓",
    }

    icon = verdict_colors.get(verdict_type, "❔")

    # Print formatted verdict
    print("\n" + "═" * 65)
    print(f"{icon}  VERDETTO: {verdict_type}")
    print(f"   Confidenza: {confidence:.0f}%")
    print("═" * 65)

    print(f"\n📝 Sintesi:\n{summary}\n")

    # Print main sources
    if sources_used:
        print("📚 Fonti Principali:")
        for i, source in enumerate(sources_used[:5], 1):  # Show top 5 sources
            url = source.get("url", "N/A")
            reliability = source.get("reliability", "unknown")
            title = source.get("title", "No title")

            # Truncate long titles
            if len(title) > 70:
                title = title[:67] + "..."

            reliability_display = {
                "high": "Alta 🟢",
                "medium": "Media 🟡",
                "low": "Bassa 🔴"
            }.get(reliability, "Sconosciuta ⚪")

            print(f"  [{i}] {title}")
            print(f"      {url}")
            print(f"      Affidabilità: {reliability_display}\n")

    # Print metadata
    if metadata:
        print("📊 Statistiche:")
        processing_time = metadata.get("processing_time_seconds", 0)
        rounds = metadata.get("rounds_completed", 0)
        total_sources = metadata.get("total_sources_checked", 0)

        print(f"  ⏱️  Tempo di elaborazione: {processing_time:.1f} secondi")
        print(f"  🔄 Round di dibattito: {rounds}")
        print(f"  📖 Fonti totali verificate: {total_sources}")

    print("\n" + "═" * 65 + "\n")

    # Print debate transcript if verbose
    if verbose:
        messages = result.get("messages", [])
        if messages:
            print("\n📜 TRASCRIZIONE DIBATTITO\n")
            print("-" * 65)

            for msg in messages:
                agent = msg.agent
                content = msg.content
                round_num = msg.round
                msg_type = msg.message_type

                agent_icon = {
                    "PRO": "🛡️",
                    "CONTRA": "🔍",
                    "JUDGE": "⚖️"
                }.get(agent, "💬")

                print(f"\n{agent_icon} {agent} - Round {round_num} ({msg_type})")
                print(f"{content}\n")

                if msg.sources:
                    print(f"   Fonti citate ({len(msg.sources)}):")
                    for src in msg.sources[:3]:  # Show first 3 sources
                        print(f"   - {src.url}")

            print("-" * 65 + "\n")


def save_to_json(result: dict, output_path: str):
    """
    Saves the full result to a JSON file.

    Args:
        result: The result dictionary from the graph execution.
        output_path: Path to the output JSON file.
    """
    try:
        output_file = Path(output_path)

        # Convert any Pydantic models to dicts for JSON serialization
        serializable_result = {}

        # Handle claim
        if "claim" in result and result["claim"]:
            claim = result["claim"]
            serializable_result["claim"] = {
                "id": str(claim.id),
                "raw_input": claim.raw_input,
                "core_claim": claim.core_claim,
                "category": claim.category,
                "entities": {
                    "people": claim.entities.people,
                    "places": claim.entities.places,
                    "dates": claim.entities.dates,
                    "organizations": claim.entities.organizations,
                }
            }

        # Handle messages
        if "messages" in result:
            serializable_result["messages"] = []
            for msg in result["messages"]:
                serializable_result["messages"].append({
                    "round": msg.round,
                    "agent": msg.agent,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "confidence": msg.confidence,
                    "sources": [
                        {
                            "url": str(src.url),
                            "title": src.title,
                            "snippet": src.snippet,
                            "reliability": src.reliability,
                            "timestamp": src.timestamp.isoformat() if src.timestamp else None,
                            "agent": src.agent,
                            "relevance_score": src.relevance_score,
                        }
                        for src in msg.sources
                    ]
                })

        # Copy verdict directly (already a dict)
        if "verdict" in result:
            serializable_result["verdict"] = result["verdict"]

        # Copy other fields
        for key in ["pro_sources", "contra_sources", "round_count"]:
            if key in result:
                serializable_result[key] = result[key]

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(serializable_result, f, indent=2, ensure_ascii=False, default=str)

        print(f"✅ Risultato salvato in: {output_file.absolute()}")
    except Exception as e:
        print(f"❌ Errore nel salvare il file JSON: {e}", file=sys.stderr)


def check_phoenix_running() -> bool:
    """
    Check if Phoenix server is already running on port 6006.

    Returns:
        True if Phoenix is accessible, False otherwise
    """
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 6006))
        sock.close()
        return result == 0
    except Exception:
        return False


def start_phoenix_server(verbose: bool = False):
    """
    Starts the Phoenix server for tracing visualization with persistent storage.
    Traces are saved to a SQLite database and persist across server restarts.
    If Phoenix is already running, connects to the existing instance.

    Args:
        verbose: If True, print status messages

    Returns:
        Phoenix session object or True if already running, None if failed
    """
    global _phoenix_session

    # Check if Phoenix is already running
    if check_phoenix_running():
        if verbose:
            print("\n🔭 Phoenix server already running!")
            print("   View traces at: http://localhost:6006")
            print("   Using existing Phoenix instance\n")
        logger.info("Phoenix server already running on port 6006")
        return True  # Return True to indicate Phoenix is available

    try:
        from pathlib import Path

        import phoenix as px

        # Create a directory for Phoenix data
        phoenix_dir = Path("data/phoenix")
        phoenix_dir.mkdir(parents=True, exist_ok=True)

        # Database file for persistent traces
        db_path = phoenix_dir / "traces.db"

        # Launch Phoenix server with persistent storage
        # Using run_in_background=True keeps the server running after script exits
        # Using database stores traces permanently
        _phoenix_session = px.launch_app(
            run_in_background=True,
            database_url=f"sqlite:///{db_path.absolute()}"
        )

        url = "http://localhost:6006"

        if verbose:
            print("\n🔭 Phoenix observability enabled!")
            print(f"   View traces at: {url}")
            print(f"   💾 Traces saved to: {db_path.absolute()}")
            print("   📌 Traces persist across server restarts")
            print(f"   💡 Review past sessions anytime at {url}\n")

        logger.info(f"Phoenix server started at {url} with persistent storage at {db_path}")
        return _phoenix_session

    except ImportError:
        logger.warning("Phoenix not available. Install with: pip install arize-phoenix")
        if verbose:
            print("\n⚠️  Phoenix tracing not available. Install with:")
            print("   pip install arize-phoenix openinference-instrumentation-langchain\n")
        return None
    except Exception as e:
        logger.error(f"Failed to start Phoenix server: {e}")
        if verbose:
            print(f"\n⚠️  Could not start Phoenix server: {e}\n")
        return None


def run_verification(
    input_text: str,
    verbose: bool = False,
    no_cache: bool = False,
    output_path: str | None = None,
    enable_trace: bool = False,
    max_iterations: int = 3,
    max_searches: int = -1
) -> dict:
    """
    Runs the full verification pipeline.

    Args:
        input_text: The claim text or URL to verify.
        verbose: If True, show detailed progress and debate transcript.
        no_cache: If True, disable caching (not implemented yet).
        output_path: If provided, save the result to this JSON file.
        enable_trace: If True, enable Phoenix tracing for observability.
        max_iterations: Maximum number of debate rounds (default: 3).
        max_searches: Maximum number of searches per agent (default: unlimited).

    Returns:
        The final state dictionary from the graph execution.
    """
    start_time = time.time()

    # Initialize performance metrics
    metrics = init_metrics()

    # Enable Phoenix tracing if requested
    if enable_trace:
        # Start Phoenix server
        phoenix_started = start_phoenix_server(verbose=True)
        # Only enable tracing if Phoenix actually started
        if phoenix_started:
            enable_tracing()
        else:
            logger.warning("Phoenix server failed to start, tracing disabled")
            if verbose:
                print("⚠️  Tracing disabled - Phoenix server not available\n")

    # Determine if input is a URL or text
    is_url = input_text.startswith("http://") or input_text.startswith("https://")

    if verbose:
        input_type = "URL" if is_url else "testo"
        print(f"\n🔍 Input ricevuto ({input_type}): {input_text[:100]}{'...' if len(input_text) > 100 else ''}\n")

    logger.info(
        f"Starting verification for {'URL' if is_url else 'text'} input",
        extra={"input_length": len(input_text), "is_url": is_url}
    )

    # Step 1: Extract claim
    print_progress("Estrazione della notizia in corso...", True)

    try:
        if is_url:
            logger.debug(f"Extracting claim from URL: {input_text}")
            claim = extract_from_url(input_text)
        else:
            # Create a basic claim object - the graph will extract the core claim
            claim = Claim(
                raw_input=input_text,
                core_claim=input_text,  # Will be refined by extract_claim node
                entities=Entities(),
            )
            logger.debug("Created basic claim from text input")

        # Set request context with claim ID
        set_request_context(claim_id=str(claim.id), request_id=f"req_{int(start_time)}")
        logger.info(f"Claim ID: {claim.id}")

    except Exception as e:
        logger.error(f"Failed to extract claim: {e}", exc_info=True)
        print(f"❌ Errore nell'estrazione della notizia: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Initialize the graph
    print_progress("Inizializzazione del sistema multi-agente...", verbose)

    try:
        logger.info("Initializing LangGraph application")
        app = get_app()
    except Exception as e:
        logger.error(f"Failed to initialize graph: {e}", exc_info=True)
        print(f"❌ Errore nell'inizializzazione del grafo: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Run the verification
    initial_state = {
        "claim": claim,
        "messages": [],
        "pro_sources": [],
        "contra_sources": [],
        "round_count": 0,
        "verdict": None,
        "max_iterations": max_iterations,
        "max_searches": max_searches,
    }

    print_progress("Avvio della verifica...\n", verbose)

    try:
        logger.info("Starting verification pipeline")
        result = app.invoke(initial_state)
        logger.info("Verification pipeline completed successfully")
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        print(f"❌ Errore durante la verifica: {e}", file=sys.stderr)
        import traceback
        if verbose:
            traceback.print_exc()
        sys.exit(1)

    # Step 4: Calculate processing time and log metrics
    end_time = time.time()
    processing_time = end_time - start_time

    # Update metadata if verdict exists
    if result.get("verdict"):
        if "metadata" not in result["verdict"]:
            result["verdict"]["metadata"] = {}
        result["verdict"]["metadata"]["processing_time_seconds"] = processing_time

        # Add performance metrics to metadata
        metrics_summary = log_metrics_summary(logger if verbose else None)
        if metrics_summary:
            result["verdict"]["metadata"]["performance"] = metrics_summary

    # Step 5: Display results
    print_verdict(result, verbose)

    # Step 6: Save to file if requested
    if output_path:
        save_to_json(result, output_path)

        # Also save detailed metrics
        if verbose:
            metrics_path = str(Path(output_path).with_suffix('.metrics.json'))
            save_metrics_to_file(
                metrics_path,
                metadata={
                    "claim_id": str(claim.id),
                    "input": input_text[:200],
                    "verdict": result.get("verdict", {}).get("verdict", "UNKNOWN")
                }
            )
            logger.info(f"Metrics saved to {metrics_path}")

    # Step 7: Remind user about Phoenix traces if enabled
    if enable_trace and _phoenix_session:
        print("\n" + "=" * 65)
        print("🔭 Phoenix Traces Available")
        print("=" * 65)
        print("   View detailed traces at: http://localhost:6006")
        print("   The Phoenix server is still running in the background.")
        print("   You can review all traces anytime at the URL above.")
        print("=" * 65 + "\n")

    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="VeritasLoop - Multi-Agent News Verification System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify a text claim
  python -m src.cli --input "L'ISTAT ha dichiarato che l'inflazione è al 5%%"

  # Verify a URL with verbose output
  python -m src.cli --input "https://www.ansa.it/..." --verbose

  # Save results to JSON file
  python -m src.cli --input "..." --output results.json

  # Enable Phoenix tracing for observability
  python -m src.cli --input "..." --trace

  # Disable caching (for testing)
  python -m src.cli --input "..." --no-cache
        """
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Claim text or URL to verify"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to save the verdict as JSON file"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress and debate transcript"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching for this verification"
    )

    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Skip the ASCII art banner"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--trace",
        action="store_true",
        help="Enable Phoenix tracing for observability (http://localhost:6006)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum number of debate rounds between PRO and CONTRA agents (default: 3)"
    )

    parser.add_argument(
        "--max-searches",
        type=int,
        default=-1,
        help="Maximum number of searches per agent. Use -1 for unlimited (default: -1)"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(
        level=log_level,
        enable_console=args.verbose or args.debug,
        enable_file=True
    )

    logger.info("=" * 60)
    logger.info("VeritasLoop CLI started")
    logger.info("=" * 60)

    # Print banner unless disabled
    if not args.no_banner:
        print_banner()

    # Run verification
    try:
        run_verification(
            input_text=args.input,
            verbose=args.verbose,
            no_cache=args.no_cache,
            output_path=args.output,
            enable_trace=args.trace,
            max_iterations=args.max_iterations,
            max_searches=args.max_searches,
        )
        logger.info("Verification completed successfully")
    except KeyboardInterrupt:
        logger.warning("Verification interrupted by user")
        print("\n\n⚠️  Verifica interrotta dall'utente.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Errore imprevisto: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
