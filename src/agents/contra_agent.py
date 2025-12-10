"""
Defines the ContraAgent class, responsible for challenging claims and providing skeptical analysis.
"""

from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseAgent
from src.models.schemas import (
    GraphState,
    DebateMessage,
    AgentType,
    MessageType,
    Reliability,
    Source
)
from src.utils.tool_manager import ToolManager


class ContraAgent(BaseAgent):
    """
    The CONTRA Agent (The Skeptic).
    
    Role: Investigative journalist challenging the claim.
    Personality: Skeptical, detail-oriented, looks for omissions and context.
    """

    def __init__(self, llm: Any, tool_manager: ToolManager):
        """
        Initialize the CONTRA Agent.
        
        Args:
            llm: The language model to use.
            tool_manager: The tool manager for search and verification.
        """
        super().__init__(llm, tool_manager, agent_name="CONTRA")
        
        self.system_prompt = """
You are a sharp, skeptical investigative journalist participating in a live debate.
Your goal is to challenge the news claim and expose any weaknesses, exaggerations, or missing context.

Voice and Tone:
- Use a natural, conversational, and questioning tone.
- Don't just list facts; tell a story about what's missing or wrong.
- Directly engage with the PRO agent's arguments (e.g., "Capisco l'entusiasmo del mio collega, ma...", "C'è un dettaglio fondamentale che è stato omesso...").
- Integrate your sources naturally (e.g., "Guardando i dati di fact-checking di...", "Diversi esperti su [Fonte] hanno chiarito che...").
- Be professional but relentless in seeking the truth. Avoid being rude, but be firm.

If the claim is TRUE:
- Focus on nuance. Is the headline misleading? Is the context correct? 
- "Sì, è vero, ma attenzione a non generalizzare..."

IMPORTANT: Be concise. Summarize your response in less than 500 characters.
IMPORTANT: Your output must be in the language specified in the user prompt.
"""

    def think(self, state: GraphState) -> DebateMessage:
        """
        Process the current state and generate a skeptical response.

        Args:
            state: The current state of the debate.

        Returns:
            DebateMessage: The agent's argument or rebuttal.
        """
        self.logger.info(f"CONTRA Agent thinking... Round {state['round_count']}")

        claim = state['claim']
        messages = state['messages']
        max_searches = state.get('max_searches', -1)  # Get max_searches from state, default unlimited
        language = state.get('language', 'Italian')

        # Determine if this is initial research (Round 0) or a rebuttal
        is_initial_round = state['round_count'] == 0

        # 1. Research Phase
        search_query = f"fake news {claim.core_claim}" if is_initial_round else f"contradiction {claim.core_claim}"

        # CONTRA strategy: FactCheck -> Social -> Blogs (simulated by broad search)
        # We'll use a mix of strategies.
        search_results = self.search(search_query, strategy="fact_check_first", max_searches=max_searches)

        # Also try to find specific contradictions if we have previous messages
        if not is_initial_round and messages:
            last_message = messages[-1]
            if last_message.agent == AgentType.PRO:
                # Search for counter-evidence to PRO's specific points
                # This is a simplification; a real agent would extract points first
                rebuttal_query = f"debunk {claim.core_claim}"
                more_results = self.search(rebuttal_query, strategy="web_deep_dive", max_searches=max_searches)
                search_results.extend(more_results)

        # Deduplicate results based on URL
        unique_results = {r['url']: r for r in search_results}.values()
        
        # Convert search results to Source objects
        sources = []
        for res in unique_results:
            # Simple reliability mapping for now
            reliability = Reliability.MEDIUM
            if "snopes" in res['url'] or "factcheck" in res['url'] or "bufale" in res['url']:
                reliability = Reliability.HIGH
            
            sources.append(Source(
                url=res['url'],
                title=res.get('title', 'Unknown Title'),
                snippet=res.get('snippet', ''),
                reliability=reliability,
                agent=AgentType.CONTRA
            ))
            
        # Limit sources to top 5 for context window
        top_sources = sources[:5]
        
        # 2. Argument Generation Phase
        formatted_sources = "\n".join([f"- {s.title}: {s.snippet} ({s.url})" for s in top_sources])
        
        if is_initial_round:
            user_prompt = f"""
            Analyze this claim: "{claim.core_claim}"
            Original input: "{claim.raw_input}"
            
            Available sources:
            {formatted_sources}
            
            Generate an initial skeptical opening statement for the debate. 
            Set the stage by questioning the validity or context of the claim.
            Speak naturally and engage the audience.
            """
            msg_type = MessageType.ARGUMENT
        else:
            last_msg = messages[-1]
            user_prompt = f"""
            The PRO agent argued:
            "{last_msg.content}"
            
            Claim: "{claim.core_claim}"
            
            Available sources:
            {formatted_sources}
            
            Generate a rebuttal. Directly address the PRO agent's points.
            Point out logical fallacies, missing context, or contradictory evidence using a conversational but critical tone.
            """
            msg_type = MessageType.REBUTTAL

        user_prompt += f"\n\nIMPORTANT: Your output must be in {language}."

        messages_payload = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages_payload)
        content = response.content
        
        # Calculate a simple confidence score (mock logic)
        # In a real system, the LLM would output this
        confidence = 70.0 if top_sources else 30.0
        
        return DebateMessage(
            round=state['round_count'] + 1,
            agent=AgentType.CONTRA,
            message_type=msg_type,
            content=content,
            sources=top_sources,
            confidence=confidence
        )

    def _detect_fallacies(self, argument: str) -> List[str]:
        """
        Helper to detect logical fallacies in an argument.
        
        Args:
            argument: The text to analyze.
            
        Returns:
            List of detected fallacies.
        """
        # This is a placeholder for a specific LLM call to detect fallacies
        # For MVP, we might just include this instruction in the main prompt
        pass
