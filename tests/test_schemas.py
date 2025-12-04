"""
Unit tests for data models and schemas.
"""
import pytest
from datetime import datetime
from uuid import UUID
from pydantic import ValidationError

from src.models.schemas import (
    Claim,
    ClaimCategory,
    Entities,
    Source,
    Reliability,
    AgentType,
    DebateMessage,
    MessageType,
    Verdict,
    VerdictType,
    VerdictAnalysis,
    VerdictMetadata
)

def test_claim_creation_defaults():
    """Test Claim creation with default values."""
    claim = Claim(
        raw_input="Some news text",
        core_claim="Core claim text"
    )
    assert isinstance(claim.id, UUID)
    assert claim.entities.people == []
    assert claim.category == ClaimCategory.OTHER

def test_claim_full_creation():
    """Test Claim creation with all fields."""
    claim = Claim(
        raw_input="Input",
        core_claim="Core",
        entities=Entities(people=["Mario Rossi"], places=["Roma"]),
        category=ClaimCategory.POLITICS
    )
    assert claim.entities.people == ["Mario Rossi"]
    assert claim.category == ClaimCategory.POLITICS

def test_source_validation_valid():
    """Test Source creation with valid data."""
    source = Source(
        url="https://example.com/article",
        title="Example Article",
        snippet="Snippet text",
        reliability=Reliability.HIGH,
        timestamp="2023-10-27T10:00:00Z"
    )
    assert str(source.url) == "https://example.com/article/" or str(source.url) == "https://example.com/article"
    assert isinstance(source.timestamp, datetime)
    assert source.reliability == Reliability.HIGH

def test_source_validation_invalid_url():
    """Test Source validation fails with invalid URL."""
    with pytest.raises(ValidationError):
        Source(
            url="not-a-url",
            title="Title",
            snippet="Snippet",
            reliability=Reliability.LOW
        )

def test_source_timestamp_parsing():
    """Test lenient timestamp parsing."""
    # Test with standard ISO format
    s1 = Source(
        url="https://a.com", title="A", snippet="A", reliability="low",
        timestamp="2023-01-01T12:00:00"
    )
    assert s1.timestamp.year == 2023

    # Test with invalid format (should be None due to custom validator logic or fail depending on implementation)
    # The current implementation returns None on ValueError
    s2 = Source(
        url="https://a.com", title="A", snippet="A", reliability="low",
        timestamp="invalid-date-string"
    )
    assert s2.timestamp is None

def test_debate_message_confidence_validation():
    """Test DebateMessage confidence score limits."""
    # Valid
    msg = DebateMessage(
        round=1,
        agent=AgentType.PRO,
        message_type=MessageType.ARGUMENT,
        content="Argument",
        confidence=85.5
    )
    assert msg.confidence == 85.5

    # Invalid (> 100)
    with pytest.raises(ValidationError):
        DebateMessage(
            round=1, agent=AgentType.PRO, message_type=MessageType.ARGUMENT,
            content="A", confidence=101
        )

    # Invalid (< 0)
    with pytest.raises(ValidationError):
        DebateMessage(
            round=1, agent=AgentType.PRO, message_type=MessageType.ARGUMENT,
            content="A", confidence=-1
        )

def test_verdict_serialization():
    """Test full Verdict object serialization."""
    verdict = Verdict(
        verdict=VerdictType.PARZIALMENTE_VERO,
        confidence_score=75.0,
        summary="Summary text",
        analysis=VerdictAnalysis(
            pro_strength="High",
            contra_strength="Medium",
            consensus_facts=["Fact 1"],
            disputed_points=["Point 1"]
        ),
        sources_used=[
            Source(
                url="https://source.com",
                title="S1",
                snippet="Snip",
                reliability=Reliability.HIGH,
                agent=AgentType.PRO
            )
        ],
        metadata=VerdictMetadata(
            processing_time_seconds=1.5,
            rounds_completed=3,
            total_sources_checked=10
        )
    )
    
    # Check simple properties
    assert verdict.verdict == VerdictType.PARZIALMENTE_VERO
    
    # Test JSON roundtrip
    json_str = verdict.model_dump_json()
    assert "PARZIALMENTE_VERO" in json_str
    
    # Re-hydrate
    v2 = Verdict.model_validate_json(json_str)
    assert v2.analysis.pro_strength == "High"
    assert v2.sources_used[0].url == verdict.sources_used[0].url