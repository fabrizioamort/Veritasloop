import logging
from typing import List, Dict, Any
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base_agent import BaseAgent
from src.models.schemas import (
    GraphState, DebateMessage, AgentType, MessageType, Source, Reliability
)
from src.utils.tool_manager import ToolManager
from src.config.personalities import get_agent_name, get_personality_prompt

class ProAgent(BaseAgent):
    """
    The PRO Agent defends the claim using institutional and authoritative sources.
    Personality can be PASSIVE, ASSERTIVE, or AGGRESSIVE.
    """

    def __init__(self, llm: Any, tool_manager: ToolManager, personality: str = "ASSERTIVE"):
        super().__init__(llm, tool_manager, agent_name="PRO")
        self.personality = personality
        self.agent_display_name = get_agent_name("PRO", personality)
        self.system_prompt = get_personality_prompt("PRO", personality)
        self.logger.info(f"PRO Agent initialized with personality: {personality} (Display name: {self.agent_display_name})")

    def think(self, state: GraphState) -> DebateMessage:
        """
        Generates an argument or defense for the claim based on search results.
        """
        claim = state['claim']
        messages = state['messages']
        max_searches = state.get('max_searches', -1)  # Get max_searches from state, default unlimited
        language = state.get('language', 'Italian')


        self.logger.info(f"Thinking about claim: {claim.core_claim}")

        # 1. Search Strategy
        # Prioritize official/institutional sources
        search_results = self.search(claim.core_claim, strategy="institutional", max_searches=max_searches)
        
        # 2. Construct Prompt
        formatted_results = "\n".join([
            f"- [{res.get('title', 'No Title')}]({res.get('url', 'No URL')}): {res.get('snippet', 'No snippet')}"
            for res in search_results[:5]
        ])

        history = "\n".join([f"{m.agent}: {m.content}" for m in messages])

        prompt = f"""
Claim: {claim.core_claim}
Category: {claim.category}

Search Results:
{formatted_results}

Debate History:
{history}

Based on the search results, construct a persuasive argument supporting the claim.
If this is a rebuttal, directly address the specific points raised by the CONTRA agent in the history.
Speak naturally, as if you are in a live debate. Don't simply list facts; weave them into a narrative.

IMPORTANT: Your output must be in {language}.
"""
        
        # 3. Call LLM with error handling
        try:
            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])
            content = response.content
            confidence = 0.7  # Default confidence on success
        except Exception as e:
            self.logger.error(f"LLM call failed in PRO agent: {e}")
            content = "Unable to generate argument due to technical difficulties. The system is experiencing issues communicating with the language model."
            confidence = 0.0

        # 4. Parse Sources (Simple heuristic for MVP)
        sources = []
        for res in search_results[:3]:
            # In a real implementation, we would check if the URL is actually used in the content
            sources.append(Source(
                url=res.get('url', 'http://unknown.com'),
                title=res.get('title', 'Unknown Source'),
                snippet=res.get('snippet', ''),
                reliability=Reliability.HIGH,
                agent=AgentType.PRO,
                timestamp=datetime.now()
            ))

        # Determine message type
        msg_type = MessageType.ARGUMENT if len(messages) == 0 else MessageType.DEFENSE

        return DebateMessage(
            round=state['round_count'],
            agent=AgentType.PRO,
            message_type=msg_type,
            content=str(content),
            sources=sources,
            confidence=confidence if confidence == 0.0 else 85.0  # 0 on error, 85 on success
        )

    def search(self, query: str, strategy: str, max_searches: int = -1) -> List[Dict]:
        """
        Overrides base search to implement institutional search strategy.
        """
        # Check if search limit has been reached
        if max_searches > 0 and self.search_count >= max_searches:
            self.logger.warning(f"Search limit reached ({max_searches}). Skipping search for '{query}'")
            return []

        self.logger.info(f"Performing search for '{query}' with strategy '{strategy}'")
        self.search_count += 1

        if strategy == "institutional":
            # In a real implementation, we might append "site:.gov" or "site:.edu" or use a specific tool
            # For MVP, we use the general web search but log the intent
            return self.tools.search_web(query, tool="brave")

        return super().search(query, strategy, max_searches)
