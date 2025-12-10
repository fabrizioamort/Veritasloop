"""
Unit tests for the JudgeAgent class.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from src.agents.judge_agent import JudgeAgent
from src.models.schemas import (AgentType, Claim, ClaimCategory, DebateMessage,
                              Entities, GraphState, MessageType, Reliability,
                              Source, Verdict, VerdictType)
from src.utils.tool_manager import ToolManager


class TestJudgeAgent(unittest.TestCase):
    """Test suite for the JudgeAgent."""

    def setUp(self):
        """Set up the test environment."""
        self.mock_llm = MagicMock()
        self.mock_tool_manager = MagicMock(spec=ToolManager)
        self.judge_agent = JudgeAgent(llm=self.mock_llm, tool_manager=self.mock_tool_manager)

        # Sample data for tests
        self.claim = Claim(
            raw_input="Test claim",
            core_claim="This is a test claim.",
            entities=Entities(people=[], places=[], dates=[], organizations=[]),
            category=ClaimCategory.OTHER,
        )
        self.pro_message = DebateMessage(
            round=1,
            agent=AgentType.PRO,
            message_type=MessageType.ARGUMENT,
            content="The claim is true.",
            sources=[
                Source(url="http://example.com/pro", title="Pro Source", snippet="...", reliability=Reliability.HIGH)
            ],
            confidence=90.0,
        )
        self.contra_message = DebateMessage(
            round=1,
            agent=AgentType.CONTRA,
            message_type=MessageType.REBUTTAL,
            content="The claim is false.",
            sources=[
                Source(url="http://example.com/contra", title="Contra Source", snippet="...", reliability=Reliability.MEDIUM)
            ],
            confidence=85.0,
        )
        self.graph_state: GraphState = {
            "claim": self.claim,
            "messages": [self.pro_message, self.contra_message],
            "pro_sources": self.pro_message.sources,
            "contra_sources": self.contra_message.sources,
            "round_count": 1,
            "start_time": time.time() - 60, # 60 seconds ago
        }

    def test_initialization(self):
        """Test that the JudgeAgent is initialized correctly."""
        self.assertIsInstance(self.judge_agent, JudgeAgent)
        self.assertEqual(self.judge_agent.logger.name, "Agent.JUDGE")
        self.assertIn("You are an impartial Supreme Court judge", self.judge_agent.system_prompt)

    def test_format_debate_history(self):
        """Test the _format_debate_history method."""
        formatted_history = self.judge_agent._format_debate_history(self.graph_state)
        self.assertIn("Initial Claim: This is a test claim.", formatted_history)
        self.assertIn("Round 1 - pro (argument):", formatted_history)
        self.assertIn("The claim is true.", formatted_history)
        self.assertIn("- Pro Source: http://example.com/pro (Reliability: high)", formatted_history)
        self.assertIn("Round 1 - contra (rebuttal):", formatted_history)
        self.assertIn("The claim is false.", formatted_history)
        self.assertIn("- Contra Source: http://example.com/contra (Reliability: medium)", formatted_history)

    def test_calculate_metadata(self):
        """Test the _calculate_metadata method."""
        metadata = self.judge_agent._calculate_metadata(self.graph_state)
        self.assertGreater(metadata["processing_time_seconds"], 55) # Should be around 60
        self.assertEqual(metadata["rounds_completed"], 1)
        self.assertEqual(metadata["total_sources_checked"], 2)

    @patch("src.agents.judge_agent.ChatPromptTemplate")
    def test_think_evaluation_success(self, mock_prompt_template_class):
        """Test the think method for successful verdict generation."""
        # Mock the LLM chain to return a valid Verdict object
        mock_verdict_dict = {
            "verdict": "PARZIALMENTE_VERO",
            "confidence_score": 75.0,
            "summary": "Il claim è parzialmente vero.",
            "analysis": {
                "pro_strength": "Good sources.",
                "contra_strength": "Pointed out missing context.",
                "consensus_facts": ["Something is true."],
                "disputed_points": ["The impact is debated."],
            },
            "sources_used": [],
            "metadata": {
                "processing_time_seconds": 0, # This will be updated
                "rounds_completed": 0, # This will be updated
                "total_sources_checked": 0, # This will be updated
            },
        }
        mock_verdict = Verdict.model_validate(mock_verdict_dict)

        # Create a mock prompt that when piped with chain returns a callable that returns verdict
        mock_prompt = MagicMock()
        mock_chain_result = MagicMock()
        mock_chain_result.invoke.return_value = mock_verdict
        mock_prompt.__or__.return_value = mock_chain_result
        
        mock_prompt_template_class.from_messages.return_value = mock_prompt

        # Call the think method
        result = self.judge_agent.think(self.graph_state)

        # Assertions
        self.assertIn("verdict", result)
        
        verdict_result = Verdict.model_validate(result["verdict"])
        self.assertEqual(verdict_result.verdict, VerdictType.PARZIALMENTE_VERO)
        self.assertEqual(verdict_result.confidence_score, 75.0)
        self.assertGreater(verdict_result.metadata.processing_time_seconds, 55)
        self.assertEqual(verdict_result.metadata.rounds_completed, 1)
        self.assertEqual(verdict_result.metadata.total_sources_checked, 2)
        self.assertEqual(verdict_result.summary, "Il claim è parzialmente vero.")

    @patch("src.agents.judge_agent.ChatPromptTemplate")
    def test_think_evaluation_error(self, mock_prompt_template_class):
        """Test the think method handles errors and returns a fallback verdict."""
        # Create a mock prompt that when piped with chain raises an exception
        mock_prompt = MagicMock()
        mock_chain_result = MagicMock()
        mock_chain_result.invoke.side_effect = Exception("LLM failed")
        mock_prompt.__or__.return_value = mock_chain_result
        
        mock_prompt_template_class.from_messages.return_value = mock_prompt

        # Call the think method
        result = self.judge_agent.think(self.graph_state)

        # Assertions
        self.assertIn("verdict", result)
        
        verdict_result = Verdict.model_validate(result["verdict"])
        self.assertEqual(verdict_result.verdict, VerdictType.NON_VERIFICABILE)
        self.assertEqual(verdict_result.confidence_score, 0.0)
        self.assertIn("An error occurred", verdict_result.summary)
        self.assertGreater(verdict_result.metadata.processing_time_seconds, 55)


if __name__ == "__main__":
    unittest.main()
