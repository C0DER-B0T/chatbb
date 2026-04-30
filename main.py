import streamlit as st
from google import genai
from google.genai import errors
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# --- Chat Persistence Helpers ---
CHAT_HISTORY_FILE = "chat_sessions.json"

def save_all_sessions(sessions):
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(sessions, f)

def load_all_sessions():
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

# --- Model Aliasing ---
MODEL_MAP = {
    "Model-1": "gemini-3-flash-preview",
    "Model-2": "gemini-2.5-flash",
    "Model-3": "gemini-2.0-flash",
    "Model-4": "gemini-1.5-pro"
}
REVERSE_MODEL_MAP = {v: k for k, v in MODEL_MAP.items()}

# --- App Configuration ---
st.set_page_config(
    page_title="BrainBuddy AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Advanced UI & Responsiveness ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }

    /* Chat Container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }

    /* Message Bubbles */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 1rem 0 !important;
    }

    .user-message {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white !important;
        border-radius: 20px 20px 5px 20px;
        padding: 15px 25px;
        margin-left: auto;
        max-width: 85%;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        animation: fadeInRight 0.3s ease-out;
    }

    .bot-message {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(10px);
        color: #e2e8f0 !important;
        border-radius: 20px 20px 20px 5px;
        padding: 15px 25px;
        margin-right: auto;
        max-width: 85%;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(148, 163, 184, 0.2);
        animation: fadeInLeft 0.3s ease-out;
    }

    @keyframes fadeInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    @keyframes fadeInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* Header Styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem !important;
    }

    /* Input Field Styling */
    .stChatInputContainer {
        border-top: 1px solid rgba(148, 163, 184, 0.1) !important;
        background-color: #0f172a !important;
        padding: 1rem !important;
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
        }
        .user-message, .bot-message {
            max-width: 95%;
        }
        .chat-container {
            padding: 10px;
        }
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
</style>
""", unsafe_allow_html=True)

# --- Gemini API Initialization ---
# Support both 'gemini_api' and 'GEMINI_API_KEY' environment variables
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api") or "").strip().strip('"').strip("'")

if not GEMINI_API_KEY:
    st.error("🚨 API Key not found! Please ensure 'gemini_api' is set in your .env file.")
    st.stop()

if "client" not in st.session_state:
    try:
        # Initialize client with robust settings
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Elite models from app.py
        st.session_state.model_alias = "Model-1"
        st.session_state.model_name = MODEL_MAP[st.session_state.model_alias]
        
        # Test connection
        client.models.generate_content(model=st.session_state.model_name, contents="Test")
        
        st.session_state.client = client
        st.session_state.chat_session = client.chats.create(model=st.session_state.model_name)
    except Exception as e:
        st.error(f"❌ Connection Failed: {str(e)}")
        st.stop()

# --- Multi-Session Management ---
if "sessions" not in st.session_state:
    st.session_state.sessions = load_all_sessions()

if "current_session_id" not in st.session_state:
    # If no sessions exist, create a default one
    if not st.session_state.sessions:
        first_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.sessions[first_session_id] = {
            "name": "New Chat",
            "messages": []
        }
        save_all_sessions(st.session_state.sessions)
        st.session_state.current_session_id = first_session_id
    else:
        # Load the most recent session
        st.session_state.current_session_id = list(st.session_state.sessions.keys())[-1]

# Shortcut for current messages
st.session_state.messages = st.session_state.sessions[st.session_state.current_session_id]["messages"]

# --- UI Layout ---
st.markdown('<h1 class="main-header">BrainBuddy</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #94a3b8; margin-bottom: 2rem;">Elite Intelligence • High-Performance Chat</p>', unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.title("⚙️ Settings")
    
    # New Chat Button
    if st.button("➕ New Conversation", use_container_width=True):
        new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.sessions[new_id] = {"name": "New Chat", "messages": []}
        st.session_state.current_session_id = new_id
        st.session_state.chat_session = st.session_state.client.chats.create(model=st.session_state.model_name)
        save_all_sessions(st.session_state.sessions)
        st.rerun()

    st.divider()

    # Past Conversations List
    st.subheader("📜 Past Conversations")
    for sess_id in reversed(list(st.session_state.sessions.keys())):
        sess_name = st.session_state.sessions[sess_id]["name"]
        # Highlight current session
        is_current = (sess_id == st.session_state.current_session_id)
        btn_label = f"💬 {sess_name}" if not is_current else f"👉 {sess_name}"
        
        if st.button(btn_label, key=sess_id, use_container_width=True):
            st.session_state.current_session_id = sess_id
            st.session_state.chat_session = st.session_state.client.chats.create(model=st.session_state.model_name)
            st.rerun()

    st.divider()

    # Elite Model Selector with Aliases
    model_alias_options = list(MODEL_MAP.keys())
    
    new_model_alias = st.selectbox(
        "Select Advanced Model",
        model_alias_options,
        index=model_alias_options.index(st.session_state.model_alias) if st.session_state.model_alias in model_alias_options else 0,
        help="Elite models for complex tasks. Model-4 has higher reasoning capabilities."
    )
    
    if new_model_alias != st.session_state.model_alias:
        st.session_state.model_alias = new_model_alias
        st.session_state.model_name = MODEL_MAP[new_model_alias]
        st.session_state.chat_session = st.session_state.client.chats.create(model=st.session_state.model_name)
        st.toast(f"Switched to {new_model_alias}")

    if st.button("🗑️ Delete Current Chat", use_container_width=True):
        if len(st.session_state.sessions) > 1:
            del st.session_state.sessions[st.session_state.current_session_id]
            st.session_state.current_session_id = list(st.session_state.sessions.keys())[-1]
            save_all_sessions(st.session_state.sessions)
            st.rerun()
        else:
            st.session_state.sessions[st.session_state.current_session_id]["messages"] = []
            st.session_state.sessions[st.session_state.current_session_id]["name"] = "New Chat"
            save_all_sessions(st.session_state.sessions)
            st.rerun()
    
    st.divider()
    
    # About Us Section
    st.title("👥 About Us")
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.5); padding: 15px; border-radius: 10px; border: 1px solid rgba(148, 163, 184, 0.1);">
        <p style="margin-bottom: 5px;">Build by <b>Satyam chandra</b></p>
        <a href="https://satyamchandra-info.vercel.app/" target="_blank" style="color: #3b82f6; text-decoration: none;">🌐 My Portfolio web →</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.info("BrainBuddy is powered by NLP System. It can handle complex reasoning, coding, and creative tasks, it is made by Satyam Chandra.")

# Display Chat History
chat_placeholder = st.container()

with chat_placeholder:
    for message in st.session_state.messages:
        role_class = "user-message" if message["role"] == "user" else "bot-message"
        avatar = "👤" if message["role"] == "user" else "✨"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(f'<div class="{role_class}">{message["content"]}</div>', unsafe_allow_html=True)

# Chat Input
if prompt := st.chat_input("How can I assist you today?"):
    # Update session name if it's the first message
    if not st.session_state.messages:
        st.session_state.sessions[st.session_state.current_session_id]["name"] = prompt[:20] + "..." if len(prompt) > 20 else prompt

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_all_sessions(st.session_state.sessions) # Persist all sessions
    
    # Display user message
    with chat_placeholder:
        with st.chat_message("user", avatar="👤"):
            st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)

    # Generate and display assistant response
    with chat_placeholder:
        with st.chat_message("assistant", avatar="✨"):
            response_placeholder = st.empty()
            with st.status("🧠 Processing...", expanded=False) as status:
                try:
                    response = st.session_state.chat_session.send_message(prompt)
                    full_response = response.text
                    
                    status.update(label="✨ Response Ready", state="complete", expanded=False)
                    response_placeholder.markdown(f'<div class="bot-message">{full_response}</div>', unsafe_allow_html=True)
                    
                    # Add assistant response to history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    save_all_sessions(st.session_state.sessions) # Persist all sessions
                except errors.APIError as e:
                    status.update(label="⚠️ Connection/API Issue", state="error")
                    err_msg = str(e).lower()
                    if "10051" in err_msg or "unreachable" in err_msg or "10060" in err_msg:
                        st.error("🌐 **Network Error**: BrainBuddy cannot reach the Google servers. This is usually a local network or proxy issue.")
                        st.info("💡 **Try this**: Check if your internet is stable, or try switching to a different network (like a mobile hotspot).")
                    elif "quota" in err_msg:
                        st.error("🚨 **Quota Exceeded**: You've hit the Gemini free tier limit. Please wait a moment or try switching the model in the settings sidebar.")
                    elif "not found" in err_msg or "supported" in err_msg:
                        st.error(f"🚨 **Model Error**: The model '{st.session_state.model_name}' is not responding. Attempting elite fallback...")
                        try:
                            fallback_model = "gemini-1.5-pro" if st.session_state.model_name != "gemini-1.5-pro" else "gemini-2.0-flash"
                            st.session_state.model_name = fallback_model
                            st.session_state.chat_session = st.session_state.client.chats.create(model=fallback_model)
                            response = st.session_state.chat_session.send_message(prompt)
                            full_response = response.text
                            status.update(label="✨ Recovered with Elite Fallback", state="complete")
                            response_placeholder.markdown(f'<div class="bot-message">{full_response}</div>', unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": full_response})
                        except:
                            st.error("Could not recover automatically. Please select a different advanced model from the sidebar manually.")
                    else:
                        st.error(f"API Error: {e.message}")
                except Exception as e:
                    status.update(label="❌ Unexpected error", state="error")
                    err_msg = str(e).lower()
                    if "10051" in err_msg or "unreachable" in err_msg or "10060" in err_msg:
                        st.error("🌐 **Network Unreachable**: BrainBuddy is blocked by your local network. Please check your firewall or internet connection.")
                        st.info("💡 **Fix**: Ensure you are connected to a network that allows outgoing HTTPS requests to Google services.")
                    else:
                        st.error(f"Error: {str(e)}")

# Footer
st.markdown(f"""
<div style="position: fixed; bottom: 10px; right: 10px; color: #475569; font-size: 0.8rem;">
    Powered by {st.session_state.model_alias}
</div>
""", unsafe_allow_html=True)
