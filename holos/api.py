import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse, AssistantSections
from .simple_rag import process_chat

# Load environment variables from .env file in the project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Create FastAPI app instance
app = FastAPI(title="Holos Agri Assistant")

# Allow frontend (like Streamlit) to connect to backend (CORS setup)
origins = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Which websites can connect
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],            # Allow all headers
)

# Store session data
SESSION_CTX = {}
CHAT_HISTORY = {}


# Root API endpoint (used to check if server is running)
@app.get("/")
def root():
    return {
        "name": "Holos Agri Assistant",
        "status": "ok",
        "version": "simple",
        "rag_available": True
    }

# Chat endpoint - main function for chatbot requests
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Get and merge context
    prior = SESSION_CTX.get(req.session_id, {})
    merged_context = {**prior, **(req.context or {})}

    # Process the chat message
    # --- Maintain short-term memory (conversation history) ---
    history = CHAT_HISTORY.get(req.session_id, [])

    state_out = process_chat(
        req.message,
        req.session_id,
        merged_context,
        history
    )

    # Save updated history (keep last 4 exchanges)
    history.append({"user": req.message, "bot": state_out.get("reply", "")})
    CHAT_HISTORY[req.session_id] = history[-4:]


    # Save updated context for the current session
    if "context" in state_out:
        SESSION_CTX[req.session_id] = state_out["context"]

    # Extract follow-up questions or missing info
    missing = state_out.get("missing") or []
    followup = state_out.get("followup") or (" ".join(missing) if missing else None)
    
    # Extract detailed response sections
    sections = state_out.get("sections") or {}

    # Validate and safely create the AssistantSections object
    try:
        sections_obj = AssistantSections(**sections) if sections else None
    except Exception as e:
        # Fallback if data structure is slightly off
        sections_obj = AssistantSections(
            rag_insights=sections.get("rag_insights"),
            csv_findings=sections.get("csv_findings"),
            weather_context=sections.get("weather_context"),
            csm_results=sections.get("csm_results"),
            assumptions=sections.get("assumptions"),
            sources=sections.get("sources")
        )
    
    # Return chatbot response back to frontend
    return ChatResponse(
        session_id=req.session_id,
        reply=state_out.get("reply", ""),  # Main chatbot reply
        followup=followup,                 # Follow-up prompt if needed
        sections=sections_obj              # Detailed result sections
    )
