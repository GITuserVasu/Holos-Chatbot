import os, requests, streamlit as st

# -------------------------------------------------------
# Backend API Configuration
# -------------------------------------------------------
# The FastAPI backend endpoint that handles chat requests.
# Default: runs locally on port 8001 unless overridden by environment variable.
API_URL = os.getenv("API_URL", "http://172.31.23.62:8001/chat")
API_URL = "http://172.31.23.62:8001/chat"

# -------------------------------------------------------
# Streamlit Page Setup
# -------------------------------------------------------
st.set_page_config(page_title="Holos Agri Assistant", page_icon="🌾")
st.title("Holos Agri Assistant 🌾")

# -------------------------------------------------------
# Session Initialization
# -------------------------------------------------------
# Create a unique session ID and store conversation context across interactions.
if "session_id" not in st.session_state:
    st.session_state.session_id = "demo-session"
if "context" not in st.session_state:
    st.session_state.context = {}

# -------------------------------------------------------
# Sidebar: User Context Input
# -------------------------------------------------------
# Sidebar allows the user to set or modify context like crop, region, soil, etc.
with st.sidebar:
    st.header("Context")
    st.session_state.context["crop"] = st.text_input(
        "Crop", st.session_state.context.get("crop", "")
    )
    st.session_state.context["region"] = st.text_input(
        "Region/County/ZIP", st.session_state.context.get("region", "")
    )
    st.session_state.context["season"] = st.text_input(
        "Season", st.session_state.context.get("season", "")
    )
    st.session_state.context["soil"] = st.text_input(
        "Soil (optional)", st.session_state.context.get("soil", "")
    )
    st.session_state.context["water"] = st.text_input(
        "Water source (optional)", st.session_state.context.get("water", "")
    )
    st.session_state.context["planting_method"] = st.text_input(
        "Planting method (optional)", st.session_state.context.get("planting_method", "")
    )

# -------------------------------------------------------
# Chat Input Box
# -------------------------------------------------------
# The main text box for user messages at the bottom of the app.
user_input = st.chat_input("Ask about planting windows, yield, irrigation, etc.")

# -------------------------------------------------------
# When user submits a message
# -------------------------------------------------------
if user_input:
    with st.spinner("Thinking..."):
        # Prepare the payload to send to the FastAPI backend
        payload = {
            "session_id": st.session_state.session_id,
            "message": user_input,
            "context": st.session_state.context,
        }

        # Send the message to the backend API
        print(API_URL)
        r = requests.post(API_URL, json=payload, timeout=120)
        r.raise_for_status()  # Raise error if the request failed

        # Parse the response JSON from backend
        data = r.json()

        # Save the last response in session memory
        st.session_state.last_response = data

# -------------------------------------------------------
# Display Chatbot Response
# -------------------------------------------------------
if "last_response" in st.session_state:
    data = st.session_state.last_response

    # Display chatbot’s main reply in chat message format
    st.chat_message("assistant").write(data["reply"])

    # If chatbot suggests a follow-up question, show it in an info box
    if data.get("followup"):
        st.info(data["followup"])

    # Expandable sections for structured details (from backend)
    with st.expander("RAG Insights"):
        st.json((data.get("sections") or {}).get("rag_insights"))

    with st.expander("CSV Findings"):
        st.json((data.get("sections") or {}).get("csv_findings"))

    with st.expander("Weather Context"):
        st.json((data.get("sections") or {}).get("weather_context"))

    with st.expander("CSM Results"):
        st.json((data.get("sections") or {}).get("csm_results"))

    with st.expander("Sources"):
        st.json((data.get("sections") or {}).get("sources"))
