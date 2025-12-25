"""
Unit tests for the ContraAgent class.
"""

from unittest.mock import MagicMock

import pytest

from src.agents.contra_agent import ContraAgent
from src.models.schemas import (
    AgentType,
    Claim,
    DebateMessage,
    GraphState,
    MessageType,
)
from src.utils.tool_manager import ToolManager


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    # Mock the invoke method to return a response with content
    mock_response = MagicMock()
    mock_response.content = "This is a skeptical response."
    llm.invoke.return_value = mock_response
    return llm


@pytest.fixture
def mock_tool_manager():
    tool_manager = MagicMock(spec=ToolManager)
    # Mock search_web to return some dummy results
    tool_manager.search_web.return_value = [
        {
            "url": "https://example.com/factcheck",
            "title": "Fact Check Example",
            "snippet": "This claim is false.",
        },
        {
            "url": "https://example.com/news",
            "title": "News Example",
            "snippet": "Reporting on the event.",
        }
    ]
    return tool_manager


@pytest.fixture
def contra_agent(mock_llm, mock_tool_manager):
    return ContraAgent(llm=mock_llm, tool_manager=mock_tool_manager)


def test_initialization(contra_agent):
    assert contra_agent.logger.name == "Agent.CONTRA"
    # Default personality is ASSERTIVE (Diana)
    assert "Diana" in contra_agent.system_prompt
    assert "skeptical investigative journalist" in contra_agent.system_prompt


def test_think_initial_round(contra_agent, mock_tool_manager, mock_llm):
    # Setup state for round 0
    claim = Claim(
        raw_input="Test claim",
        core_claim="The sky is green.",
        category="science"
    )
    state = GraphState(
        claim=claim,
        messages=[],
        pro_sources=[],
        contra_sources=[],
        round_count=0
    )

    # Execute think
    message = contra_agent.think(state)

    # Verify search was called
    mock_tool_manager.search_web.assert_called()

    # Verify LLM was called with correct prompt structure
    mock_llm.invoke.assert_called_once()
    call_args = mock_llm.invoke.call_args[0][0]
    assert len(call_args) == 2
    # Default personality is ASSERTIVE (Diana)
    assert "Diana" in call_args[0].content  # System prompt
    assert "Analyze this claim" in call_args[1].content     # User prompt for round 0

    # Verify message structure
    assert isinstance(message, DebateMessage)
    assert message.agent == AgentType.CONTRA
    assert message.message_type == MessageType.ARGUMENT
    assert message.round == 0
    assert len(message.sources) > 0
    assert message.content == "This is a skeptical response."


def test_think_rebuttal_round(contra_agent, mock_tool_manager, mock_llm):
    # Setup state for round 1
    claim = Claim(
        raw_input="Test claim",
        core_claim="The sky is green.",
        category="science"
    )
    pro_message = DebateMessage(
        round=0,
        agent=AgentType.PRO,
        message_type=MessageType.ARGUMENT,
        content="I have proof the sky is green.",
        confidence=90.0
    )
    state = GraphState(
        claim=claim,
        messages=[pro_message],
        pro_sources=[],
        contra_sources=[],
        round_count=1
    )

    # Execute think
    message = contra_agent.think(state)

    # Verify LLM was called with rebuttal prompt
    mock_llm.invoke.assert_called_once()
    call_args = mock_llm.invoke.call_args[0][0]
    assert "The PRO agent argued" in call_args[1].content

    # Verify message structure
    assert message.agent == AgentType.CONTRA
    assert message.message_type == MessageType.REBUTTAL
    assert message.round == 1


def test_search_strategy(contra_agent, mock_tool_manager):
    # Test that default search uses fact_check_first strategy for initial round
    claim = Claim(raw_input="Test", core_claim="Test", category="other")
    state = GraphState(claim=claim, messages=[], pro_sources=[], contra_sources=[], round_count=0)

    contra_agent.think(state)

    # Check if search_web was called with expected tools for fact checking
    # Note: The BaseAgent.search logic calls tool_manager.search_web
    # We just want to ensure it's calling something.
    assert mock_tool_manager.search_web.call_count >= 1
