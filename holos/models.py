from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# -------------------------------------------------------
# Model: ChatRequest
# -------------------------------------------------------
# Purpose:
# Represents the input that the chatbot API receives from the user.
# It includes:
# - session_id: unique identifier for the chat session
# - message: user's question or input text
# - context: additional information (like crop, region, soil, etc.)
class ChatRequest(BaseModel):
    session_id: str                      # Unique session key for tracking the conversation
    message: str                         # The user’s input message
    context: Optional[Dict[str, Any]] = None  # Optional background info (e.g., crop, region, season)


# -------------------------------------------------------
# Model: AssistantSections
# -------------------------------------------------------
# Purpose:
# Represents structured parts of the chatbot's detailed answer.
# These sections organize insights from various data sources.
class AssistantSections(BaseModel):
    rag_insights: Optional[List[Dict[str, Any]]] = None   # Insights retrieved from RAG (retrieval-augmented generation)
    csv_findings: Optional[Dict[str, Any]] = None         # Data summaries from CSV datasets
    weather_context: Optional[Dict[str, Any]] = None      # Weather data or forecasts
    csm_results: Optional[Dict[str, Any]] = None          # Crop Simulation Model (CSM) results
    recommendations: Optional[str] = None                 # AI-generated actionable advice or suggestions
    assumptions: Optional[Dict[str, Any]] = None          # Any assumptions used in the analysis
    sources: Optional[List[Dict[str, Any]]] = None        # References or documents used to support the reply


# -------------------------------------------------------
# Model: ChatResponse
# -------------------------------------------------------
# Purpose:
# Represents the response that the chatbot sends back to the user.
# It includes:
# - session_id: same as request (for continuity)
# - reply: main chatbot answer (text)
# - followup: optional next question for the user
# - sections: structured insights (AssistantSections)
class ChatResponse(BaseModel):
    session_id: str                         # Matches the request session ID
    reply: str                              # Main chatbot reply text
    followup: Optional[str] = None          # Optional next question for missing info
    sections: Optional[AssistantSections] = None  # Detailed structured answer parts
