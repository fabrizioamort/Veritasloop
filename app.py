"""
VeritasLoop - Streamlit Web Interface
Interactive UI for multi-agent news verification system.
"""

import streamlit as st
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from src.orchestrator.graph import get_app, enable_tracing
from src.models.schemas import Claim, Entities, GraphState
from src.utils.claim_extractor import extract_from_url
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global Phoenix session tracker
_phoenix_session = None

# Page configuration
st.set_page_config(
    page_title="VeritasLoop - News Verification",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .pro-message {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1976d2;
        margin-bottom: 0.5rem;
    }
    .contra-message {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f57c00;
        margin-bottom: 0.5rem;
    }
    .verdict-true {
        background-color: #c8e6c9;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #4caf50;
    }
    .verdict-false {
        background-color: #ffcdd2;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #f44336;
    }
    .verdict-partial {
        background-color: #fff9c4;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #fbc02d;
    }
    .verdict-context {
        background-color: #e1bee7;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #9c27b0;
    }
    .verdict-unknown {
        background-color: #e0e0e0;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #757575;
    }
    .source-link {
        font-size: 0.9rem;
        color: #1976d2;
    }
    .agent-header {
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'verification_result' not in st.session_state:
    st.session_state.verification_result = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'stream_updates' not in st.session_state:
    st.session_state.stream_updates = []

def get_verdict_color(verdict: str) -> str:
    """Return CSS class based on verdict type."""
    verdict_map = {
        "VERO": "verdict-true",
        "FALSO": "verdict-false",
        "PARZIALMENTE_VERO": "verdict-partial",
        "CONTESTO_MANCANTE": "verdict-context",
        "NON_VERIFICABILE": "verdict-unknown"
    }
    return verdict_map.get(verdict, "verdict-unknown")

def get_verdict_emoji(verdict: str) -> str:
    """Return emoji based on verdict type."""
    emoji_map = {
        "VERO": "✅",
        "FALSO": "❌",
        "PARZIALMENTE_VERO": "⚠️",
        "CONTESTO_MANCANTE": "🔍",
        "NON_VERIFICABILE": "❓"
    }
    return emoji_map.get(verdict, "❓")

def format_source(source: Dict[str, Any], index: int) -> str:
    """Format a source for display."""
    reliability_emoji = {
        "high": "🟢",
        "medium": "🟡",
        "low": "🔴"
    }

    reliability = source.get('reliability', 'unknown')
    emoji = reliability_emoji.get(reliability, "⚪")

    title = source.get('title', 'Untitled')
    url = source.get('url', '#')
    snippet = source.get('snippet', '')

    html = f"""
    <div style="margin-bottom: 0.5rem;">
        <span style="font-weight: bold;">[{index}]</span> {emoji}
        <a href="{url}" target="_blank" class="source-link">{title}</a>
    """

    if snippet:
        html += f'<br><span style="font-size: 0.85rem; color: #666;">{snippet[:150]}...</span>'

    html += "</div>"
    return html

def display_debate_message(message: Dict[str, Any], agent: str, container):
    """Display a debate message in the appropriate column."""
    with container:
        if agent == "PRO":
            st.markdown(f'<div class="pro-message">', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="contra-message">', unsafe_allow_html=True)

        st.markdown(f"**Round {message.get('round', '?')}** - {message.get('message_type', 'argument').upper()}")
        st.write(message.get('content', ''))

        # Display sources
        sources = message.get('sources', [])
        if sources:
            with st.expander(f"📚 Fonti ({len(sources)})"):
                for i, source in enumerate(sources, 1):
                    st.markdown(format_source(source, i), unsafe_allow_html=True)

        # Display confidence
        confidence = message.get('confidence', 0)
        st.progress(confidence / 100, text=f"Confidenza: {confidence}%")

        st.markdown('</div>', unsafe_allow_html=True)

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


def start_phoenix_server() -> Optional[any]:
    """
    Starts the Phoenix server for tracing visualization with persistent storage.
    Traces are saved to a SQLite database and persist across server restarts.
    If Phoenix is already running, connects to the existing instance.

    Returns:
        Phoenix session object or True if already running, None if failed
    """
    global _phoenix_session

    # Check if Phoenix is already running
    if check_phoenix_running():
        st.success("🔭 Phoenix server already running at http://localhost:6006")
        logger.info("Phoenix server already running on port 6006")
        return True

    try:
        import phoenix as px

        # Create a directory for Phoenix data
        phoenix_dir = Path("data/phoenix")
        phoenix_dir.mkdir(parents=True, exist_ok=True)

        # Database file for persistent traces
        db_path = phoenix_dir / "traces.db"

        # Launch Phoenix server with persistent storage
        _phoenix_session = px.launch_app(
            run_in_background=True,
            database_url=f"sqlite:///{db_path.absolute()}"
        )

        st.success(f"🔭 Phoenix server started! View traces at http://localhost:6006")
        st.info(f"💾 Traces saved to: {db_path.absolute()}")
        logger.info(f"Phoenix server started at http://localhost:6006 with persistent storage at {db_path}")
        return _phoenix_session

    except ImportError:
        logger.warning("Phoenix not available. Install with: pip install arize-phoenix")
        st.error("⚠️ Phoenix not available. Install with: `pip install arize-phoenix openinference-instrumentation-langchain`")
        return None
    except Exception as e:
        logger.error(f"Failed to start Phoenix server: {e}")
        st.error(f"⚠️ Could not start Phoenix server: {e}")
        return None


def run_verification(user_input: str, input_type: str, enable_trace: bool = False, max_iterations: int = 3, max_searches: int = -1):
    """Run the verification process with streaming updates."""
    try:
        # Enable tracing if requested
        if enable_trace:
            # First, start Phoenix server if not running
            phoenix_started = start_phoenix_server()

            if phoenix_started:
                # Then enable tracing instrumentation
                enable_tracing()
                st.info("🔍 Tracing enabled. View at http://localhost:6006")
            else:
                st.warning("⚠️ Tracing requested but Phoenix could not start. Continuing without tracing.")
                # Continue without tracing

        # Extract claim
        if input_type == "URL":
            st.info(f"📄 Extracting content from URL...")
            claim = extract_from_url(user_input)
        else:
            claim = Claim(
                raw_input=user_input,
                core_claim=user_input,
                entities=Entities()
            )

        # Initialize state
        initial_state: GraphState = {
            "claim": claim,
            "messages": [],
            "pro_sources": [],
            "contra_sources": [],
            "round_count": 0,
            "max_iterations": max_iterations,
            "max_searches": max_searches
        }

        # Get the app
        app = get_app()

        # Create containers for streaming updates
        status_container = st.empty()
        pro_container = st.container()
        contra_container = st.container()
        center_container = st.container()

        # Stream the graph execution
        final_state = None
        for update in app.stream(initial_state):
            # Process each node update
            node_name = list(update.keys())[0]
            node_data = update[node_name]

            if node_name == "extract":
                status_container.info("🔍 Extracting core claim...")
                if 'claim' in node_data:
                    st.session_state.extracted_claim = node_data['claim']

            elif node_name == "pro_research":
                status_container.info("🛡️ PRO Agent researching...")
                if 'messages' in node_data and node_data['messages']:
                    msg = node_data['messages'][0]
                    display_debate_message(msg.dict(), "PRO", pro_container)

            elif node_name == "contra_research":
                status_container.info("🔍 CONTRA Agent investigating...")
                if 'messages' in node_data and node_data['messages']:
                    msg = node_data['messages'][0]
                    display_debate_message(msg.dict(), "CONTRA", contra_container)

            elif node_name == "debate":
                round_num = node_data.get('round_count', 0)
                status_container.info(f"⚖️ Debate Round {round_num}/3...")

                # Display new messages
                if 'messages' in node_data:
                    for msg in node_data['messages']:
                        agent = msg.agent if hasattr(msg, 'agent') else msg.get('agent', 'UNKNOWN')
                        msg_dict = msg.dict() if hasattr(msg, 'dict') else msg

                        if agent == "PRO":
                            display_debate_message(msg_dict, "PRO", pro_container)
                        elif agent == "CONTRA":
                            display_debate_message(msg_dict, "CONTRA", contra_container)

                # Update progress in center
                with center_container:
                    st.progress(round_num / 3, text=f"Round {round_num}/3")

            elif node_name == "judge":
                status_container.info("⚖️ Judge evaluating arguments...")
                final_state = node_data

        status_container.success("✅ Verification complete!")

        return final_state

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        st.error(f"❌ Error during verification: {str(e)}")
        return None

# Main App Layout
def main():
    # Header
    st.title("🔍 VeritasLoop")
    st.markdown("### Sistema di Verifica Notizie Multi-Agente")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurazione")

        enable_trace = st.checkbox(
            "Abilita Tracing (Phoenix)",
            help="Avvia automaticamente Phoenix e visualizza le operazioni degli agenti in tempo reale"
        )

        # Show Phoenix status
        if check_phoenix_running():
            st.success("🔭 Phoenix: Online")
            st.caption("http://localhost:6006")
        else:
            if enable_trace:
                st.info("🔭 Phoenix: Will start with verification")
            else:
                st.info("🔭 Phoenix: Offline")

        st.markdown("---")
        st.subheader("🎛️ Parametri di Test")

        max_iterations = st.number_input(
            "Massimo iterazioni dibattito",
            min_value=1,
            max_value=10,
            value=3,
            help="Numero massimo di round tra PRO e CONTRA. Usa valori bassi (1-2) per i test."
        )

        max_searches = st.number_input(
            "Massimo ricerche per agente",
            min_value=-1,
            max_value=20,
            value=-1,
            help="Numero massimo di ricerche web per agente. -1 = illimitato. Usa 1-2 per i test."
        )

        st.markdown("---")
        st.markdown("### 📖 Come funziona")
        st.markdown("""
        1. **PRO Agent** 🛡️: Cerca prove a supporto
        2. **CONTRA Agent** 🔍: Cerca prove contrarie
        3. **Debate** ⚖️: Gli agenti si confrontano
        4. **Judge** ⚖️: Valuta e emette il verdetto
        """)

        st.markdown("---")
        st.markdown("### 📊 Tipi di Verdetto")
        st.markdown("""
        - ✅ **VERO**: Verificato come vero
        - ❌ **FALSO**: Verificato come falso
        - ⚠️ **PARZIALMENTE_VERO**: Parzialmente vero
        - 🔍 **CONTESTO_MANCANTE**: Manca contesto
        - ❓ **NON_VERIFICABILE**: Non verificabile
        """)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Input section
        st.subheader("📝 Inserisci la notizia da verificare")

        input_type = st.radio(
            "Tipo di Input",
            ["Testo", "URL"],
            horizontal=True,
            help="Scegli se inserire il testo direttamente o un URL"
        )

        if input_type == "Testo":
            user_input = st.text_area(
                "Inserisci il testo della notizia",
                placeholder="Es: L'ISTAT ha dichiarato che l'inflazione è al 5%",
                height=150
            )
        else:
            user_input = st.text_input(
                "Inserisci l'URL della notizia",
                placeholder="Es: https://www.ansa.it/..."
            )

        verify_button = st.button("🔍 Verifica", type="primary", use_container_width=True)

    with col2:
        st.subheader("💡 Esempi")
        st.markdown("""
        **Politica:**
        - "Il governo ha aumentato le tasse del 10%"

        **Salute:**
        - "Un nuovo studio conferma l'efficacia del vaccino"

        **Economia:**
        - "La disoccupazione è scesa al minimo storico"
        """)

    # Process verification
    if verify_button and user_input:
        st.markdown("---")
        st.header("🎭 Arena del Dibattito")

        # Create 3-column layout for debate
        col_pro, col_center, col_contra = st.columns([1, 1, 1])

        with col_pro:
            st.markdown('<div class="agent-header">🛡️ PRO Agent</div>', unsafe_allow_html=True)
            st.caption("Difende la veridicità")

        with col_center:
            st.markdown('<div class="agent-header">⚖️ Arena</div>', unsafe_allow_html=True)
            st.caption("Progressione del dibattito")

        with col_contra:
            st.markdown('<div class="agent-header">🔍 CONTRA Agent</div>', unsafe_allow_html=True)
            st.caption("Cerca contraddizioni")

        # Run verification
        result = run_verification(user_input, input_type, enable_trace, max_iterations, max_searches)

        if result and 'verdict' in result:
            st.markdown("---")
            st.header("⚖️ Verdetto Finale")

            verdict_data = result['verdict']
            verdict_type = verdict_data.get('verdict', 'NON_VERIFICABILE')
            confidence = verdict_data.get('confidence_score', 0)
            summary = verdict_data.get('summary', 'Nessun riepilogo disponibile.')

            # Display verdict with color coding
            verdict_class = get_verdict_color(verdict_type)
            verdict_emoji = get_verdict_emoji(verdict_type)

            st.markdown(f"""
            <div class="{verdict_class}">
                <h2 style="margin: 0;">{verdict_emoji} {verdict_type}</h2>
                <p style="font-size: 1.2rem; margin-top: 0.5rem;">Confidenza: {confidence}%</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"### 📋 Sintesi\n{summary}")

            # Analysis section
            if 'analysis' in verdict_data:
                analysis = verdict_data['analysis']

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 🛡️ Forza PRO")
                    st.info(analysis.get('pro_strength', 'N/A'))

                with col2:
                    st.markdown("#### 🔍 Forza CONTRA")
                    st.warning(analysis.get('contra_strength', 'N/A'))

                # Consensus facts
                if 'consensus_facts' in analysis and analysis['consensus_facts']:
                    st.markdown("#### ✅ Fatti Concordati")
                    for fact in analysis['consensus_facts']:
                        st.success(f"- {fact}")

                # Disputed points
                if 'disputed_points' in analysis and analysis['disputed_points']:
                    st.markdown("#### ⚠️ Punti Contestati")
                    for point in analysis['disputed_points']:
                        st.warning(f"- {point}")

            # Sources used
            if 'sources_used' in verdict_data and verdict_data['sources_used']:
                st.markdown("### 📚 Fonti Utilizzate")

                sources = verdict_data['sources_used']
                for i, source in enumerate(sources, 1):
                    st.markdown(format_source(source, i), unsafe_allow_html=True)

            # Metadata
            if 'metadata' in verdict_data:
                metadata = verdict_data['metadata']

                st.markdown("---")
                st.markdown("### 📊 Statistiche Verifica")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "⏱️ Tempo Elaborazione",
                        f"{metadata.get('processing_time_seconds', 0):.1f}s"
                    )

                with col2:
                    st.metric(
                        "🔄 Round Completati",
                        metadata.get('rounds_completed', 0)
                    )

                with col3:
                    st.metric(
                        "🔗 Fonti Verificate",
                        metadata.get('total_sources_checked', 0)
                    )

            # JSON output (collapsible)
            with st.expander("📄 Visualizza Output JSON"):
                st.json(result)

    elif verify_button:
        st.warning("⚠️ Per favore, inserisci una notizia da verificare.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>VeritasLoop - Sistema di Verifica Notizie Multi-Agente</p>
        <p>Powered by LangGraph & OpenAI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
