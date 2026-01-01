import streamlit as st
import requests
import json
from PyPDF2 import PdfReader
import pdfplumber
import fitz
import os 
from streamlit_extras.switch_page_button import switch_page

st.markdown("""
<style>
.block-container {
    max-width: 760px;
    margin: auto;
}

.chat {
    padding: 12px 16px;
    border-radius: 14px;
    margin-bottom: 10px;
    max-width: 75%;
    font-size: 15px;
    line-height: 1.5;
}

.user {
    background-color: #2563eb;
    color: white;
    margin-left: auto;
}

.bot {
    background-color: #1f2937;
    color: #e5e7eb;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
.chat-window {
    max-height: 65vh;
    overflow-y: auto;
    padding: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Chat buttons */
.chat-btn {
    background-color: #1f2937 !important;
    color: #e5e7eb !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
    padding: 6px 10px !important;
    font-size: 16px !important;
    cursor: pointer;
}

.chat-btn:hover {
    background-color: #374151 !important;
}

/* Input box */
input[type="text"] {
    background-color: #111827 !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
    border: 1px solid #374151 !important;
}
</style>
""", unsafe_allow_html=True)

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
st.markdown("<h4 style='text-align:center; color:#9ca3af;'>EDUBOT</h4>", unsafe_allow_html=True)

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

# ───── CHAT DISPLAY ─────
st.markdown("<div class='chat-window'>", unsafe_allow_html=True)
# Display chat history
for chat in st.session_state.chat_history:
    role = chat["role"]
    msg = chat["content"]

    cls = "user" if role == "user" else "bot"

    st.markdown(
    f"<div class='chat {cls}'>{msg}</div>",
    unsafe_allow_html=True
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
    send_clicked = st.button("➤", key="send", help="Send", type="secondary")

with clear_col:
    if st.button("🗑️", key="clear", help="Clear Chat History", type="secondary"):
        clear_history(username)
        st.session_state.chat_history = []
        st.rerun()

        #st.experimental_rerun()
# Optional: Add CSS to make buttons small & rectangular
st.markdown("""
<style>
/* Send, Clear, PDF buttons - DARK MODE */
button[kind="secondary"] {
    background-color: #1f2937 !important;
    color: #e5e7eb !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
    padding: 6px 10px !important;
    font-size: 1.1rem !important;
}

button[kind="secondary"]:hover {
    background-color: #374151 !important;
}
</style>
""", unsafe_allow_html=True)

# ───── NLP CALL ─────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if send_clicked and st.session_state.current_input:
    user_message = st.session_state.current_input

    # 1️⃣ Add user message
    st.session_state.chat_history.append(
        {"role": "user", "content": user_message}
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.app",
        "X-Title": "EduyyBot"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": st.session_state.chat_history
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,      # ✅ IMPORTANT FIX
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        reply = f"❌ Error: {e}"

    # 2️⃣ Add assistant reply
    st.session_state.chat_history.append(
        {"role": "assistant", "content": reply}
    )

    # 3️⃣ Save history
    save_history(username, st.session_state.chat_history)

    # 4️⃣ Clear input
    st.session_state.clear_flag = True

    # 5️⃣ FORCE UI REFRESH ✅
    st.rerun()

upload_col, _ = st.columns([0.5,0.5])  # 30% width for uploader
with upload_col:
    st.markdown("""
<style>
[data-testid="stFileUploader"] {
    background-color: #111827 !important;
    border: 1px dashed #374151 !important;
    border-radius: 12px !important;
    padding: 12px !important;
}

[data-testid="stFileUploader"] label {
    color: #e5e7eb !important;
}
</style>
""", unsafe_allow_html=True)

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
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://streamlit.app",
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
