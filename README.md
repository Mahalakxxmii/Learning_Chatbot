# EduBot 📘

An AI-powered study chatbot — chat naturally with an LLM for help on any topic, or upload a PDF to get an instant summary or auto-generated questions from it.

## Demo

https://github.com/user-attachments/assets/f3f466cc-7d7b-4b16-a838-43dc98f508c5

## Features
- 🤖 Conversational AI chatbot (powered by OpenRouter) — ask questions, get explanations, general Q&A
- 📄 PDF upload — summarize documents or generate exam/interview-style questions from them
- 🔐 User authentication — signup/login with hashed passwords
- 🔑 Forgot password flow with OTP email verification
- 💬 Persistent chat history per user
- 🎨 ChatGPT-style dark UI built with Streamlit

## Tech stack
- Python, Streamlit
- OpenRouter API (LLM inference)
- pdfplumber / PyPDF2 (PDF text extraction)
- bcrypt (password hashing)

## Setup
1. Clone the repo and install dependencies:
```bash
   pip install -r requirements.txt
```
2. Create a `.env` file with your API keys:

OPENROUTER_API_KEY=your_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

3. Run the app:
```bash
   streamlit run app.py
```
