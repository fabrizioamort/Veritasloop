
"""
Main orchestration graph for the VeritasLoop system.
Defines the state machine for the multi-agent debate and verification process.
"""

from langgraph.graph import StateGraph, START, END
from src.models.schemas import GraphState
from src.orchestrator.debate import contra_turn, pro_turn
from src.agents.pro_agent import ProAgent
from src.agents.contra_agent import ContraAgent
from src.agents.judge_agent import JudgeAgent
from src.utils.tool_manager import ToolManager
from src.utils.claim_extractor import extract_from_text, get_llm
from src.utils.logger import get_logger, log_performance

logger = get_logger(__name__)

# Global flag for tracing (set by CLI)
_tracing_enabled = False

# Initialize shared resources
# In a production app, these might be dependency-injected or initialized in a config module
# specific instance creation moved inside get_app or global scope but guarded

def extract_claim(state: GraphState) -> dict:
    """
    Node to extract the core claim from the user input.
    """
    logger.info("Starting claim extraction")

    with log_performance("extract_claim", logger):
        current_claim = state['claim']
        if not current_claim.core_claim or current_claim.core_claim == current_claim.raw_input:
            extracted = extract_from_text(current_claim.raw_input)
            logger.info(
                f"Claim extracted successfully",
                extra={
                    "core_claim": extracted.core_claim[:100],
                    "category": extracted.category,
                    "entity_count": len(extracted.entities.people) + len(extracted.entities.places)
                }
            )
            return {"claim": extracted}

    logger.debug("Claim already extracted, skipping")
    return {}

def should_continue(state: GraphState) -> str:
    """
    Determines whether the debate should continue or end.
    """
    round_count = state['round_count']
    max_iterations = state.get('max_iterations', 3)  # Default to 3 if not set
    logger.debug(f"Evaluating continuation at round {round_count}/{max_iterations}")

    if round_count >= max_iterations:
        logger.info(f"Debate ending: maximum rounds ({max_iterations}) reached")
        return "end"

    logger.info(f"Debate continuing to round {round_count + 1}")
    return "continue"

def enable_tracing():
    """
    Enable Phoenix tracing for the application.
    Should be called before get_app() to trace all agent operations.
    """
    global _tracing_enabled
    try:
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor

        # Register Phoenix tracer
        tracer_provider = register(
            project_name="veritasloop",
            endpoint="http://localhost:6006/v1/traces"
        )

        # Instrument LangChain
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

        _tracing_enabled = True
        logger.info("Phoenix tracing enabled successfully")
        return True
    except ImportError as e:
        logger.warning(f"Phoenix tracing not available: {e}")
        logger.warning("Install with: pip install arize-phoenix openinference-instrumentation-langchain")
        return False
    except Exception as e:
        logger.error(f"Failed to enable tracing: {e}")
        return False

def get_app():
    """
    Constructs and returns the LangGraph application.
    Initializes agents and standard tools.
    """
    # Initialize resources
    tool_manager = ToolManager()
    llm = get_llm()

    if _tracing_enabled:
        logger.info("Running with Phoenix observability enabled")

    # Initialize Judge Agent (doesn't need personality)
    judge_agent = JudgeAgent(llm=llm, tool_manager=tool_manager)

    def pro_research(state: GraphState) -> dict:
        # Create PRO agent with personality from state
        pro_personality = state.get('pro_personality', 'ASSERTIVE')
        pro_agent = ProAgent(llm=llm, tool_manager=tool_manager, personality=pro_personality)

        logger.info(f"PRO agent ({pro_agent.agent_display_name}) starting research phase")
        with log_performance("pro_research", logger):
            message = pro_agent.think(state)
            logger.info(
                f"PRO research complete",
                extra={
                    "sources_found": len(message.sources),
                    "confidence": message.confidence,
                    "personality": pro_personality
                }
            )
            # Return only the update. Messages is Annotated with add, so we return a list of new messages.
            return {"messages": [message]}

    def contra_research(state: GraphState) -> dict:
        # Create CONTRA agent with personality from state
        contra_personality = state.get('contra_personality', 'ASSERTIVE')
        contra_agent = ContraAgent(llm=llm, tool_manager=tool_manager, personality=contra_personality)

        logger.info(f"CONTRA agent ({contra_agent.agent_display_name}) starting research phase")
        with log_performance("contra_research", logger):
            message = contra_agent.think(state)
            logger.info(
                f"CONTRA research complete",
                extra={
                    "sources_found": len(message.sources),
                    "confidence": message.confidence,
                    "personality": contra_personality
                }
            )
            return {"messages": [message]}

    def judge_verdict(state: GraphState) -> dict:
        logger.info("JUDGE agent evaluating debate")
        with log_performance("judge_verdict", logger):
            # judge.think returns a dict like {'verdict': ...}
            verdict_result = judge_agent.think(state)
            if isinstance(verdict_result, dict):
                verdict = verdict_result.get("verdict", {})
                logger.info(
                    f"Verdict reached: {verdict.get('verdict', 'UNKNOWN')}",
                    extra={
                        "confidence": verdict.get("confidence_score", 0),
                        "sources_used": len(verdict.get("sources_used", []))
                    }
                )
                return verdict_result

        logger.warning("JUDGE returned empty verdict")
        return {}

    # Define the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("extract", extract_claim)
    workflow.add_node("pro_research", pro_research)
    workflow.add_node("contra_research", contra_research)
    
    # Split debate nodes
    workflow.add_node("contra_node", contra_turn)
    workflow.add_node("pro_node", pro_turn)
    
    workflow.add_node("judge", judge_verdict)

    # Define the edges
    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "pro_research")
    workflow.add_edge("pro_research", "contra_research")

    # Initial transition to debate loop (Pro speaks first in debate)
    workflow.add_edge("contra_research", "pro_node")
    
    # Pro speaks first in round, then Contra
    workflow.add_edge("pro_node", "contra_node")

    # After Contra speaks (end of round), check if we continue or go to judge
    workflow.add_conditional_edges(
        "contra_node",
        should_continue,
        {
            "continue": "pro_node",
            "end": "judge",
        },
    )

    workflow.add_edge("judge", END)
    
    return workflow.compile()

# For backwards compatibility or direct script usage:
if __name__ == "__main__":
    app = get_app()
