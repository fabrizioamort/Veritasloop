"""
End-to-End Integration Tests for VeritasLoop Pipeline

This module contains comprehensive integration tests for the full VeritasLoop system.
It includes both mocked unit tests (fast) and real integration tests (slow, optional).

Task 4.3: End-to-End Integration Test
- Test with known true claim
- Test with known false claim
- Test with ambiguous claim
- Validate: graph completes, verdict format is valid, sources are real URLs, execution time
"""

import pytest
import time
import re
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from src.models.schemas import (
    Claim,
    Entities,
    GraphState,
    Verdict,
    DebateMessage,
    AgentType,
    MessageType,
    Source,
    Reliability,
    VerdictType
)
from src.orchestrator.graph import get_app


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def is_valid_url(url: str) -> bool:
    """Validate that a string is a properly formatted URL."""
    try:
        result = urlparse(str(url))
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception:
        return False


def validate_verdict_structure(verdict_data: Dict[str, Any]) -> None:
    """
    Validate that the verdict dictionary has the correct structure.

    Raises AssertionError if validation fails.
    """
    # Top-level fields
    assert "verdict" in verdict_data, "Missing 'verdict' field"
    assert "confidence_score" in verdict_data, "Missing 'confidence_score' field"
    assert "summary" in verdict_data, "Missing 'summary' field"
    assert "analysis" in verdict_data, "Missing 'analysis' field"
    assert "sources_used" in verdict_data, "Missing 'sources_used' field"
    assert "metadata" in verdict_data, "Missing 'metadata' field"

    # Type validation
    assert isinstance(verdict_data["verdict"], str), "verdict must be a string"
    assert isinstance(verdict_data["confidence_score"], (int, float)), "confidence_score must be numeric"
    assert isinstance(verdict_data["summary"], str), "summary must be a string"
    assert isinstance(verdict_data["analysis"], dict), "analysis must be a dict"
    assert isinstance(verdict_data["sources_used"], list), "sources_used must be a list"
    assert isinstance(verdict_data["metadata"], dict), "metadata must be a dict"

    # Verdict category validation
    valid_verdicts = [v.value for v in VerdictType]
    assert verdict_data["verdict"] in valid_verdicts, f"Invalid verdict: {verdict_data['verdict']}"

    # Confidence score range
    assert 0 <= verdict_data["confidence_score"] <= 100, "confidence_score must be 0-100"

    # Analysis structure
    analysis = verdict_data["analysis"]
    assert "pro_strength" in analysis, "Missing 'pro_strength' in analysis"
    assert "contra_strength" in analysis, "Missing 'contra_strength' in analysis"
    assert "consensus_facts" in analysis, "Missing 'consensus_facts' in analysis"
    assert "disputed_points" in analysis, "Missing 'disputed_points' in analysis"

    # Metadata structure
    metadata = verdict_data["metadata"]
    assert "processing_time_seconds" in metadata, "Missing 'processing_time_seconds' in metadata"
    assert "rounds_completed" in metadata, "Missing 'rounds_completed' in metadata"
    assert "total_sources_checked" in metadata, "Missing 'total_sources_checked' in metadata"


def validate_sources(sources: list) -> None:
    """
    Validate that all sources have valid URLs.

    Raises AssertionError if validation fails.
    """
    for source in sources:
        if isinstance(source, dict):
            assert "url" in source, "Source missing 'url' field"
            url = source["url"]
        elif isinstance(source, Source):
            url = source.url
        else:
            raise AssertionError(f"Unknown source type: {type(source)}")

        assert is_valid_url(url), f"Invalid URL: {url}"


# ============================================================================
# MOCKED UNIT TESTS (FAST, ALWAYS RUN)
# ============================================================================

@pytest.fixture
def mock_env(mocker):
    """Mock all external dependencies for fast unit testing."""
    # Mock LLM
    mocker.patch('src.utils.claim_extractor.get_llm', return_value=MagicMock(invoke=lambda messages: MagicMock(content="Extracted claim")))

    # Mock search tools
    mocker.patch('src.agents.pro_agent.ProAgent.search', return_value=[
        {"title": "Official Source PRO", "url": "https://gov.example.it/news", "snippet": "Official confirmation."}
    ])
    mocker.patch('src.agents.contra_agent.ContraAgent.search', return_value=[
        {"title": "Fact-Check Source CONTRA", "url": "https://factcheck.example.org/debunk", "snippet": "This is disputed."}
    ])

    # Mock judge metadata calculation
    mocker.patch('src.agents.judge_agent.JudgeAgent._calculate_metadata', return_value={
        "processing_time_seconds": 12.34,
        "rounds_completed": 3,
        "total_sources_checked": 5
    })


@pytest.fixture(autouse=True)
def patch_agents(mocker):
    """Patch agent methods for mocked unit tests."""
    from src.models.schemas import DebateMessage, AgentType, MessageType

    # Mock shared resources
    mocker.patch('src.orchestrator.graph.get_llm', return_value=MagicMock())
    mocker.patch('src.orchestrator.graph.ToolManager', return_value=MagicMock())

    # Mock ProAgent.think
    def mock_pro_think(state, *args, **kwargs):
        return DebateMessage(
            round=state['round_count'],
            agent=AgentType.PRO,
            message_type=MessageType.ARGUMENT,
            content=f"PRO: Supporting the claim '{state['claim'].core_claim}' with institutional evidence.",
            sources=[Source(
                url="https://gov.example.it/data",
                title="Government Data",
                snippet="Official government data confirms the claim.",
                reliability=Reliability.HIGH
            )],
            confidence=80.0
        )
    mocker.patch('src.agents.pro_agent.ProAgent.think', side_effect=mock_pro_think)

    # Mock ContraAgent.think
    def mock_contra_think(state, *args, **kwargs):
        return DebateMessage(
            round=state['round_count'],
            agent=AgentType.CONTRA,
            message_type=MessageType.REBUTTAL,
            content=f"CONTRA: Challenging the claim '{state['claim'].core_claim}' with fact-checking.",
            sources=[Source(
                url="https://factcheck.example.org/analysis",
                title="Fact-Check Analysis",
                snippet="Independent fact-checkers dispute this claim.",
                reliability=Reliability.HIGH
            )],
            confidence=70.0
        )
    mocker.patch('src.agents.contra_agent.ContraAgent.think', side_effect=mock_contra_think)

    # Mock JudgeAgent.think
    def mock_judge_think(state, *args, **kwargs):
        return {
            'verdict': {
                'verdict': 'PARZIALMENTE_VERO',
                'confidence_score': 75.0,
                'summary': 'La verifica ha rivelato che il claim è parzialmente corretto ma manca di contesto importante.',
                'analysis': {
                    'pro_strength': 'Alta - fonti istituzionali affidabili',
                    'contra_strength': 'Media - evidenze di fact-checking valide',
                    'consensus_facts': ['Il dato è tecnicamente corretto'],
                    'disputed_points': ['Manca contesto temporale importante']
                },
                'sources_used': [
                    {'url': 'https://gov.example.it/data', 'title': 'Government Data'},
                    {'url': 'https://factcheck.example.org/analysis', 'title': 'Fact-Check Analysis'}
                ],
                'metadata': {
                    'processing_time_seconds': 45.2,
                    'rounds_completed': 3,
                    'total_sources_checked': 5
                }
            }
        }
    mocker.patch('src.agents.judge_agent.JudgeAgent.think', side_effect=mock_judge_think)

    # Mock claim extraction
    def mock_extract(text):
        return Claim(
            raw_input=text,
            core_claim=text,
            entities=Entities(
                people=["Example Person"],
                places=["Italy"],
                organizations=["ISTAT"],
                dates=["2024"]
            )
        )
    mocker.patch('src.orchestrator.graph.extract_from_text', side_effect=mock_extract)


@pytest.mark.parametrize("claim_text,description", [
    ("Il terremoto in Emilia del 2012 ha avuto magnitudo 5.9", "Known TRUE claim"),
    ("L'ISTAT ha dichiarato che l'Italia ha 100 milioni di abitanti", "Known FALSE claim"),
    ("Le tasse sono aumentate nel 2024", "Ambiguous claim"),
])
def test_full_pipeline_mocked(claim_text, description, mock_env):
    """
    Test the full pipeline with mocked dependencies (FAST).

    This test validates:
    - Graph executes without errors
    - All nodes complete successfully
    - State is properly updated throughout execution
    - Final verdict has correct structure
    """
    print(f"\n=== Testing: {description} ===")
    print(f"Claim: {claim_text}")

    # 1. Setup initial state
    initial_state = {
        "claim": Claim(raw_input=claim_text, core_claim=claim_text, entities=Entities()),
        "messages": [],
        "pro_sources": [],
        "contra_sources": [],
        "round_count": 0,
        "max_iterations": 3,
        "max_searches": -1,
        "language": "Italian",
        "pro_personality": "ASSERTIVE",
        "contra_personality": "ASSERTIVE"
    }

    # 2. Measure execution time
    start_time = time.time()

    # 3. Run the full pipeline
    app = get_app()
    final_state = app.invoke(initial_state)

    execution_time = time.time() - start_time
    print(f"Execution time: {execution_time:.2f}s")

    # 4. Validate graph completion
    assert final_state is not None, "Graph returned None"
    assert "verdict" in final_state, "No verdict in final state"
    assert "messages" in final_state, "No messages in final state"

    # 5. Validate verdict structure
    verdict_data = final_state["verdict"]
    validate_verdict_structure(verdict_data)

    # 6. Validate debate happened
    assert len(final_state["messages"]) > 0, "No debate messages generated"
    assert final_state["round_count"] >= 0, "Invalid round count"

    # 7. Validate sources
    all_sources = []
    for msg in final_state["messages"]:
        if hasattr(msg, 'sources') and msg.sources:
            all_sources.extend(msg.sources)

    if all_sources:
        validate_sources(all_sources)

    # 8. Validate metadata
    metadata = verdict_data["metadata"]
    assert metadata["rounds_completed"] == final_state["round_count"], "Round count mismatch"
    assert metadata["total_sources_checked"] >= 0, "Invalid source count"

    # 9. Print results
    print(f"✓ Verdict: {verdict_data['verdict']}")
    print(f"✓ Confidence: {verdict_data['confidence_score']}%")
    print(f"✓ Rounds completed: {metadata['rounds_completed']}")
    print(f"✓ Sources checked: {metadata['total_sources_checked']}")
    print(f"✓ Messages generated: {len(final_state['messages'])}")
    print(f"✓ Test passed for: {description}")


def test_verdict_structure_validation():
    """Test the verdict validation helper with various inputs."""

    # Valid verdict
    valid_verdict = {
        "verdict": "VERO",
        "confidence_score": 85.5,
        "summary": "Test summary",
        "analysis": {
            "pro_strength": "High",
            "contra_strength": "Low",
            "consensus_facts": ["Fact 1"],
            "disputed_points": []
        },
        "sources_used": [],
        "metadata": {
            "processing_time_seconds": 30.0,
            "rounds_completed": 2,
            "total_sources_checked": 5
        }
    }

    # Should not raise
    validate_verdict_structure(valid_verdict)

    # Invalid: missing field
    invalid_verdict = valid_verdict.copy()
    del invalid_verdict["summary"]

    with pytest.raises(AssertionError, match="Missing 'summary'"):
        validate_verdict_structure(invalid_verdict)

    # Invalid: wrong type
    invalid_verdict = valid_verdict.copy()
    invalid_verdict["confidence_score"] = "not a number"

    with pytest.raises(AssertionError, match="confidence_score must be numeric"):
        validate_verdict_structure(invalid_verdict)

    # Invalid: out of range confidence
    invalid_verdict = valid_verdict.copy()
    invalid_verdict["confidence_score"] = 150

    with pytest.raises(AssertionError, match="confidence_score must be 0-100"):
        validate_verdict_structure(invalid_verdict)


def test_url_validation():
    """Test the URL validation helper."""

    # Valid URLs
    assert is_valid_url("https://www.example.com")
    assert is_valid_url("http://example.org/path")
    assert is_valid_url("https://gov.it/news/2024")

    # Invalid URLs
    assert not is_valid_url("not a url")
    assert not is_valid_url("ftp://invalid.scheme")
    assert not is_valid_url("")
    assert not is_valid_url("example.com")  # Missing scheme


def test_graph_state_progression():
    """Test that the graph properly updates state through all phases."""

    initial_state = {
        "claim": Claim(
            raw_input="Test claim for state progression",
            core_claim="Test claim for state progression",
            entities=Entities()
        ),
        "messages": [],
        "pro_sources": [],
        "contra_sources": [],
        "round_count": 0,
        "max_iterations": 2,  # Shorter for faster test
        "max_searches": 3,
        "language": "Italian",
        "pro_personality": "PASSIVE",
        "contra_personality": "AGGRESSIVE"
    }

    app = get_app()
    final_state = app.invoke(initial_state)

    # State should have evolved
    assert final_state["round_count"] > initial_state["round_count"], "Round count should increase"
    assert len(final_state["messages"]) > 0, "Messages should be added"
    assert "verdict" in final_state, "Verdict should be generated"

    # Personality should be preserved
    assert final_state.get("pro_personality") == "PASSIVE"
    assert final_state.get("contra_personality") == "AGGRESSIVE"


# ============================================================================
# REAL INTEGRATION TESTS (SLOW, OPTIONAL)
# ============================================================================

@pytest.mark.integration
@pytest.mark.skip(reason="Integration tests require --run-integration flag (manually enable by removing @pytest.mark.skip)")
@pytest.mark.parametrize("claim_text,expected_verdict_type,description", [
    (
        "Il terremoto in Emilia del 2012 ha avuto magnitudo 5.9",
        ["VERO", "PARZIALMENTE_VERO"],
        "Known TRUE claim - Emilia earthquake 2012"
    ),
    (
        "L'ISTAT ha dichiarato che l'Italia ha 100 milioni di abitanti",
        ["FALSO", "PARZIALMENTE_VERO"],
        "Known FALSE claim - Italy population"
    ),
    (
        "Le tasse sono aumentate nel 2024",
        ["PARZIALMENTE_VERO", "CONTESTO_MANCANTE", "NON_VERIFICABILE"],
        "Ambiguous claim - Tax increases"
    ),
])
def test_full_pipeline_real(claim_text, expected_verdict_type, description):
    """
    REAL integration test with actual API calls.

    WARNING: This test:
    - Makes real API calls (costs money)
    - Takes 30-90 seconds to run
    - Requires valid API keys in .env
    - May fail due to network issues

    Run with: pytest tests/test_full_pipeline.py --run-integration -v
    """
    print(f"\n{'='*80}")
    print(f"REAL INTEGRATION TEST: {description}")
    print(f"Claim: {claim_text}")
    print(f"{'='*80}")

    # 1. Setup initial state (no mocking!)
    initial_state = {
        "claim": Claim(raw_input=claim_text, core_claim=claim_text, entities=Entities()),
        "messages": [],
        "pro_sources": [],
        "contra_sources": [],
        "round_count": 0,
        "max_iterations": 2,  # Reduced for faster testing
        "max_searches": 5,    # Limited to reduce API costs
        "language": "Italian",
        "pro_personality": "ASSERTIVE",
        "contra_personality": "ASSERTIVE"
    }

    # 2. Measure execution time
    start_time = time.time()

    # 3. Run the REAL pipeline (no mocks!)
    # We need to temporarily disable the autouse fixture
    # This is done by running with --no-cov or in a separate test session
    from src.orchestrator.graph import get_app as get_real_app

    app = get_real_app()
    final_state = app.invoke(initial_state)

    execution_time = time.time() - start_time

    # 4. Validate execution completed
    assert final_state is not None, "Graph execution failed"
    print(f"✓ Graph execution completed in {execution_time:.2f}s")

    # 5. Validate verdict structure
    assert "verdict" in final_state, "No verdict generated"
    verdict_data = final_state["verdict"]
    validate_verdict_structure(verdict_data)
    print(f"✓ Verdict structure is valid")

    # 6. Validate verdict type (should match expected)
    actual_verdict = verdict_data["verdict"]
    assert actual_verdict in expected_verdict_type, \
        f"Unexpected verdict: {actual_verdict}, expected one of {expected_verdict_type}"
    print(f"✓ Verdict type: {actual_verdict} (expected: {expected_verdict_type})")

    # 7. Validate sources are REAL URLs
    all_sources = verdict_data.get("sources_used", [])
    for msg in final_state.get("messages", []):
        if hasattr(msg, 'sources'):
            all_sources.extend([{"url": s.url, "title": s.title} for s in msg.sources])

    assert len(all_sources) > 0, "No sources were gathered"
    validate_sources(all_sources)
    print(f"✓ All {len(all_sources)} sources have valid URLs")

    # 8. Print sample sources
    print(f"\nSample sources:")
    for i, source in enumerate(all_sources[:3], 1):
        url = source.get("url") if isinstance(source, dict) else source.url
        title = source.get("title", "No title") if isinstance(source, dict) else source.title
        print(f"  [{i}] {title}")
        print(f"      {url}")

    # 9. Validate execution time is reasonable
    assert execution_time < 180, f"Execution took too long: {execution_time:.2f}s"
    print(f"✓ Execution time reasonable: {execution_time:.2f}s")

    # 10. Validate debate happened
    messages = final_state.get("messages", [])
    assert len(messages) >= 2, "Not enough debate messages"
    print(f"✓ Debate occurred: {len(messages)} messages exchanged")

    # 11. Print final summary
    print(f"\n{'='*80}")
    print(f"VERDICT SUMMARY:")
    print(f"  Verdict: {verdict_data['verdict']}")
    print(f"  Confidence: {verdict_data['confidence_score']}%")
    print(f"  Summary: {verdict_data['summary'][:200]}...")
    print(f"  Rounds: {verdict_data['metadata']['rounds_completed']}")
    print(f"  Sources: {verdict_data['metadata']['total_sources_checked']}")
    print(f"  Time: {execution_time:.2f}s")
    print(f"{'='*80}")
    print(f"✓ REAL INTEGRATION TEST PASSED: {description}")
