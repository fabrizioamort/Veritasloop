
import json
import logging
import socket
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from src.orchestrator.graph import get_app, enable_tracing
from src.models.schemas import Claim, Entities, GraphState
from src.utils.claim_extractor import extract_from_url
from src.utils.logger import get_logger
from api.server_utils import serialize_for_json

# Configure logger
logger = get_logger("api")

def check_phoenix_running() -> bool:
    """Check if Phoenix server is already running on port 6006."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 6006))
        sock.close()
        return result == 0
    except Exception:
        return False

def start_phoenix_server():
    """Start Phoenix server with persistent storage if not already running."""
    if check_phoenix_running():
        logger.info("Phoenix server already running at http://localhost:6006")
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
            run_in_background=True,
            database_url=f"sqlite:///{db_path.absolute()}"
        )

        logger.info(f"Phoenix server started at http://localhost:6006 with persistent storage at {db_path}")
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
    logger.info("Phoenix tracing enabled for API server - traces available at http://localhost:6006")
else:
    logger.warning("Phoenix tracing not enabled - Phoenix server failed to start")

app = FastAPI(title="VeritasLoop API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "service": "VeritasLoop API"}

@app.websocket("/ws/verify")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        # Wait for initialization message
        data = await websocket.receive_text()
        request_data = json.loads(data)

        user_input = request_data.get("input")
        input_type = request_data.get("type", "Text")
        max_iterations = request_data.get("max_iterations", 3)
        max_searches = request_data.get("max_searches", -1)
        language = request_data.get("language", "Italian")

        logger.info(f"Received verification request: {input_type} (max_iterations={max_iterations}, max_searches={max_searches})")

        # 1. Extract Claim
        await websocket.send_json({
            "type": "status", 
            "message": "Analyzing input...", 
            "node": "initialize"
        })

        if input_type == "URL":
            try:
                claim = extract_from_url(user_input)
            except Exception as e:
                logger.error(f"Extraction failed: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Failed to extract content: {str(e)}"
                })
                return
        else:
            claim = Claim(
                raw_input=user_input,
                core_claim=user_input,  # Will be refined by extraction agent if needed
                entities=Entities()
            )

        # 2. Initialize State
        initial_state: GraphState = {
            "claim": claim,
            "messages": [],
            "pro_sources": [],
            "contra_sources": [],
            "round_count": 0,
            "max_iterations": max_iterations,
            "max_searches": max_searches,
            "language": language
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
            elif node_name == "debate":
                round_num = node_data.get('round_count', 0)
                payload["description"] = f"Debate Round {round_num}/3"
            elif node_name == "judge":
                payload["type"] = "verdict"
                payload["description"] = "Final Verdict Reached"
                # Extract the verdict from nested structure: node_data = {"verdict": {...}}
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
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Internal server error: {str(e)}"
            })
        except:
            pass  # Connection might be already closed
