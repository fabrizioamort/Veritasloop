from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from src.agents.pro_agent import ProAgent
from src.models.schemas import (
    AgentType,
    Claim,
    ClaimCategory,
    DebateMessage,
    GraphState,
    MessageType,
)
from src.utils.tool_manager import ToolManager


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke.return_value = AIMessage(content="This is a strong argument supporting the claim.")
    return llm

@pytest.fixture
def mock_tool_manager():
    tm = MagicMock(spec=ToolManager)
    tm.search_web.return_value = [
        {"title": "Official Source", "url": "https://gov.it/news", "snippet": "Official confirmation."}
    ]
    return tm

@pytest.fixture
def pro_agent(mock_llm, mock_tool_manager):
    return ProAgent(llm=mock_llm, tool_manager=mock_tool_manager)

def test_initialization(pro_agent):
    assert pro_agent.logger.name == "Agent.PRO"

def test_think_argument(pro_agent, mock_tool_manager):
    claim = Claim(
        raw_input="Test claim",
        core_claim="The sky is blue",
        category=ClaimCategory.SCIENCE
    )
    state = GraphState(
        claim=claim,
        messages=[],
        pro_sources=[],
        contra_sources=[],
        round_count=0
    )

    message = pro_agent.think(state)

    assert isinstance(message, DebateMessage)
    assert message.agent == AgentType.PRO
    assert message.message_type == MessageType.ARGUMENT
    assert message.content == "This is a strong argument supporting the claim."
    assert len(message.sources) > 0
    assert str(message.sources[0].url) == "https://gov.it/news"

    # Verify search was called with correct strategy
    mock_tool_manager.search_web.assert_called()

def test_think_defense(pro_agent):
    claim = Claim(
        raw_input="Test claim",
        core_claim="The sky is blue",
        category=ClaimCategory.SCIENCE
    )
    # Simulate existing messages (CONTRA rebuttal)
    contra_msg = DebateMessage(
        round=0,
        agent=AgentType.CONTRA,
        message_type=MessageType.REBUTTAL,
        content="But it looks gray today.",
        confidence=50.0
    )
    state = GraphState(
        claim=claim,
        messages=[contra_msg],
        pro_sources=[],
        contra_sources=[],
        round_count=1
    )

    message = pro_agent.think(state)

    assert message.message_type == MessageType.DEFENSE
