import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse, AssistantSections
from .multi_source_rag import build_graph

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

# Variables to store graph and session data
graph = None
SESSION_CTX = {}

# Root API endpoint (used to check if server is running)
@app.get("/")
def root():
    return {
        "name": "Holos Agri Assistant",
        "status": "ok",
        "version": "langgraph",
        "rag_available": True
    }

# Chat endpoint - main function for chatbot requests
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    ##print("in chat")
    # Get previous session context (if any)
    prior = SESSION_CTX.get(req.session_id, {})
    # Merge new context with previous one
    merged_context = {**prior, **(req.context or {})}

    # Build the RAG (Retrieval-Augmented Generation) graph only once
    # This prevents errors during import and speeds up future requests
    global graph
    if graph is None:
        graph = build_graph()

    # Prepare input for the RAG model
    state_in = {
        "session_id": req.session_id,
        "message": req.message,
        "context": merged_context
    }

    # Run the graph (process input and get response)
    state_out = graph.invoke(state_in)

    # Save updated context for the current session
    if "context" in state_out:
        SESSION_CTX[req.session_id] = state_out["context"]

    # Extract follow-up questions or missing info
    missing = state_out.get("missing") or []
    followup = state_out.get("followup") or (" ".join(missing) if missing else None)
    # Extract detailed response sections (like weather, data insights, etc.)
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
    """ return ChatResponse(
        session_id="1",
        reply="test"
    )
 """