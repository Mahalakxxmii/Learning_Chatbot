import streamlit as st
import requests
import json
from PyPDF2 import PdfReader
import pdfplumber
import os
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="EduyyBot", page_icon="📘", layout="wide")

COOKIE_KEY = "eduyy_user"

def get_cookie(key):
    cookies = streamlit_js_eval(js_code="document.cookie", key="get_cookie_chat")
    if cookies:
        cookies = dict(c.split("=", 1) for c in cookies.split("; ") if "=" in c)
        return cookies.get(key)
    return None

def delete_cookie(key):
    streamlit_js_eval(
        js_code=f'document.cookie = "{key}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;"',
        key="delete_cookie_chat"
    )

def load_users_local():
    try:
        with open('users.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"users": []}

# ───── AUTH CHECK ─────
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "logged_once" not in st.session_state:
    st.session_state["logged_once"] = False

# Restore login after refresh (same browser session)
if st.session_state["logged_once"] and not st.session_state["is_logged_in"]:
    st.session_state["is_logged_in"] = True

# Restore login from cookie (survives a hard browser refresh, which reloads
# this page directly without going through app.py)
if not st.session_state["is_logged_in"]:
    cookie_user = get_cookie(COOKIE_KEY)
    if cookie_user:
        users = load_users_local()
        if any(u["username"] == cookie_user for u in users["users"]):
            st.session_state["is_logged_in"] = True
            st.session_state["logged_once"] = True
            st.session_state["username"] = cookie_user
            st.rerun()

# If still not logged in, block
if not st.session_state["is_logged_in"]:
    st.warning("Please login first.")
    st.stop()

username = st.session_state.get("username", "Guest")

# ───── FUNCTIONS: HISTORY ─────
def load_history(username):
    filename = f"history_{username}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def save_history(username, history):
    filename = f"history_{username}.json"
    with open(filename, "w") as f:
        json.dump(history, f)

def clear_history(username):
    filename = f"history_{username}.json"
    if os.path.exists(filename):
        os.remove(filename)

# ───── LOAD PERMANENT HISTORY INTO SESSION ─────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history(username)

if "clear_flag" in st.session_state and st.session_state.clear_flag:
    st.session_state.current_input = ""
    st.session_state.clear_flag = False

# ═══════════════════════════ STYLE (ChatGPT-inspired) ═══════════════════════════
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}
.stApp { background-color: #212121 !important; }

/* Hide Streamlit chrome */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
[data-testid="stHeader"] {
    background-color: transparent !important;
    height: 3.5rem !important;
}
[data-testid="stToolbar"] { visibility: hidden !important; }  /* hides menu/deploy button only */

/* Lock the sidebar open: hide both the "<<" collapse button inside the
   sidebar and the ">>" re-open arrow that appears once collapsed, so the
   sidebar can't accidentally be hidden with no way back. */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"] {
    display: none !important;
    visibility: hidden !important;
}

/* Center the chat column like ChatGPT's content width */
.block-container {
    max-width: 760px;
    margin: auto;
    padding-top: 1.2rem !important;
    padding-bottom: 9rem !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #171717 !important;
    border-right: 1px solid #2a2a2a;
    min-width: 300px !important;
    width: 300px !important;
}
[data-testid="stSidebar"] > div:first-child {
    width: 300px !important;
}
[data-testid="stSidebarResizeHandle"] { display: none !important; }
[data-testid="stSidebar"] * { color: #ececec !important; }

[data-testid="stSidebar"] div.stButton { width: 100%; }
[data-testid="stSidebar"] div.stButton > button {
    width: 100% !important;
    min-width: 100% !important;
    background-color: transparent !important;
    color: #ececec !important;
    border: 1px solid #3a3a3a !important;
    border-radius: 10px !important;
    text-align: left !important;
    padding: 8px 12px !important;
    margin-bottom: 6px;
    white-space: nowrap !important;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #2a2a2a !important;
}

/* File uploader: force the inner dropzone/button dark (Streamlit renders these light by default) */
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background-color: #1c1c1c !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 8px !important;
    padding: 12px !important;
    min-height: 110px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
    color: #ececec !important;
    fill: #ececec !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {
    white-space: normal !important;
    background-color: transparent !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
    background-color: #1c1c1c !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
    background-color: #2a2a2a !important;
    color: #ececec !important;
    border: 1px solid #3f3f3f !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    position: static !important;
    margin-top: 6px !important;
}

/* Page title row */
.eduyy-header {
    text-align: center;
    color: #ececec;
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 0px;
}
.eduyy-subheader {
    text-align: center;
    color: #8e8e8e;
    font-size: 13px;
    margin-bottom: 18px;
}

/* Chat rows - ChatGPT style: full-width row, content column, no bubble on bot */
.chat-row {
    padding: 18px 6px;
    border-bottom: 1px solid #2a2a2a;
}
.chat-row.user { background-color: transparent; }
.chat-row.bot  { background-color: #2a2a2a; border-radius: 12px; }

.chat-role {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.chat-row.user .chat-role { color: #10a37f; }
.chat-row.bot .chat-role  { color: #9d7bea; }

.chat-content {
    color: #ececec;
    font-size: 15px;
    line-height: 1.6;
    white-space: pre-wrap;
}

/* Empty state */
.empty-state {
    text-align: center;
    color: #6b6b6b;
    margin-top: 15vh;
    font-size: 15px;
}
.empty-state .big { font-size: 22px; color: #ececec; margin-bottom: 8px; font-weight: 600; }

/* ───── Floating input bar, ChatGPT-style pill ───── */
.input-bar-wrap {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: center;
    background: linear-gradient(180deg, rgba(33,33,33,0) 0%, #212121 40%);
    padding: 18px 0 22px 0;
    z-index: 999;
}

/* Streamlit widgets inside the "input row" columns, styled to look like one pill */
div[data-testid="stHorizontalBlock"] .stTextInput input {
    background-color: #2f2f2f !important;
    color: #ececec !important;
    border: 1px solid #4b4b4b !important;
    border-radius: 24px !important;
    padding: 12px 18px !important;
    font-size: 15px !important;
}
div[data-testid="stHorizontalBlock"] .stTextInput input:focus {
    border: 1px solid #10a37f !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] .stTextInput input::placeholder { color: #7a7a7a !important; }

/* Scope the round send button to the input row only, NOT every secondary button (sidebar buttons are also "secondary" by default) */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background-color: #2f2f2f !important;
    color: #ececec !important;
    border: 1px solid #4b4b4b !important;
    border-radius: 50% !important;
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    padding: 0 !important;
    font-size: 1rem !important;
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
    background-color: #10a37f !important;
    border-color: #10a37f !important;
}

[data-testid="stFileUploader"] {
    background-color: #1c1c1c !important;
    border: 1px dashed #3f3f3f !important;
    border-radius: 12px !important;
    padding: 10px !important;
}
[data-testid="stFileUploader"] label { color: #d4d4d4 !important; }

div[data-testid="stAlert"] { border-radius: 10px !important; }

[data-testid="stSpinner"] {
    justify-content: center !important;
}
[data-testid="stSpinner"] > div {
    color: #ececec !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════ SIDEBAR ═══════════════════════════
with st.sidebar:
    st.markdown("### 📘 EduBot")
    st.caption(f"Signed in as **{username}**")

    if st.button("🗑️  Clear chat"):
        clear_history(username)
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("**📄 Upload a PDF**")
    uploaded_file = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")

    pdf_action = None
    run_pdf_task = False
    if uploaded_file:
        try:
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            st.session_state.pdf_text = text
            st.success("PDF loaded ✓")

            pdf_action = st.radio("What should I do with it?", ("Summarize", "Generate Questions"))
            run_pdf_task = st.button("Run PDF task")
        except Exception as e:
            st.error(f"Failed to read PDF: {e}")
            st.session_state.pdf_text = ""

    st.markdown("---")
    if st.button("Log Out"):
        delete_cookie(COOKIE_KEY)
        st.session_state["is_logged_in"] = False
        st.session_state["logged_once"] = False
        st.session_state["username"] = ""
        st.session_state["chat_history"] = []
        js = """
        <script>
            window.location.href = "/";
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)
        st.stop()

# ═══════════════════════════ HEADER ═══════════════════════════
st.markdown(f"<div class='eduyy-header'>Welcome back, {username} 👋</div>", unsafe_allow_html=True)
st.markdown("<div class='eduyy-subheader'>Ask me anything, or upload a PDF from the sidebar to summarize or generate questions.</div>", unsafe_allow_html=True)

# ═══════════════════════════ CHAT DISPLAY ═══════════════════════════
chat_container = st.container()
with chat_container:
    if not st.session_state.chat_history:
        st.markdown(
            "<div class='empty-state'><div class='big'>EduBot</div>How can I help you study today?</div>",
            unsafe_allow_html=True
        )
    else:
        for chat in st.session_state.chat_history:
            role = chat["role"]
            msg = chat["content"]
            cls = "user" if role == "user" else "bot"
            label = "You" if role == "user" else "EduBot"
            st.markdown(
                f"""<div class='chat-row {cls}'>
                        <div class='chat-role'>{label}</div>
                        <div class='chat-content'>{msg}</div>
                    </div>""",
                unsafe_allow_html=True
            )

# ═══════════════════════════ NLP CALL SETUP ═══════════════════════════
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def ask_openrouter(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.app",
        "X-Title": "EduyyBot"
    }
    payload = {"model": "openrouter/free", "messages": messages}
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Error: {e}"

# ═══════════════════════════ PDF TASK HANDLING (triggered from sidebar) ═══════════════════════════
if uploaded_file and pdf_action and run_pdf_task:
    if pdf_action == "Summarize":
        prompt = f"Summarize the following text:\n{st.session_state.pdf_text}"
    else:
        prompt = f"Generate interview/exam-style questions from the following text:\n{st.session_state.pdf_text}"

    st.session_state.chat_history.append({"role": "user", "content": f"PDF Task: {pdf_action}"})
    with st.spinner("EduBot is reading your PDF…"):
        reply = ask_openrouter(st.session_state.chat_history + [{"role": "user", "content": prompt}])
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    save_history(username, st.session_state.chat_history)
    st.rerun()

# ═══════════════════════════ FLOATING INPUT BAR ═══════════════════════════
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)  # spacer so last message isn't hidden

input_col, send_col = st.columns([14, 1])

with input_col:
    user_input = st.text_input(
        "",
        placeholder="Message EduBot...",
        label_visibility="collapsed",
        key="current_input"
    )

with send_col:
    send_clicked = st.button("➤", key="send", help="Send", type="secondary")

if send_clicked and st.session_state.current_input:
    user_message = st.session_state.current_input
    st.session_state.chat_history.append({"role": "user", "content": user_message})

    with st.spinner("EduBot is thinking…"):
        reply = ask_openrouter(st.session_state.chat_history)
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    save_history(username, st.session_state.chat_history)
    st.session_state.clear_flag = True
    st.rerun()

# ───── AUTO-SCROLL TO BOTTOM ─────
st.markdown("""
<script>
window.parent.document.querySelector('section.main').scrollTo(0, window.parent.document.querySelector('section.main').scrollHeight);
</script>
""", unsafe_allow_html=True)
