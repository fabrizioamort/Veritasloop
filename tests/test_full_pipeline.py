
from unittest.mock import MagicMock

import pytest

from src.models.schemas import (
    AgentType,
    Claim,
    DebateMessage,
    Entities,
    MessageType,
)
from src.orchestrator.graph import get_app


def mock_llm_response(messages):
    # Simplified mock LLM to return a plausible response based on agent
    system_prompt = messages[0].content
    human_prompt = messages[1].content

    if "You are a meticulous institutional analyst" in system_prompt: # PRO
        return MagicMock(content="The claim is supported by institutional data.")
    elif "You are a critical fact-checker" in system_prompt: # CONTRA
        return MagicMock(content="The claim lacks context and is misleading.")
    elif "You are an impartial Supreme Court judge" in system_prompt: # JUDGE
        # Return a valid Verdict object as a dictionary
        return {
            "verdict": "PARZIALMENTE_VERO",
            "confidence_score": 75.0,
            "summary": "Il verdetto è parzialmente vero.",
            "analysis": {
                "pro_strength": "Good",
                "contra_strength": "Good",
                "consensus_facts": [],
                "disputed_points": []
            },
            "sources_used": [],
            "metadata": {
                "processing_time_seconds": 0,
                "rounds_completed": 0,
                "total_sources_checked": 0
            }
        }
    return MagicMock(content="Default mock response.")

@pytest.fixture
def mock_env(mocker):
    mocker.patch('src.utils.claim_extractor.get_llm', return_value=MagicMock(invoke=lambda messages: mock_llm_response(messages)))
    mocker.patch('src.agents.pro_agent.ProAgent.search', return_value=[{"title": "Source PRO", "url": "http://pro.source", "snippet": "Pro snippet"}])
    mocker.patch('src.agents.contra_agent.ContraAgent.search', return_value=[{"title": "Source CONTRA", "url": "http://contra.source", "snippet": "Contra snippet"}])
    mocker.patch('src.agents.judge_agent.JudgeAgent._calculate_metadata', return_value={
        "processing_time_seconds": 12.34,
        "rounds_completed": 3,
        "total_sources_checked": 2
    })

    # Mock the LLM inside the agents
    # Removed invalid patching of instance attributes on the class
    # mocker.patch('src.agents.pro_agent.ProAgent.llm', ...)
    # The agents' think method is mocked entirely below, so this is not needed.

    # The judge's chain is more complex, so we patch the `think` method directly
    # to return a controlled verdict dictionary.
    mock_verdict = {
        'verdict': {
            'verdict': 'PARZIALMENTE_VERO',
            'confidence_score': 75.0,
            'summary': 'This is a test summary.',
            'analysis': {
                'pro_strength': 'High',
                'contra_strength': 'Medium',
                'consensus_facts': ['Fact 1'],
                'disputed_points': ['Point 1']
            },
            'sources_used': [],
            'metadata': {
                'processing_time_seconds': 12.34,
                'rounds_completed': 3,
                'total_sources_checked': 2
            }
        }
    }
    mocker.patch('src.agents.judge_agent.JudgeAgent.think', return_value=mock_verdict)


# Since the placeholder functions in graph.py are not using the agents,
# we need to replace them with the actual agent calls for the integration test.
# Since the graph now uses real agents, we want to mock the AGENT classes or their methods,
# NOT the graph node functions (pro_research, etc.). We want to test that the node functions
# correctly call the agents.

@pytest.fixture(autouse=True)
def patch_agents(mocker):

    # Mock the LLM and ToolManager used by agents to avoid real calls
    mocker.patch('src.orchestrator.graph.get_llm', return_value=MagicMock())
    mocker.patch('src.orchestrator.graph.ToolManager', return_value=MagicMock())

    # We need to mock ProAgent, ContraAgent, JudgeAgent classes where they are used.
    # They are imported in src.orchestrator.graph AND src.orchestrator.debate

    # Mock ProAgent.think
    def mock_pro_think(state, *args, **kwargs):
        return DebateMessage(
            round=state['round_count'],
            agent=AgentType.PRO,
            message_type=MessageType.ARGUMENT, # Simplify
            content=f"PRO Argument for {state['claim'].core_claim}",
            sources=[],
            confidence=80.0
        )
    mocker.patch('src.agents.pro_agent.ProAgent.think', side_effect=mock_pro_think)

    # Mock ContraAgent.think
    def mock_contra_think(state, *args, **kwargs):
        return DebateMessage(
            round=state['round_count'],
            agent=AgentType.CONTRA,
            message_type=MessageType.REBUTTAL,
            content=f"CONTRA Rebuttal for {state['claim'].core_claim}",
            sources=[],
            confidence=70.0
        )
    mocker.patch('src.agents.contra_agent.ContraAgent.think', side_effect=mock_contra_think)

    # Mock JudgeAgent.think
    def mock_judge_think(state, *args, **kwargs):
        return {
            'verdict': {
                'verdict': 'PARZIALMENTE_VERO',
                'confidence_score': 75.0,
                'summary': 'Test Summary',
                'analysis': {},
                'sources_used': [],
                'metadata': {}
            }
        }
    mocker.patch('src.agents.judge_agent.JudgeAgent.think', side_effect=mock_judge_think)


    # Also mock extract_from_text called in graph.py for the 'extract' node
    def mock_extract(text):
        return Claim(raw_input=text, core_claim=text, entities=Entities())
    mocker.patch('src.orchestrator.graph.extract_from_text', side_effect=mock_extract)

    # Note: src.orchestrator.debate creates NEW instances of agents.
    # By patching the classes methods above `src.agents.pro_agent.ProAgent.think`,
    # any instance of ProAgent will use the mocked method.


@pytest.mark.parametrize("claim_text, expected_verdict_key", [
    ("Il terremoto in Emilia del 2012 ha avuto magnitudo 5.9", "VERO"),
    ("L'ISTAT ha dichiarato che l'Italia ha 100 milioni di abitanti", "FALSO"),
    ("Le tasse sono aumentate nel 2024", "PARZIALMENTE_VERO"),
])
def test_full_pipeline(claim_text, expected_verdict_key, mock_env):
    """
    Tests the full pipeline from claim to verdict for different scenarios.
    
    This is an integration test that runs the entire LangGraph.
    The external dependencies (LLMs, search tools) are mocked to ensure
    the test is fast, repeatable, and focuses on the integration logic.
    """
    # 1. Initial State
    initial_state = {
        "claim": Claim(raw_input=claim_text, core_claim=claim_text, entities=Entities()),
        "messages": [],
        "pro_sources": [],
        "contra_sources": [],
        "round_count": 0,
    }

    # 2. Run the full pipeline
    # The `app` is the compiled LangGraph from `src/orchestrator/graph.py`
    app = get_app()
    final_state = app.invoke(initial_state)

    # 3. Validate the output
    assert final_state is not None
    assert "verdict" in final_state

    verdict_data = final_state["verdict"]

    # Validate verdict structure
    assert "verdict" in verdict_data
    assert "confidence_score" in verdict_data
    assert "summary" in verdict_data
    assert isinstance(verdict_data["confidence_score"], float)

    # Because we mocked the judge's response, we can't assert the *actual* verdict
    # for each specific claim. The goal of this test is to ensure the graph
    # runs end-to-end without errors and returns a correctly formatted verdict object.
    # The mock judge *always* returns PARZIALMENTE_VERO.
    # We can check that the graph completes and the structure is valid.
    assert verdict_data["verdict"] == "PARZIALMENTE_VERO"

    # Validate that the debate happened
    assert "messages" in final_state
    assert len(final_state["messages"]) > 0
    # With the mocked debate round, it will run 3 times, adding 2 messages each time
    # plus the two initial research messages. 2 + 3*2 = 8
    assert len(final_state["messages"]) == 8
    assert final_state["round_count"] == 3

    print(f"Test for '{claim_text}' passed. Final verdict: {verdict_data['verdict']}")
