
"""
This module contains the logic for a single round of debate between the PRO and CONTRA agents.
"""
from src.models.schemas import GraphState
from src.agents.pro_agent import ProAgent
from src.agents.contra_agent import ContraAgent
from src.utils.tool_manager import ToolManager
from src.utils.claim_extractor import get_llm
from src.utils.logger import get_logger, log_performance

logger = get_logger(__name__)

# Initialize needed resources for the isolated function if strictly necessary,
# but ideally these should be passed in or available. 
# Since `debate_round` is a node function, it doesn't accept the agents as args easily in LangGraph's basic setup
# without using `partial` or global scope. 
# We will duplicate the init here for safety or we could import the instances from graph.py if we avoid circular imports.
# To avoid circular imports (since graph imports debate), we re-instantiate or use a singleton pattern.
# For MVP simplicity, we re-instantiate.

def debate_round(state: GraphState) -> GraphState:
    """
    Executes a single round of debate, where the CONTRA agent rebuts the PRO's
    last argument, and the PRO agent defends against the rebuttal.
    """
    round_num = state['round_count'] + 1
    logger.info(f"Starting debate round {round_num}")

    with log_performance(f"debate_round_{round_num}", logger):
        # Lazy init to avoid top-level cost/issues
        llm = get_llm()
        tool_manager = ToolManager()
        pro_agent = ProAgent(llm, tool_manager)
        contra_agent = ContraAgent(llm, tool_manager)

        # 1. CONTRA Agent Rebuttal
        # In a debate, CONTRA responds to what PRO just said (or general claim if first round,
        # but strictly this node runs after initial research where both spoke).
        # We assume 'messages' has the history.

        logger.info(f"CONTRA agent preparing rebuttal (round {round_num})")
        with log_performance(f"contra_rebuttal_round_{round_num}", logger):
            contra_message = contra_agent.think(state)
            logger.debug(
                f"CONTRA rebuttal complete",
                extra={
                    "sources": len(contra_message.sources),
                    "confidence": contra_message.confidence
                }
            )

        # Note: State is not updated yet, so Pro agent sees old state + what we might pass manually?
        # In this logic, Pro responds to Contra.
        # But if we don't update state, Pro.think(state) won't see Contra's message in state['messages'].
        # We must manually append strictly for the Pro agent's context, OR rely on internal logic.
        # To be clean, we can create a temporary state or just pass the message.
        # But ProAgent.think takes `state`.
        # Let's create a temporary copy of messages for Pro.

        current_messages = list(state['messages'])
        current_messages.append(contra_message)
        temp_state = state.copy()
        temp_state['messages'] = current_messages

        # 2. PRO Agent Defense
        # PRO responds to CONTRA's latest rebuttal
        logger.info(f"PRO agent preparing defense (round {round_num})")
        with log_performance(f"pro_defense_round_{round_num}", logger):
            pro_message = pro_agent.think(temp_state)
            logger.debug(
                f"PRO defense complete",
                extra={
                    "sources": len(pro_message.sources),
                    "confidence": pro_message.confidence
                }
            )

        logger.info(f"Debate round {round_num} complete")

        return {
            "messages": [pro_message, contra_message],
            "round_count": state['round_count'] + 1
        }
