import os, requests, streamlit as st

# st.markdown("<style>.stChatMessage.user {text-align: right;}</style>", unsafe_allow_html=True)


# -------------------------------------------------------
# Backend API Configuration
# -------------------------------------------------------
# The FastAPI backend endpoint that handles chat requests.
# Default: runs locally on port 8001 unless overridden by environment variable.
API_URL = os.getenv("API_URL", "http://localhost:8001/chat")

# -------------------------------------------------------
# Streamlit Page Setup
# -------------------------------------------------------
st.set_page_config(page_title="Holos Agri Assistant", page_icon="🌾")


# -------------------------------------------------------
# Welcome / Landing Page
# -------------------------------------------------------
# if "page" not in st.session_state:
#     st.session_state.page = "welcome"

# if st.session_state.page == "welcome":
#     st.markdown("""
#         <style>
#         /* ---- Page background ---- */
#         .stApp {
#             background-color: #0b3d0b;  /* dark green */
#             background-image: radial-gradient(#134e13 1px, transparent 1px);
#             background-size: 25px 25px; /* subtle leafy texture dots */
#         }

#         /* ---- Card container ---- */
#         .welcome-card {
#             max-width: 1000px;
#             margin: 5% auto;
#             background-color: #ffffff;
#             border-radius: 20px;
#             box-shadow: 0 6px 25px rgba(0,0,0,0.25);
#             display: flex;
#             justify-content: space-between;
#             align-items: center;
#             overflow: hidden;
#             border: 8px solid #134e13; /* thin dark-green border */
#         }

#         /* ---- Left Section ---- */
#         .left-section {
#             flex: 1;
#             padding: 60px 50px;
#         }

#         .left-section h1 {
#             color: #134e13;   /* heading color dark green */
#             font-size: 42px;
#             margin-bottom: 15px;
#             font-weight: 700;
#         }

#         .left-section p {
#             font-size: 18px;
#             color: #333333;
#             margin-bottom: 30px;
#         }

#         .button {
#             background-color: #134e13;
#             color: #ffffff;
#             border: none;
#             padding: 14px 36px;
#             font-size: 18px;
#             border-radius: 10px;
#             cursor: pointer;
#             transition: 0.3s;
#         }

#         .button:hover {
#             background-color: #1a661a;
#         }

#         /* ---- Right Section ---- */
#         .right-section {
#             flex: 1;
#             text-align: center;
#             background-color: #eaf5e4; /* pale green backdrop for image */
#         }

#         .right-section img {
#             width: 100%;
#             height: auto;
#             border-left: 6px solid #134e13;
#         }

#         /* ---- Leafy border illusion ---- */
#         body::before {
#             content: "";
#             position: fixed;
#             top: 0; left: 0; right: 0; bottom: 0;
#             pointer-events: none;
#             background-image: url('https://cdn.pixabay.com/photo/2016/03/31/20/37/leaf-1296593_960_720.png');
#             background-repeat: repeat;
#             background-size: 80px;
#             opacity: 0.08;
#         }
#         </style>
#     """, unsafe_allow_html=True)

#     # --- Card layout ---
#     st.markdown("""
#         <div class="welcome-card">
#             <div class="left-section">
#                 <h1>Agriculture AI Chatbot</h1>
#                 <p>Your personalized farming and crop assistant 🌱</p>
#                 <form action="#">
#                     <button class="button" name="chat" type="submit">💬 Chat</button>
#                 </form>
#             </div>
#             <div class="right-section">
#                 <img src="farmer_welcome.jpg" alt="Farmer">
#             </div>
#         </div>
#     """, unsafe_allow_html=True)

#     # Streamlit button logic handled outside HTML form
#     chat = st.button("Start Chat", key="chat_button")
#     if chat:
#         st.session_state.page = "chatbot"
#         st.rerun()

#     st.stop()


# -------------------------------------------------------
# Main Page
# -------------------------------------------------------


# if st.session_state.page == "chatbot":


st.title("Holos Agri Assistant 🌾")

# -------------------------------------------------------
# Session Initialization
    # -------------------------------------------------------
    # Create a unique session ID and store conversation context across interactions.
if "session_id" not in st.session_state:
    st.session_state.session_id = "demo-session"
if "context" not in st.session_state:
    st.session_state.context = {}
if "messages" not in st.session_state:
        st.session_state.messages = []


    # -------------------------------------------------------
    # Sidebar: Context Input
    # -------------------------------------------------------
with st.sidebar:
    st.header("Context")
    st.session_state.context["crop"] = st.text_input(
        "Crop", st.session_state.context.get("crop", "")
    )
    st.session_state.context["region"] = st.text_input(
        "Region/County/ZIP", st.session_state.context.get("region", "")
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

        # Try to send the message to the backend API
        try:
            r = requests.post(API_URL, json=payload, timeout=120)
            r.raise_for_status()  # Raise error if the request failed
            
            # Parse the response JSON from backend
            data = r.json()
            
            # Save the last response in session memory
            st.session_state.last_response = data
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Unable to connect to the backend server. Please make sure the backend server is running on port 8001.")
            st.info("To start the backend server, open a new terminal and run: `uvicorn holos.api:app --port 8001`")
            st.session_state.last_response = None
        except Exception as e:
            st.error(f"⚠️ An error occurred: {str(e)}")
            st.session_state.last_response = None

# -------------------------------------------------------
# Display Chatbot Response
# -------------------------------------------------------
# --- Display existing chat history (like ChatGPT) ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle new user input ---
if user_input:
    # Show user message instantly on right
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Thinking..."):
        payload = {
            "session_id": st.session_state.session_id,
            "message": user_input,
            "context": st.session_state.context,
        }
        try:
            r = requests.post(API_URL, json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            reply = data.get("reply", "⚠️ No reply received.")
        except requests.exceptions.ConnectionError:
            reply = "⚠️ Backend not reachable. Run: `uvicorn holos.api:app --port 8001`"
        except Exception as e:
            reply = f"⚠️ Error: {e}"

    # Add assistant reply on left
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)


