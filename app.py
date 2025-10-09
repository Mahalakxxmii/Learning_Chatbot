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
# 🧼 Hide sidebar and footer
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Load users from JSO
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

def main():
    st.markdown("""
        <style>
          .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            margin-top: 0rem !important;
            margin-bottom: 0rem !important;
            height: 100vh !important;
        }

        /* Prevent scrollbars */
        html, body, [class*="stApp"] {
            height: 100vh !important;
            overflow: hidden !important;
        }

        /* Center content vertically */
        .main {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh !important;
            padding: 0 !important;
        }
        .stApp {
           /* background-image: url("https://i.pinimg.com/1200x/a2/88/37/a28837488ede20bcfc1c931267e9c617.jpg) */
            background-color:#EFEEEA
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        /* Input field styles */
        .stTextInput input, .stPasswordInput input {
            width: 400px !important;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #ccc;
            display: block;
            margin: 0 auto;
        }
        .stTextInput, .stPasswordInput {
            width: 300px !important;
            margin: 10px auto;
            padding: 0px;
        }
        label[data-testid="stMarkdownContainer"] > div {
            text-align: center;
        }
        div[data-baseweb="select"] {
            width: 300px !important;
            margin: 0 auto 0px auto;
        }
        div.stButton > button {
    display: block!important;    /* ensures block-level for centering */
    margin: 0 auto !important;    /* horizontally center */
    width: 200px !important;         /* same width for all buttons */
    border-radius: 8px;
    border: 1px solid #ccc;
    padding: 10px;
    
}
        h1 {
            text-align: center;
        }
        h3 {
             text-align: center !important;   /* Left align headers/subheaders */
                position: relative;
            left: -100px;
    margin-left: 0px; 
            font-size: 20px !important; /* Subheader smaller */
            font-weight: normal;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.title("EduBot")


        st.subheader("Are you a new user?")
        # ✅ Use label_visibility to avoid warning
        option = st.selectbox("Choose an option", ["Sign Up", "Log In"], label_visibility="collapsed")
        

    users_data = load_users()

    if option == "Sign Up":
        st.subheader("Create an account")

        email = st.text_input("Email", placeholder="Enter your email")
        username = st.text_input("Username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Create a password")

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
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
                        joined  = " and ".join(dup_msg)
                        st.warning(f"That {joined} is already registered .""Please log in instead")
                    else:
                        add_new_user(email, username, password)
                        st.success("Account created successfully! You can now log in.")

    elif option == "Log In":
        st.subheader("Log into your account")

    # ── 1️⃣  STANDARD LOGIN  ──────────────────────────────
        login_username = st.text_input("Username", key="login_username",
                                   placeholder="Enter your username")
        login_password = st.text_input("Password", key="login_password",
                                   placeholder="Enter your password", type="password")

        col1, col2, col3 = st.columns([1, 2.3, 0.7])
        with col2:
            if st.button("Log In"):
                if not (login_username and login_password):
                    st.error("Please fill both fields.")
                elif check_user_credentials(login_username, login_password):
                    st.session_state["is_logged_in"] = True
                    st.session_state["logged_once"] = True
                    st.session_state.username = login_username
                    st.success(f"Welcome {login_username}! , Redirecting to Bot…")
                    st.session_state["page"] = "chatbot"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


        st.markdown("<p style='text-align:center;'>or</p>", unsafe_allow_html=True)

    # ── 2️⃣  FORGOT‑PASSWORD (OTP) FLOW  ──────────────────
        if "fp_stage" not in st.session_state:            # track stage: 0 idle, 1 got e‑mail, 2 otp ok
            st.session_state.fp_stage = 0                 # 0: waiting

    # ► Stage‑0: show link
        col1, col2, col3 = st.columns([1, 2.3, 0.7])
        with col2:
            if st.button("Forgot Password?"):
                st.session_state.fp_stage = 1


    # ► Stage‑1: ask for e‑mail and send OTP
        if st.session_state.fp_stage == 1:
            email_input = st.text_input("Enter your registered e‑mail")
            col1, col2, col3 = st.columns([1, 2.3, 0.7])
            with col2:
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
                            st.session_state.fp_otp        = otp
                            st.session_state.fp_username   = login_username
                            st.session_state.fp_timestamp  = time.time()
                            st.session_state.fp_stage      = 2
                            st.success("OTP sent! Check your inbox.")
                        except Exception as e:
                            st.error(f"E‑mail failed ➜ {e}")

    # ► Stage‑2: verify OTP & set new password
        if st.session_state.fp_stage == 2:
            entered_otp = st.text_input("Enter the 6‑digit OTP")
            new_pw1     = st.text_input("New password", type="password")
            new_pw2     = st.text_input("Confirm password", type="password")

            col1, col2, col3 = st.columns([1, 2.3, 0.7])
            with col2:
                if st.button("Reset Password"):

                    expired = time.time() - st.session_state.fp_timestamp > 300  # 5 min
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
                                usr["password"] = bcrypt.hashpw(new_pw1.encode(),bcrypt.gensalt()).decode()
                                save_users(users_data)
                                break
                        st.success("Password reset! Please log in with the new password.")
                # clear fp session keys
                        for k in ("fp_stage","fp_otp","fp_username","fp_timestamp"):
                            st.session_state.pop(k, None)
            


main()
