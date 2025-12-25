
"""
This module contains the logic for a single round of debate between the PRO and CONTRA agents.
"""
from src.agents.contra_agent import ContraAgent
from src.agents.pro_agent import ProAgent
from src.models.schemas import GraphState
from src.utils.claim_extractor import get_llm
from src.utils.logger import get_logger, log_performance
from src.utils.tool_manager import ToolManager

logger = get_logger(__name__)

# Initialize needed resources for the isolated function if strictly necessary,
# but ideally these should be passed in or available.
# Since `debate_round` is a node function, it doesn't accept the agents as args easily in LangGraph's basic setup
# without using `partial` or global scope.
# We will duplicate the init here for safety or we could import the instances from graph.py if we avoid circular imports.
# To avoid circular imports (since graph imports debate), we re-instantiate or use a singleton pattern.
# For MVP simplicity, we re-instantiate.

def pro_turn(state: GraphState) -> GraphState:
    """
    Executes PRO agent's turn in the debate.
    Increments round count (start of new round) and produces argument/defense.
    """
    # Increment round count at the start of PRO's turn (start of a new round cycle)
    new_round = state['round_count'] + 1
    logger.info(f"Starting debate round {new_round} - PRO Turn")

    with log_performance(f"pro_turn_round_{new_round}", logger):
        # Initialize resources
        llm = get_llm()
        tool_manager = ToolManager()

        # Get personality from state
        personality = state.get('pro_personality', 'ASSERTIVE')
        pro_agent = ProAgent(llm, tool_manager, personality=personality)

        logger.info(f"PRO agent preparing argument (round {new_round})")

        # Calculate argument
        message = pro_agent.think(state)

        logger.debug(
            "PRO argument complete",
            extra={
                "sources": len(message.sources),
                "confidence": message.confidence
            }
        )

        return {
            "messages": [message],
            "round_count": new_round
        }

def contra_turn(state: GraphState) -> GraphState:
    """
    Executes CONTRA agent's turn in the debate.
    CONTRA rebuts PRO's argument.
    """
    round_num = state['round_count']
    logger.info(f"Continuing debate round {round_num} - CONTRA Turn")

    with log_performance(f"contra_turn_round_{round_num}", logger):
        # Initialize resources
        llm = get_llm()
        tool_manager = ToolManager()

        # Get personality from state
        personality = state.get('contra_personality', 'ASSERTIVE')
        contra_agent = ContraAgent(llm, tool_manager, personality=personality)

        logger.info(f"CONTRA agent preparing rebuttal (round {round_num})")

        # Calculate rebuttal
        # Note: Pro's message was just added to state['messages'] by the previous node,
        # so contra_agent.think(state) will see it automatically.
        message = contra_agent.think(state)

        logger.debug(
            "CONTRA rebuttal complete",
            extra={
                "sources": len(message.sources),
                "confidence": message.confidence
            }
        )

        # We do NOT increment round count here, as CONTRA finishes the round started by PRO
        return {
            "messages": [message]
        }
