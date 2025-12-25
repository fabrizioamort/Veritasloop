"""
Unit tests for the BaseAgent class.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.agents.base_agent import BaseAgent
from src.models.schemas import AgentType, DebateMessage, GraphState, MessageType


class ConcreteAgent(BaseAgent):
    """A concrete implementation of BaseAgent for testing purposes."""
    def think(self, state: GraphState) -> DebateMessage:
        """A mock implementation of the think method."""
        self.logger.info("ConcreteAgent is thinking.")
        return DebateMessage(
            round=1,
            agent=AgentType.PRO,
            message_type=MessageType.ARGUMENT,
            content="This is a test message.",
            confidence=100.0,
            sources=[]
        )

class TestBaseAgent(unittest.TestCase):
    """Test suite for the BaseAgent abstract class."""

    def setUp(self):
        """Set up mock objects for each test."""
        self.mock_llm = MagicMock()
        self.mock_tool_manager = MagicMock()
        self.agent = ConcreteAgent(
            llm=self.mock_llm,
            tool_manager=self.mock_tool_manager,
            agent_name="TestAgent"
        )

    def test_initialization(self):
        """Test if the agent is initialized correctly."""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.llm, self.mock_llm)
        self.assertEqual(self.agent.tools, self.mock_tool_manager)
        self.assertEqual(self.agent.logger.name, "Agent.TestAgent")

    def test_think_method(self):
        """Test if the think method can be called on a concrete subclass."""
        mock_state = MagicMock(spec=GraphState)
        message = self.agent.think(mock_state)
        self.assertIsInstance(message, DebateMessage)
        self.assertEqual(message.content, "This is a test message.")

    def test_search_default_strategy(self):
        """Test the search method with the default strategy."""
        query = "test query"
        self.agent.search(query, "default")
        self.mock_tool_manager.search_web.assert_called_once_with(query, tool="brave")

    @patch.dict('os.environ', {'GOOGLE_PSE_API_KEY': 'test_key', 'GOOGLE_PSE_CX': 'test_cx'})
    def test_search_fact_check_strategy_hit(self):
        """Test the fact_check_first strategy with a hit on the first tier."""
        query = "fact check query"
        # Simulate that the first tool returns results
        self.mock_tool_manager.search_web.return_value = [{"title": "Fact Check Result", "url": "http://factcheck.example.com"}]

        self.agent.search(query, "fact_check_first")

        # It should only call the first tool (google_pse_factcheck when env vars are set)
        self.mock_tool_manager.search_web.assert_called_once_with(query, tool="google_pse_factcheck")

    @patch.dict('os.environ', {'GOOGLE_PSE_API_KEY': 'test_key', 'GOOGLE_PSE_CX': 'test_cx'})
    def test_search_fact_check_strategy_miss(self):
        """Test the fact_check_first strategy with a miss on the first tier."""
        query = "fact check query"
        # Simulate that the first tool returns no results
        self.mock_tool_manager.search_web.side_effect = [
            [], # No results for google_pse_factcheck
            [{"title": "Brave Result", "url": "http://example.com"}] # Results for brave
        ]

        self.agent.search(query, "fact_check_first")

        # It should have been called twice (google_pse_factcheck then brave)
        self.assertEqual(self.mock_tool_manager.search_web.call_count, 2)
        # Check the calls
        calls = self.mock_tool_manager.search_web.call_args_list
        self.assertEqual(calls[0].args[0], query)
        self.assertEqual(calls[0].kwargs['tool'], "google_pse_factcheck")
        self.assertEqual(calls[1].args[0], query)
        self.assertEqual(calls[1].kwargs['tool'], "brave")

    def test_search_web_deep_dive_strategy(self):
        """Test the web_deep_dive strategy."""
        query = "deep dive query"
        # Mock return values for the search calls
        self.mock_tool_manager.search_web.return_value = [{"title": "Result", "url": "http://example.com"}]

        self.agent.search(query, "web_deep_dive")

        # web_deep_dive calls brave and duckduckgo (2 calls total)
        self.assertEqual(self.mock_tool_manager.search_web.call_count, 2)
        calls = self.mock_tool_manager.search_web.call_args_list
        # Check the tools used
        tools_called = [call.kwargs['tool'] for call in calls]
        self.assertEqual(tools_called, ["brave", "duckduckgo"])


if __name__ == '__main__':
    unittest.main()
