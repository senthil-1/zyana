import streamlit as st
import openai
import base64
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- FIREBASE INITIALIZATION ---
try:
    firebase_json = base64.b64decode(st.secrets["firebase_key"]).decode("utf-8")
    firebase_dict = json.loads(firebase_json)
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"🔥 Firebase init failed: {e}")

# --- OPENAI CONFIGURATION ---
openai.api_key = st.secrets["openrouter_api_key"]
openai.api_base = "https://openrouter.ai/api/v1"
MODEL = "meta-llama/llama-3-8b-instruct"

# --- PAGE CONFIG ---
st.set_page_config(page_title="Zyana - AI Companion", page_icon="💜", layout="wide")

# --- SESSION STATE INIT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are a warm, friendly, and supportive companion. "
                "You speak gently and like a close friend, helping the user feel heard and safe. "
                "Avoid giving medical or crisis hotline advice unless absolutely necessary. "
                "Your goal is to comfort, encourage, and validate the user's feelings like a true friend would."
            )
        }
    ]

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# --- STYLES ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
html, body, .stApp {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(to bottom right, #e6ddf5, #d1c4e9);
    color: #333;
}
.block-container {
    max-width: 700px;
    margin: 0 auto;
}
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    overflow-y: auto;
    max-height: calc(100vh - 240px);
    margin-bottom: 1rem;
    padding-right: 1rem;
}
.chat-bubble {
    border-radius: 24px;
    padding: 1rem 1.3rem;
    max-width: 90%;
    line-height: 1.6;
    font-size: 1.1rem;
}
.user {
    background-color: #fff;
    align-self: flex-end;
    margin-left: auto;
}
.bot {
    background-color: #f3e8ff;
    align-self: flex-start;
    margin-right: auto;
}
.input-area {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #ede4ff;
    padding: 1.2rem 2rem;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.08);
    z-index: 999;
}
.input-wrapper {
    max-width: 700px;
    margin: 0 auto;
    padding: 1rem 1.2rem;
    background: #f4eaff;
    border: 1px solid #d0b9ff;
    border-radius: 16px;
}
.stTextArea > div > textarea {
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    background-color: #f6f2ff !important;
    font-size: 1rem !important;
}
.stButton > button {
    background-color: #6a5acd !important;
    color: white !important;
    font-weight: 600;
    border-radius: 20px !important;
    padding: 0.4rem 1.5rem;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("💜 ZYANA - Your AI Mental Health Companion")
st.caption("I'm here to support and listen to you like a true friend. If you're in crisis, please seek professional help.")

# --- CHAT UI ---
chat_placeholder = st.container()
with chat_placeholder:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages[1:]:
        role_class = "user" if msg["role"] == "user" else "bot"
        label = "You" if msg["role"] == "user" else "Zyana"
        st.markdown(f'<div class="chat-bubble {role_class}"><strong>{label}:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- AUTO SCROLL ---
st.markdown("""
<script>
setTimeout(() => {
  const chatDiv = window.parent.document.querySelector('.chat-container');
  if (chatDiv) {
    chatDiv.scrollTop = chatDiv.scrollHeight;
  }
}, 100);
</script>
""", unsafe_allow_html=True)

# --- INPUT FORM ---
st.markdown('<div class="input-area"><div class="input-wrapper">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area("Type something kind...", key="input_text", height=80, label_visibility="collapsed")
    submitted = st.form_submit_button("Send")
st.markdown('</div></div>', unsafe_allow_html=True)

# --- ENTER TO SUBMIT ---
st.markdown("""
<script>
document.addEventListener("DOMContentLoaded", function() {
    const textarea = window.parent.document.querySelector("textarea");
    if (textarea) {
        textarea.addEventListener("keydown", function(e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                textarea.blur();
            }
        });
    }
});
</script>
""", unsafe_allow_html=True)

# --- HANDLE RESPONSE ---
# --- HANDLE RESPONSE ---
if submitted and user_input.strip() and not st.session_state.is_processing:
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})
    st.session_state.is_processing = True

    with st.spinner("Zyana is typing..."):
        try:
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=st.session_state.messages
            )
            print("🔍 DEBUG:", response)

            reply = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": reply})

            db.collection("zyana_chat").add({
                "user_input": user_input.strip(),
                "bot_reply": reply,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            st.error(f"❌ API Error: {e}")
            if 'response' in locals():
                st.error(f"Raw response: {response}")
        finally:
            st.session_state.is_processing = False
            st.rerun()
