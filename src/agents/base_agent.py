"""
Defines the BaseAgent abstract class for all agents in the VeritasLoop system.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from src.models.schemas import DebateMessage, GraphState
from src.utils.tool_manager import ToolManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BaseAgent(ABC):
    """
    An abstract base class for creating specific types of agents (PRO, CONTRA, JUDGE).

    This class provides a common structure for agents, including initialization
    with a language model and a tool manager, and defines the core methods
    that every agent must implement.
    """

    def __init__(self, llm: Any, tool_manager: ToolManager, agent_name: str):
        """
        Initializes the BaseAgent.

        Args:
            llm (Any): The language model instance to be used for generating responses.
            tool_manager (ToolManager): An instance of the ToolManager for accessing tools.
            agent_name (str): The name of the agent, used for logging.
        """
        self.llm = llm
        self.tools = tool_manager
        self.logger = logging.getLogger(f"Agent.{agent_name}")
        self.search_count = 0  # Track number of searches performed
        self.logger.info(f"Initialized {agent_name} agent.")

    @abstractmethod
    def think(self, state: GraphState) -> DebateMessage:
        """
        The core logic of the agent. This method should be implemented by subclasses
        to define the agent's behavior in response to the current state.

        Args:
            state (GraphState): The current state of the debate graph.

        Returns:
            DebateMessage: A message containing the agent's response, sources, and confidence.
        """
        pass

    def search(self, query: str, strategy: str, max_searches: int = -1) -> List[Dict]:
        """
        Performs a search using a tiered strategy.

        The strategy determines which tools to use and in what order.

        Args:
            query (str): The search query.
            strategy (str): The search strategy to employ (e.g., 'fact_check_first', 'web_deep_dive').
            max_searches (int): Maximum number of searches allowed. -1 means unlimited.

        Returns:
            List[Dict]: A list of search results.
        """
        # Check if search limit has been reached
        if max_searches > 0 and self.search_count >= max_searches:
            self.logger.warning(f"Search limit reached ({max_searches}). Skipping search for '{query}'")
            return []

        self.logger.info(f"Performing search {self.search_count + 1} for '{query}' with strategy '{strategy}'")
        self.search_count += 1

        if strategy == 'fact_check_first':
            # Tier 1: Fact-Check Direct (only if credentials are available)
            google_pse_available = bool(os.getenv("GOOGLE_PSE_API_KEY") and os.getenv("GOOGLE_PSE_CX"))

            if google_pse_available:
                results = self.tools.search_web(query, tool="google_pse_factcheck")
                if results:
                    return results

            # Tier 2: Broad Web Search (fallback)
            return self.tools.search_web(query, tool="brave")

        elif strategy == 'web_deep_dive':
            # Tier 1: Broad Web Search
            results = self.tools.search_web(query, tool="brave")
            # Tier 2: Try DuckDuckGo as alternative
            # Only do the second search if we haven't hit the limit
            if max_searches <= 0 or self.search_count < max_searches:
                self.search_count += 1
                results.extend(self.tools.search_web(query, tool="duckduckgo"))
            return results

        else: # Default basic search
            return self.tools.search_web(query, tool="brave")
