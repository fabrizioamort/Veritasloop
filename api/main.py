
import contextlib
import json
import socket
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Load environment variables from .env file
load_dotenv()

# Import centralized settings and validation
from src.config.env_validator import validate_all
from src.config.settings import settings


# Pydantic model for WebSocket request validation
class VerificationRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=10000)
    type: str = Field(default="Text", pattern="^(Text|URL)$")
    max_iterations: int = Field(default=3, ge=1, le=10)
    max_searches: int = Field(default=-1, ge=-1, le=100)
    language: str = Field(default="Italian", pattern="^(Italian|English)$")
    proPersonality: str = Field(default="ASSERTIVE", pattern="^(PASSIVE|ASSERTIVE|AGGRESSIVE)$")
    contraPersonality: str = Field(default="ASSERTIVE", pattern="^(PASSIVE|ASSERTIVE|AGGRESSIVE)$")

from api.server_utils import sanitize_error_message, serialize_for_json
from src.models.schemas import Claim, Entities, GraphState
from src.orchestrator.graph import enable_tracing, get_app
from src.utils.claim_extractor import extract_from_url
from src.utils.logger import get_logger

# Configure logger
logger = get_logger("api")

def check_phoenix_running() -> bool:
    """Check if Phoenix server is already running."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((settings.phoenix_host, settings.phoenix_port))
        sock.close()
        return result == 0
    except Exception:
        return False

def start_phoenix_server():
    """Start Phoenix server with persistent storage if not already running."""
    if not settings.phoenix_enabled:
        logger.info("Phoenix tracing is disabled (PHOENIX_ENABLED=false)")
        return False

    if check_phoenix_running():
        logger.info(f"Phoenix server already running at {settings.phoenix_url}")
        return True

    try:
        import phoenix as px

        # Create directory for Phoenix data
        phoenix_dir = Path("data/phoenix")
        phoenix_dir.mkdir(parents=True, exist_ok=True)

        # Database file for persistent traces
        db_path = phoenix_dir / "traces.db"

        # Launch Phoenix server with persistent storage
        px.launch_app(
            database_url=f"sqlite:///{db_path.absolute()}"
        )

        logger.info(f"Phoenix server started at {settings.phoenix_url} with persistent storage at {db_path}")
        return True
    except ImportError:
        logger.warning("Phoenix not available. Install with: pip install arize-phoenix openinference-instrumentation-langchain")
        return False
    except Exception as e:
        logger.error(f"Failed to start Phoenix server: {e}")
        return False

# Start Phoenix server and enable tracing for the React UI
phoenix_started = start_phoenix_server()
if phoenix_started:
    enable_tracing()
    logger.info(f"Phoenix tracing enabled for API server - traces available at {settings.phoenix_url}")
else:
    logger.warning("Phoenix tracing not enabled - Phoenix server failed to start")

app = FastAPI(title="VeritasLoop API")

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    """Validate environment variables on application startup."""
    logger.info("Running environment validation...")
    validate_all()
    logger.info("Environment validation completed - application ready to start")

# Configure CORS using settings
logger.info(f"Configuring CORS with allowed origins: {settings.allowed_origins_list}")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to only necessary methods
    allow_headers=["Content-Type"],   # Restrict to only necessary headers
    max_age=3600,
)

@app.get("/")
async def root():
    return {"status": "online", "service": "VeritasLoop API"}

@app.websocket("/ws/verify")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        # Wait for initialization message and validate it
        data = await websocket.receive_text()

        try:
            request = VerificationRequest(**json.loads(data))
        except ValidationError as e:
            # Use the sanitizer, which logs the detailed error
            safe_message = sanitize_error_message(e, "Invalid request: please check your parameters.")
            await websocket.send_json({
                "type": "error",
                "message": safe_message
            })
            await websocket.close(code=4000) # Custom close code for validation error
            return

        logger.info(f"Received valid verification request: {request.type} (max_iterations={request.max_iterations}, max_searches={request.max_searches}, pro={request.proPersonality}, contra={request.contraPersonality})")

        # 1. Extract Claim
        await websocket.send_json({
            "type": "status",
            "message": "Analyzing input...",
            "node": "initialize"
        })

        if request.type == "URL":
            try:
                claim = extract_from_url(request.input)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": sanitize_error_message(e, "Failed to process the provided URL.")
                })
                return
        else:
            claim = Claim(
                raw_input=request.input,
                core_claim=request.input,  # Will be refined by extraction agent if needed
                entities=Entities()
            )

        # 2. Initialize State
        initial_state: GraphState = {
            "claim": claim,
            "messages": [],
            "pro_sources": [],
            "contra_sources": [],
            "round_count": 0,
            "max_iterations": request.max_iterations,
            "max_searches": request.max_searches,
            "language": request.language,
            "pro_personality": request.proPersonality,
            "contra_personality": request.contraPersonality
        }

        # 3. Stream from LangGraph
        graph_app = get_app()

        await websocket.send_json({
            "type": "status",
            "message": "Starting Multi-Agent System...",
            "node": "graph_start"
        })

        # Iterate through the graph stream
        for update in graph_app.stream(initial_state):
            # update is a dict where keys are node names and values are state updates
            node_name = list(update.keys())[0]
            node_data = update[node_name]

            # Prepare payload for frontend
            payload = {
                "type": "update",
                "node": node_name,
                "data": serialize_for_json(node_data)
            }

            # Send specific event types based on node
            if node_name == "extract":
                payload["description"] = "Claim extracted and analyzed"
            elif node_name == "pro_research":
                payload["description"] = "PRO Agent searching for evidence"
            elif node_name == "contra_research":
                payload["description"] = "CONTRA Agent finding contradictions"
            elif node_name == "contra_node":
                round_num = node_data.get('round_count', 0)
                payload["description"] = f"Debate Round {round_num}/3 (CONTRA)"
            elif node_name == "pro_node":
                payload["description"] = "Debate Round (PRO)"
            elif node_name == "debate":
                round_num = node_data.get('round_count', 0)
                payload["description"] = f"Debate Round {round_num}/3"
            elif node_name == "judge":
                payload["type"] = "verdict"
                payload["description"] = "Final Verdict Reached"
                if "verdict" in node_data:
                    payload["data"] = serialize_for_json(node_data["verdict"])

            await websocket.send_json(payload)

        # 4. Completion
        await websocket.send_json({
            "type": "complete",
            "message": "Verification finished"
        })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        safe_message = sanitize_error_message(e, "An unexpected WebSocket error occurred.")
        with contextlib.suppress(Exception):
            # Try to send error message, but connection might be already closed
            await websocket.send_json({
                "type": "error",
                "message": safe_message
            })
