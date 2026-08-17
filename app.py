import streamlit as st
import json
import bcrypt
import os
from streamlit_lottie import st_lottie
import requests
import random, smtplib, ssl, time
from email.message import EmailMessage
from dotenv import load_dotenv
from streamlit_js_eval import streamlit_js_eval  # 🔑 for setting cookies

load_dotenv()
COOKIE_KEY = "eduyy_user"
COOKIE_EXPIRY = 7 * 24 * 60 * 60  # 7 days

def set_cookie(key, value, days_expire=7):
    streamlit_js_eval(
        js_code=f"""
        var d = new Date();
        d.setTime(d.getTime() + ({days_expire}*24*60*60*1000));
        document.cookie = "{key}=" + {json.dumps(value)} + "; expires=" + d.toUTCString() + "; path=/";
        """,
        key="set_cookie"
    )

def get_cookie(key):
    cookies = streamlit_js_eval(js_code="document.cookie", key="get_cookie")
    if cookies:
        cookies = dict(c.split("=", 1) for c in cookies.split("; "))
        return cookies.get(key)
    return None

def delete_cookie(key):
    streamlit_js_eval(
        js_code=f'document.cookie = "{key}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;"',
        key="delete_cookie"
    )

st.set_page_config(page_title="EduyyBot", page_icon="📘")

# Initialize session state keys to avoid key errors
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# If already logged in, redirect immediately to chatbot
if st.session_state["is_logged_in"]:
    st.session_state["page"] = "chatbot"
    st.switch_page("pages/1_chatbot.py")

# Load users from JSON
SMTP_SERVER   = os.getenv("SMTP_SERVER")     # e.g. "smtp.gmail.com"
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER")       # your email
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")   # your app-password

def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg["Subject"] = "EduyyBot OTP Verification"
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = to_email
    msg.set_content(
        f"Hi 👋,\n\nYour EduyyBot OTP is: {otp}\nIt is valid for 5 minutes.\n\nIf you didn't request this, ignore this email."
    )
    context = ssl.create_default_context()
    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
        server.starttls(context=context)
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)

def load_users():
    try:
        with open('users.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"users": []}

# Save users to JSON
def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file, indent=4)

# Check credentials
def check_user_credentials(username, password):
    users = load_users()
    for user in users["users"]:
        if user["username"] == username and bcrypt.checkpw(password.encode(), user["password"].encode()):
            return True
    return False

# Add new user
def add_new_user(email, username, password):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users = load_users()
    users["users"].append({
        "email": email,
        "username": username,
        "password": hashed_password,
    })
    save_users(users)


# ───── AUTO LOGIN VIA COOKIE (persists across browser refresh) ─────
if not st.session_state["is_logged_in"]:
    cookie_user = get_cookie(COOKIE_KEY)
    if cookie_user:
        users = load_users()
        if any(u["username"] == cookie_user for u in users["users"]):
            st.session_state["is_logged_in"] = True
            st.session_state["logged_once"] = True
            st.session_state["username"] = cookie_user
            st.session_state["page"] = "chatbot"
            st.switch_page("pages/1_chatbot.py")


def inject_css():
    st.markdown("""
        <style>
        /* ---------- ChatGPT-style dark theme for the auth page ---------- */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        }
        .stApp { background-color: #212121 !important; }

        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        footer, header {visibility: hidden;}

        .block-container {
            max-width: 400px !important;
            padding-top: 10vh !important;
            margin: 0 auto !important;
        }

        .auth-title {
            text-align: center;
            color: #ececec;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 2px;
        }
        .auth-subtitle {
            text-align: center;
            color: #9b9b9b;
            font-size: 14px;
            margin-bottom: 26px;
        }

        /* Inputs */
        .stTextInput input {
            background-color: #2f2f2f !important;
            color: #ececec !important;
            border: 1px solid #4b4b4b !important;
            border-radius: 10px !important;
            padding: 10px 12px !important;
        }
        .stTextInput input::placeholder { color: #7a7a7a !important; }
        .stTextInput input:focus {
            border: 1px solid #10a37f !important;
            box-shadow: none !important;
        }
        .stTextInput label {
            color: #d4d4d4 !important;
            font-size: 13px !important;
        }

        /* Select box (Log In / Sign Up switch) */
        div[data-baseweb="select"] > div {
            background-color: #2f2f2f !important;
            border: 1px solid #4b4b4b !important;
            border-radius: 10px !important;
            color: #ececec !important;
        }
        div[data-baseweb="select"] * { color: #ececec !important; }

        /* Primary buttons */
        div.stButton > button {
            width: 100% !important;
            background-color: #10a37f !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px !important;
            font-weight: 500 !important;
            margin-top: 4px;
            transition: background-color 0.15s ease-in-out;
        }
        div.stButton > button:hover {
            background-color: #0d8a6b !important;
            color: white !important;
        }

        .link-row { text-align: center; color: #7a7a7a; font-size: 13px; margin: 10px 0 2px 0; }

        div[data-testid="stAlert"] { border-radius: 10px !important; }
        hr.auth-divider { border: none; border-top: 1px solid #3a3a3a; margin: 22px 0; }
        </style>
    """, unsafe_allow_html=True)


def main():
    inject_css()

    st.markdown("<div class='auth-title'>EduBot</div>", unsafe_allow_html=True)
    st.markdown("<div class='auth-subtitle'>Your AI study companion</div>", unsafe_allow_html=True)

    option = st.selectbox("Choose an option", ["Log In", "Sign Up"], label_visibility="collapsed")

    users_data = load_users()

    if option == "Sign Up":
        email = st.text_input("Email", placeholder="Enter your email")
        username = st.text_input("Username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Create a password")

        if st.button("Sign Up"):
            if not (email and username and password):
                st.error("Please fill in all fields")
            else:
                users = load_users()

                email_taken = any(u["email"] == email for u in users["users"])
                user_taken = any(u["username"] == username for u in users["users"])

                if email_taken or user_taken:
                    dup_msg = []
                    if email_taken: dup_msg.append("e-mail")
                    if user_taken: dup_msg.append("username")
                    joined = " and ".join(dup_msg)
                    st.warning(f"That {joined} is already registered. Please log in instead")
                else:
                    add_new_user(email, username, password)
                    st.success("Account created successfully! You can now log in.")

    elif option == "Log In":
        # ── 1️⃣  STANDARD LOGIN  ──────────────────────────────
        login_username = st.text_input("Username", key="login_username",
                                        placeholder="Enter your username")
        login_password = st.text_input("Password", key="login_password",
                                        placeholder="Enter your password", type="password")

        if st.button("Log In"):
            if not (login_username and login_password):
                st.error("Please fill both fields.")
            elif check_user_credentials(login_username, login_password):
                st.session_state["is_logged_in"] = True
                st.session_state["logged_once"] = True
                st.session_state.username = login_username
                set_cookie(COOKIE_KEY, login_username)
                st.success(f"Welcome {login_username}! Redirecting to Bot…")
                st.session_state["page"] = "chatbot"
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("<div class='link-row'>or</div>", unsafe_allow_html=True)

        # ── 2️⃣  FORGOT‑PASSWORD (OTP) FLOW  ──────────────────
        if "fp_stage" not in st.session_state:  # track stage: 0 idle, 1 got e‑mail, 2 otp ok
            st.session_state.fp_stage = 0  # 0: waiting

        # ► Stage‑0: show link
        if st.button("Forgot Password?"):
            st.session_state.fp_stage = 1

        # ► Stage‑1: ask for e‑mail and send OTP
        if st.session_state.fp_stage == 1:
            email_input = st.text_input("Enter your registered e‑mail")
            if st.button("Send OTP"):
                user = next((u for u in users_data["users"]
                             if u["username"] == login_username and u["email"] == email_input), None)
                if not login_username:
                    st.error("Enter your username above first.")
                elif not email_input:
                    st.error("Enter your e‑mail.")
                elif not user:
                    st.error("Username & e‑mail pair not found.")
                else:
                    otp = f"{random.randint(100000, 999999)}"
                    try:
                        send_otp_email(email_input, otp)
                        st.session_state.fp_otp = otp
                        st.session_state.fp_username = login_username
                        st.session_state.fp_timestamp = time.time()
                        st.session_state.fp_stage = 2
                        st.success("OTP sent! Check your inbox.")
                    except Exception as e:
                        st.error(f"E‑mail failed ➜ {e}")

        # ► Stage‑2: verify OTP & set new password
        if st.session_state.fp_stage == 2:
            entered_otp = st.text_input("Enter the 6‑digit OTP")
            new_pw1 = st.text_input("New password", type="password")
            new_pw2 = st.text_input("Confirm password", type="password")

            if st.button("Reset Password"):
                expired = time.time() - st.session_state.fp_timestamp > 300  # 5 min
                if expired:
                    st.error("OTP expired — click *Forgot Password?* again.")
                    st.session_state.fp_stage = 0
                elif entered_otp != st.session_state.fp_otp:
                    st.error("Incorrect OTP.")
                elif new_pw1 != new_pw2 or not new_pw1:
                    st.error("Passwords don’t match or are empty.")
                else:
                    # store new password
                    for usr in users_data["users"]:
                        if usr["username"] == st.session_state.fp_username:
                            usr["password"] = bcrypt.hashpw(new_pw1.encode(), bcrypt.gensalt()).decode()
                            save_users(users_data)
                            break
                    st.success("Password reset! Please log in with the new password.")
                    # clear fp session keys
                    for k in ("fp_stage", "fp_otp", "fp_username", "fp_timestamp"):
                        st.session_state.pop(k, None)


main()
