"""
Unit tests for the BaseAgent class.
"""

import unittest
from unittest.mock import MagicMock, patch
from src.agents.base_agent import BaseAgent
from src.models.schemas import GraphState, DebateMessage, AgentType, MessageType

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

    def test_search_fact_check_strategy_hit(self):
        """Test the fact_check_first strategy with a hit on the first tier."""
        query = "fact check query"
        # Simulate that the first tool returns results
        self.mock_tool_manager.search_web.return_value = [{"title": "Fact Check Result", "url": "http://factcheck.example.com"}]
        
        self.agent.search(query, "fact_check_first")
        
        # It should only call the first tool
        self.mock_tool_manager.search_web.assert_called_once_with(query, tool="google_pse_factcheck")

    def test_search_fact_check_strategy_miss(self):
        """Test the fact_check_first strategy with a miss on the first tier."""
        query = "fact check query"
        # Simulate that the first tool returns no results
        self.mock_tool_manager.search_web.side_effect = [
            [], # No results for google_pse_factcheck
            [{"title": "Brave Result", "url": "http://example.com"}] # Results for brave
        ]
        
        self.agent.search(query, "fact_check_first")
        
        # It should have been called twice
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
        self.agent.search(query, "web_deep_dive")
        
        self.assertEqual(self.mock_tool_manager.search_web.call_count, 3)
        calls = self.mock_tool_manager.search_web.call_args_list
        # Order of calls doesn't strictly matter here, but the tools used do
        tools_called = {call.kwargs['tool'] for call in calls}
        self.assertEqual(tools_called, {"brave", "news_api", "reddit_api"})


if __name__ == '__main__':
    unittest.main()
