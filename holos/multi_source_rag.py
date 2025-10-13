import os
from typing import Dict, Any, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import project modules for data and processing
from .rag import RAGRetriever           # Retrieves relevant text/documents
from .csv_rag import CSVEngine          # Reads and summarizes CSV data
from .weather import load_weather       # Loads weather information
from .csm_runner import CSMRunner       # Runs crop simulation model
from .conversation import ensure_context  # Extracts and ensures context (crop, region, etc.)

# -------------------------------------------------------
# Class: GraphState (TypedDict)
# -------------------------------------------------------
# Purpose:
# Defines the structure of the data passed between nodes
# in the pipeline (like context, docs, weather, etc.).
class GraphState(TypedDict, total=False):
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


# -------------------------------------------------------
# Initialize all major components
# -------------------------------------------------------
retriever = RAGRetriever()   # For document retrieval
csv_engine = CSVEngine()     # For analyzing CSV data
csm_runner = CSMRunner()     # For running crop simulation models

# -------------------------------------------------------
# Initialize the language model (OpenAI chat model)
# -------------------------------------------------------
raw_model = os.getenv("MODEL_NAME", "gpt-4o-mini")
try:
    llm = ChatOpenAI(model=raw_model, temperature=1)
except Exception:
    # Fallback model in case the environment variable fails
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)


# -------------------------------------------------------
# Node 1: Context Extraction
# -------------------------------------------------------
# Uses heuristic rules to detect crop, region, and season
# from the user's message and updates the session context.
def node_context(state: GraphState) -> GraphState:
    ctx, missing, follow = ensure_context(state["message"], state.get("context"))
    return {"context": ctx, "missing": missing, "followup": follow}


# -------------------------------------------------------
# Node 2: Document Retrieval
# -------------------------------------------------------
# Retrieves top-k relevant documents (RAG step).
def node_docs(state: GraphState) -> GraphState:
    docs = retriever.retrieve(state["message"], k=5)
    return {"docs": docs}


# -------------------------------------------------------
# Node 3: CSV Data Summary
# -------------------------------------------------------
# Reads and summarizes a CSV dataset based on crop or region.
def node_csv(state: GraphState) -> GraphState:
    data = csv_engine.summarize(state["message"], state["context"])
    return {"csv": data}


# -------------------------------------------------------
# Node 4: Weather Data
# -------------------------------------------------------
# Loads weather info using the context (state/region/zip).
def node_weather(state: GraphState) -> GraphState:
    w = load_weather(state["context"])
    return {"weather": w}


# -------------------------------------------------------
# Helper: Check if CSM can run
# -------------------------------------------------------
# The Crop Simulation Model only runs when both crop and region are known.
def can_run_csm(state: GraphState) -> bool:
    ctx = state.get("context", {}) or {}
    return bool(ctx.get("crop")) and bool(ctx.get("region"))


# -------------------------------------------------------
# Node 5: Crop Simulation Model (CSM)
# -------------------------------------------------------
# Runs the crop simulation model with available context parameters.
def node_csm(state: GraphState) -> GraphState:
    params = {
        "crop": state["context"].get("crop"),
        "region": state["context"].get("region"),
        "season": state["context"].get("season"),
        "soil": state["context"].get("soil"),
        "water": state["context"].get("water"),
        "planting_method": state["context"].get("planting_method"),
    }
    res = csm_runner.run(params)
    return {"csm": res}


# -------------------------------------------------------
# Node 6: Synthesis Node
# -------------------------------------------------------
# Combines all information (RAG, CSV, weather, CSM)
# into a single answer using the LLM (ChatOpenAI).
def node_synthesize(state: GraphState) -> GraphState:
    # System prompt to guide the LLM’s behavior
    sys = (
        "You are Holos Agri Assistant. Merge RAG insights, CSV findings, weather context, and CSM outputs. "
        "Provide a concise, practical recommendation for a farmer. If inputs are missing, state assumptions and ask ONE clarifying question."
    )

    # Extract data from the state
    docs = state.get("docs", [])
    csv = state.get("csv", {})
    weather = state.get("weather", {})
    csm = state.get("csm", {})
    ctx = state.get("context", {})
    follow = state.get("followup", "")

    # Combine document snippets (for the model to read)
    doc_snips = "\n\n".join([f"- {d.get('content','')[:500]}" for d in docs])

    # Collect sources for reference display
    sources = []
    for d in docs:
        m = d.get("metadata") or {}
        sources.append({"source": m.get("source", ""), "page": m.get("page", None)})

    # Combine all information into the user's input prompt
    user = (
        f"User question: {state['message']}\n"
        f"Context: {ctx}\n"
        f"CSV: {csv}\n"
        f"Weather: {weather}\n"
        f"CSM: {csm}\n"
        f"Docs:\n{doc_snips}"
    )

    # Run the LLM to synthesize all data into a reply
    try:
        res = llm.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
        reply = res.content
    except Exception as e:
        # Fallback message if the LLM call fails
        reply = f"I hit an issue synthesizing the answer: {e}. Here are the findings from docs and data."

    # If the system found missing info, append a clarifying question
    if follow:
        reply = f"{reply}\n\nQuick question to tailor the advice: {follow}"

    # Create structured sections for the response
    sections = {
        "rag_insights": docs[:3],
        "csv_findings": csv,
        "weather_context": weather,
        "csm_results": csm if csm else {"note": "CSM skipped until crop+region are provided."},
        "recommendations": None,  # Can be filled later by the LLM
        "assumptions": {"missing": state.get("missing", [])},
        "sources": sources
    }
    return {"reply": reply, "sections": sections, "context": ctx}


# -------------------------------------------------------
# Function: build_graph
# -------------------------------------------------------
# Purpose:
# Builds the complete data-processing pipeline using LangGraph.
# Each "node" represents a step, and edges define the flow.
def build_graph():
    g = StateGraph(GraphState)
    # Add all processing nodes safely (ignore duplicates on reload)
    for name, fn in [
        ("context1", node_context),
        ("docs1", node_docs),
        ("csv1", node_csv),
        ("weather1", node_weather),
        ("csm1", node_csm),
        ("synthesize1", node_synthesize),
    ]:
        try:
            g.add_node(name, fn)
            print("node", name)
        except ValueError:
            # Ignore if the node already exists (for hot reloads)
            pass
    # Define the data flow between nodes
    g.add_edge(START, "context1")                          # Start → context extraction
    g.add_edge("context1", "docs1")                         # Context → document retrieval
    g.add_edge("docs1", "csv1")                             # Docs → CSV data summary
    g.add_edge("csv1", "weather1")                          # CSV → weather info
    g.add_conditional_edges("weather1", can_run_csm, {     # Weather → CSM or Synthesis
        True: "csm1", 
        False: "synthesize1"
    })
    g.add_edge("csm1", "synthesize1")                       # CSM → synthesis
    g.add_edge("synthesize1", END)                         # End the pipeline

    # Return the compiled graph ready for use
    return g.compile()
