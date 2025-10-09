import streamlit as st
import requests
import json
from PyPDF2 import PdfReader
import pdfplumber
import fitz
import os 
from streamlit_extras.switch_page_button import switch_page

# Function to load history from JSON
def load_history(username):
    filename = f"history_{username}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

# Function to save history to JSON
def save_history(username, history):
    filename = f"history_{username}.json"
    with open(filename, "w") as f:
        json.dump(history, f)

# Function to clear history
def clear_history(username):
    filename = f"history_{username}.json"
    if os.path.exists(filename):
        os.remove(filename)

st.set_page_config(page_title="EduyyBot", page_icon="📘", layout="wide")

username = st.session_state.get("username", "Guest")
st.markdown(f"<h2 style='text-align:center;'>Welcome {username} 👋</h2>", unsafe_allow_html=True)

if "clear_flag" in st.session_state and st.session_state.clear_flag:
    st.session_state.current_input = ""
    st.session_state.clear_flag = False

# EDUBOT centered below
st.markdown("<h4 style='text-align:center; color:#555;'>EDUBOT</h4>", unsafe_allow_html=True)

# ───── AUTH CHECK ─────
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "logged_once" not in st.session_state:
    st.session_state["logged_once"] = False

# Restore login after refresh
if st.session_state["logged_once"] and not st.session_state["is_logged_in"]:
    st.session_state["is_logged_in"] = True

# If still not logged in, block
if not st.session_state["is_logged_in"]:
    st.warning("Please login first.")
    st.stop()


# ───── LOAD PERMANENT HISTORY INTO SESSION ─────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history(username)

# ───── STYLES ─────
st.markdown("""
<style>
body {
    background-color: #f5f7fa;
}
.chat-window {
    max-height: 70vh;
    overflow-y: auto;
    padding: 2rem;
    background-color: #ffffff;
    border-radius: 12px;
    margin: 2rem auto;
    width: 65%;
    max-width: 300px;
    box-shadow: 0 0 10px rgba(0,0,0,0.05);
}
.bubble {
    padding: 12px 16px;
    margin-bottom: 12px;
    border-radius: 16px;
    max-width: 90%;
    font-size: 1rem;
    line-height: 1.5;
}
.user-msg {
    background-color: #dceeff;
    margin-left: auto;
    text-align: right;
}
.bot-msg {
    background-color: #e8fce8;
    margin-right: auto;
    text-align: left;
}
.input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 1rem;
    background: white;
    box-shadow: 0 -2px 8px rgba(0,0,0,0.05);
    z-index: 1000;
    display: flex;
    justify-content: center;
}

</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
""", unsafe_allow_html=True)

# ───── CHAT DISPLAY ─────
st.markdown("<div class='chat-window'>", unsafe_allow_html=True)
# Display chat history
for msg in st.session_state.chat_history:
    role = msg["role"]
    content = msg["content"]
    bubble_class = "user-msg" if role == "user" else "bot-msg"
    st.markdown(
        f"<div class='bubble {bubble_class}'><strong>{role.capitalize()}:</strong><br>{content}</div>",
        unsafe_allow_html=True,
    )

# ───── AUTO-SCROLL TO BOTTOM ─────
st.markdown("""
<script>
const chatWindow = window.parent.document.querySelector('.chat-window');
if (chatWindow) {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}
</script>
""", unsafe_allow_html=True)

# ───── INPUT BOX ─────
# Handle Upload & Voice FIRST (outside form)
# Top spacing
st.markdown("<br>", unsafe_allow_html=True)

# ───── CHAT INPUT ROW ─────
input_col, send_col, clear_col = st.columns([13,1,1])

def clear_input():
    st.session_state.current_input = ""

with input_col:
    user_input = st.text_input(
        "",
        placeholder="Type a message...",
        label_visibility="collapsed",
        key="current_input"
    )

with send_col:
    send_clicked = st.button("➤", help="Send")  # small rectangular button

with clear_col:
    if st.button("🗑️", help="Clear Chat History"):
        clear_history(username)
        st.session_state.chat_history = []
        st.stop()
        #st.experimental_rerun()
# Optional: Add CSS to make buttons small & rectangular
st.markdown("""
<style>
button[kind="secondary"] {
    padding: 0.25rem 0.5rem !important;
    font-size: 1.2rem !important;
    border-radius: 6px !important;
    background-color: white !important;
}
button[kind="secondary"]:hover {
    background-color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ───── NLP CALL ─────
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

if send_clicked and st.session_state.current_input:
    user_message = st.session_state.current_input
    st.session_state.chat_history.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",  # Replace with your key
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "EduyyBot"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": st.session_state.chat_history
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers,
                                 data=json.dumps(payload))
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        # Remove instruction tokens or extra trailing tags
        reply = reply.replace("[/INST]", "").strip()
    except Exception as e:
        reply = f"❌ Error: {e}"

    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    # ───── SAVE PERMANENT HISTORY ─────
   # save_chat_history(username, st.session_state.chat_history)
    save_history(username, st.session_state.chat_history)
    # Clear input
    st.session_state.clear_flag = True
    #st.rerun()

upload_col, _ = st.columns([0.5,0.5])  # 30% width for uploader
with upload_col:
    uploaded_file = st.file_uploader("To Upload PDF", type=["pdf"])
    if uploaded_file:
        try:
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            st.session_state.pdf_text = text
            st.success("PDF uploaded successfully!")

        # Ask what user wants to do
            action = st.radio("What do you want to do with this PDF?", ("Summarize", "Generate Questions"))
            if st.button("Run PDF Task"):
                prompt = ""
                if action == "Summarize":
                    prompt = f"Summarize the following text:\n{st.session_state.pdf_text}"
                elif action == "Generate Questions":
                    prompt = f"Generate interview/exam-style questions from the following text:\n{st.session_state.pdf_text}"

                if prompt:
                    st.session_state.chat_history.append({"role": "user", "content": f"PDF Task: {action}"})
                    headers = {
                    "Authorization": "Bearer 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",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "EduyyBot"
                    
                }
                    payload = {
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": st.session_state.chat_history + [{"role":"user","content":prompt}]
                }
                    try:
                        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                             headers=headers, data=json.dumps(payload))
                        response.raise_for_status()
                        reply = response.json()["choices"][0]["message"]["content"]
                    except Exception as e:
                        reply = f"❌ Error: {e}"
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
               # save_chat_history(username, st.session_state.chat_history)
                    st.rerun() 


        except Exception as e:
            st.error(f"Failed to read PDF: {e}")
            st.session_state.pdf_text = ""
# ───── SIDEBAR LOGOUT ─────
with st.sidebar:
    st.write("Account")
    if st.button("Log Out"):
        # Clear session flags
        st.session_state["is_logged_in"] = False
        st.session_state["logged_once"] = False
        st.session_state["username"] = ""
        st.session_state["chat_history"] = []

        # Redirect to login page (app.py)
        js = """
        <script>
            window.location.href = "/";
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)
        st.stop()
