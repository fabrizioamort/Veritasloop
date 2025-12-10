"""
Defines the JUDGE agent for the VeritasLoop system.

The JUDGE agent evaluates the debate between the PRO and CONTRA agents
and delivers a final, structured verdict on the authenticity of a news claim.
"""
import json
import time
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from pydantic import BaseModel
from langchain_core.utils.function_calling import convert_to_openai_function

from src.agents.base_agent import BaseAgent
from src.models.schemas import (AgentType, DebateMessage, GraphState, MessageType,
                              Verdict, VerdictType)
from src.utils.tool_manager import ToolManager


class JudgeAgent(BaseAgent):
    """
    The JUDGE agent, responsible for evaluating the debate and producing a final verdict.

    This agent does not perform searches. It analyzes the arguments, evidence, and
    logical consistency of the PRO and CONTRA agents to make a final judgment.
    """

    def __init__(self, llm: Any, tool_manager: ToolManager):
        """
        Initializes the JudgeAgent.

        Args:
            llm (Any): The language model instance for evaluation.
            tool_manager (ToolManager): An instance of ToolManager (not used for searching).
        """
        super().__init__(llm, tool_manager, "JUDGE")
        self.system_prompt = self._construct_system_prompt()
        self.parser = JsonOutputFunctionsParser()
        self.chain = self.llm.bind(
            functions=[convert_to_openai_function(Verdict)],
            function_call={"name": "Verdict"},
        ) | self.parser


    def _construct_system_prompt(self) -> str:
        """Constructs the system prompt for the JUDGE agent."""
        return """
You are an impartial Supreme Court judge tasked with evaluating a debate on the veracity of a news claim.
Your role is to analyze the arguments presented by a PRO agent and a CONTRA agent and deliver a final, reasoned verdict.

**Your Task:**
1.  **Analyze the full debate transcript:** Review the arguments, evidence (sources), and rebuttals from both agents.
2.  **Evaluate Source Quality:** Assess the reliability and relevance of the sources provided by each agent. Official sources (government, major news agencies) are generally more reliable than social media or blogs.
3.  **Assess Logical Coherence:** Identify any logical fallacies, inconsistencies, or unsupported claims in the agents' arguments.
4.  **Deliver a Structured Verdict:** Based on your analysis, you must choose one of the following verdict categories and provide a comprehensive justification in JSON format.

**Verdict Categories:**
-   **VERO (True):** The claim is substantially true, supported by strong, independent evidence.
-   **FALSO (False):** The claim is demonstrably false, and there is credible evidence to disprove it.
-   **PARZIALMENTE_VERO (Partially True):** The claim contains a kernel of truth but is misleading, exaggerated, or missing crucial details.
-   **CONTESTO_MANCANTE (Missing Context):** The claim, while perhaps technically accurate, is presented in a way that is misleading without additional context.
-   **NON_VERIFICABILE (Cannot Verify):** There is insufficient credible evidence to either confirm or deny the claim.

**Instructions for Analysis:**
-   Your `summary` must be in the requested language (default Italian).
-   Base your `confidence_score` on the quality and convergence of evidence. High confidence requires multiple, strong, independent sources.
-   In the `analysis`, be specific. For example, instead of "PRO had good sources," say "PRO cited an official government report which was highly persuasive."
-   Ensure `sources_used` includes a curated list of the most critical sources from the debate.
-   The `metadata` fields will be populated based on the provided debate history.
"""

    def _format_debate_history(self, state: GraphState) -> str:
        """Formats the debate history into a string for the LLM prompt."""
        history = []
        claim = state.get("claim")
        if claim:
            history.append(f"Initial Claim: {claim.core_claim}\n")

        messages = state.get("messages", [])
        for msg in messages:
            agent_name = msg.agent.value.lower() if hasattr(msg.agent, 'value') else str(msg.agent).lower()
            msg_type = msg.message_type.value.lower() if hasattr(msg.message_type, 'value') else str(msg.message_type).lower()
            history.append(f"Round {msg.round} - {agent_name} ({msg_type}):")
            history.append(msg.content)
            if msg.sources:
                history.append("Sources:")
                for source in msg.sources:
                    reliability = source.reliability.value.lower() if hasattr(source.reliability, 'value') else str(source.reliability).lower()
                    history.append(f"- {source.title}: {source.url} (Reliability: {reliability})")
            history.append("-" * 20)
        
        return "\n".join(history)

    def _calculate_metadata(self, state: GraphState) -> Dict:
        """Calculates metadata from the graph state."""
        start_time = state.get("start_time", time.time())
        processing_time = time.time() - start_time

        all_sources = set()
        messages = state.get("messages", [])
        for msg in messages:
            for source in msg.sources:
                all_sources.add(source.url)

        return {
            "processing_time_seconds": round(processing_time, 2),
            "rounds_completed": state.get("round_count", 0),
            "total_sources_checked": len(all_sources),
        }

    def think(self, state: GraphState) -> Dict:
        """
        The `think` method for the JUDGE evaluates the debate and returns the final verdict.
        """
        self.logger.info("JUDGE agent is evaluating the debate.")
        language = state.get("language", "Italian")
        
        debate_history_str = self._format_debate_history(state)
        debate_history_str += f"\n\nIMPORTANT: Your output must be in {language}."
        
        prompt = ChatPromptTemplate.from_messages(
            [("system", self.system_prompt), ("user", debate_history_str)]
        )
        
        chain = prompt | self.chain
        
        try:
            # Chain may return either a dict (from JsonOutputFunctionsParser) or a Verdict model (in tests)
            verdict_result = chain.invoke({})

            # Convert to dict if it's a Pydantic model
            if isinstance(verdict_result, Verdict):
                verdict_dict = verdict_result.model_dump()
            else:
                verdict_dict = verdict_result

            # Calculate and add metadata
            metadata = self._calculate_metadata(state)

            # Add metadata to the verdict dict
            if "metadata" not in verdict_dict:
                verdict_dict["metadata"] = {}

            verdict_dict["metadata"]["processing_time_seconds"] = metadata["processing_time_seconds"]
            verdict_dict["metadata"]["rounds_completed"] = metadata["rounds_completed"]
            verdict_dict["metadata"]["total_sources_checked"] = metadata["total_sources_checked"]

            self.logger.info(f"Verdict reached: {verdict_dict.get('verdict', 'UNKNOWN')} with confidence {verdict_dict.get('confidence_score', 0)}")

            # The final state update should be the verdict itself
            return {"verdict": verdict_dict}

        except Exception as e:
            self.logger.error(f"Error during verdict generation: {e}")
            # Fallback to a NON_VERIFICABILE verdict
            metadata = self._calculate_metadata(state)
            fallback_verdict = {
                "verdict": VerdictType.NON_VERIFICABILE,
                "confidence_score": 0.0,
                "summary": "An error occurred during the evaluation process. Unable to reach a verdict.",
                "analysis": {
                    "pro_strength": "N/A",
                    "contra_strength": "N/A",
                    "consensus_facts": [],
                    "disputed_points": [],
                },
                "sources_used": [],
                "metadata": metadata,
            }
            return {"verdict": fallback_verdict}

