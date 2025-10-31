import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Clear any existing OPENAI_API_KEY from environment
if 'OPENAI_API_KEY' in os.environ:
    del os.environ['OPENAI_API_KEY']

# Load environment variables from .env file in the project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Verify the key is loaded
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"[DEBUG] API key loaded: {api_key[:20]}...{api_key[-10:]}")

# Import project modules (RAG retriever may not be importable if langchain/FAISS isn't installed)
try:
    from .rag import RAGRetriever
except Exception:
    # Fallback stub retriever so the API can run without a full RAG index
    class RAGRetriever:
        def __init__(self, *args, **kwargs):
            pass
        def retrieve(self, query, k=5):
            return []

try:
    from .csv_rag import CSVEngine
except Exception:
    class CSVEngine:
        def __init__(self, *args, **kwargs):
            pass
        def summarize(self, message, context):
            return {}

try:
    from .weather import load_weather
except Exception:
    def load_weather(context):
        return {}

try:
    from .csm_runner import CSMRunner
except Exception:
    class CSMRunner:
        def __init__(self, *args, **kwargs):
            pass
        def run(self, params):
            return {}

from .conversation import ensure_context

class ChatState(TypedDict, total=False):
    message: str
    session_id: str
    context: Dict[str, Any]
    missing: List[str]
    followup: str
    docs: List[Dict[str, Any]]
    csv: Dict[str, Any]
    weather: Dict[str, Any]
    csm: Dict[str, Any]
    reply: str
    sections: Dict[str, Any]

class ChatProcessor:
    def __init__(self):
        self.retriever = RAGRetriever()
        self.csv_engine = CSVEngine()
        self.csm_runner = CSMRunner()
        
        # Initialize LLM
        raw_model = os.getenv("MODEL_NAME", "gpt-4o-mini")
        try:
            self.llm = ChatOpenAI(model=raw_model, temperature=0.2)
        except Exception:
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    def process_message(
    self,
    message: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> ChatState:

        state: ChatState = {
            "message": message,
            "session_id": session_id,
            "context": context or {}
        }

        # Step 1: Context Extraction
        ctx, missing, follow = ensure_context(message, state["context"])
        state["context"] = ctx
        state["missing"] = missing
        state["followup"] = follow

        # Step 2: Document Retrieval
        docs = self.retriever.retrieve(message, k=5)
        state["docs"] = docs

        # Step 3: CSV Data Summary
        data = self.csv_engine.summarize(message, state["context"])
        state["csv"] = data

        # Step 4: Weather Data
        weather = load_weather(state["context"])
        state["weather"] = weather

        # Step 5: CSM (if context allows)
        if state["context"].get("crop") and state["context"].get("region"):
            params = {
                "crop": state["context"].get("crop"),
                "region": state["context"].get("region"),
                "season": state["context"].get("season"),
                "soil": state["context"].get("soil"),
                "water": state["context"].get("water"),
                "planting_method": state["context"].get("planting_method"),
            }
            state["csm"] = self.csm_runner.run(params)
        else:
            state["csm"] = {}

        # Step 6: Synthesis
        sys_prompt = (
    "You are Holos Agri Assistant, a friendly and knowledgeable agricultural advisor. "
    "After giving your main answer, naturally add only ONE short, helpful follow-up question—"
    "like a continuation prompt a human might ask (e.g., 'Would you like me to show examples?' or "
    "'Want me to explain that further?'). "
    "Avoid repeating or listing multiple questions. Keep it conversational."
)


        # Extract data from state
        docs = state.get("docs", [])
        csv = state.get("csv", {})
        weather = state.get("weather", {})
        csm = state.get("csm", {})
        ctx = state.get("context", {})
        follow = state.get("followup", "")

        # Combine document snippets
        doc_snips = "\n\n".join([f"- {d.get('content','')[:500]}" for d in docs])

        # Collect sources
        sources = []
        for d in docs:
            m = d.get("metadata") or {}
            sources.append({"source": m.get("source", ""), "page": m.get("page", None)})

        # Combine all information
        user_prompt = (
            f"User question: {message}\n"
            f"Context: {ctx}\n"
            f"CSV: {csv}\n"
            f"Weather: {weather}\n"
            f"CSM: {csm}\n"
            f"Docs:\n{doc_snips}"
        )

        # Generate reply
        try:
            messages = [SystemMessage(content=sys_prompt)]

            # Add short-term memory (previous exchanges)
            for h in (history or []):
                messages.append(HumanMessage(content=h["user"]))
                messages.append(HumanMessage(content=h["bot"]))  # treat last reply as conversational context

            # Add the new question
            messages.append(HumanMessage(content=user_prompt))

            res = self.llm.invoke(messages)

            reply = res.content
        except Exception as e:
            reply = f"I hit an issue synthesizing the answer: {e}. Here are the findings from docs and data."

        


        # Structure the response
        sections = {
            "rag_insights": docs[:3],
            "csv_findings": csv,
            "weather_context": weather,
            "csm_results": csm if csm else {"note": "CSM skipped until crop+region are provided."},
            "recommendations": None,
            "assumptions": {"missing": state.get("missing", [])},
            "sources": sources
        }

        state["reply"] = reply
        state["sections"] = sections

        return state

# Create a singleton instance
processor = ChatProcessor()

def process_chat(
    message: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> ChatState:
    """Main entry point for chat processing"""
    return processor.process_message(message, session_id, context, history)
