import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json, base64

# --- LOAD FIREBASE FROM BASE64 SECRET ---
try:
    firebase_key_b64 = st.secrets["FIREBASE_KEY_BASE64"]
    firebase_key_json = json.loads(base64.b64decode(firebase_key_b64))
    cred = credentials.Certificate(firebase_key_json)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"Firebase initialization failed: {e}")

# --- LOAD OPENROUTER API KEY ---
try:
    openai.api_key = st.secrets["OPENROUTER_API_KEY"]
    openai.api_base = "https://openrouter.ai/api/v1"
except Exception as e:
    st.error(f"OpenAI API key load failed: {e}")

MODEL = "meta-llama/llama-3-8b-instruct"

# --- PAGE CONFIG ---
st.set_page_config(page_title="Zyana - AI Companion", page_icon="💜", layout="wide")

# --- SESSION STATE ---
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

# --- CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
html, body, .stApp { font-family: 'Poppins', sans-serif; background: linear-gradient(to bottom right, #e6ddf5, #d1c4e9); }
.block-container { max-width: 700px; margin: 0 auto; padding: 2rem 1rem; }
.stTextArea > div > textarea { border-radius: 16px !important; padding: 1rem 1.2rem !important; background-color: #f6f2ff !important; }
.stButton > button { background-color: #6a5acd !important; color: white !important; border-radius: 20px !important; padding: 0.4rem 1.5rem; }
.chat-bubble { border-radius: 24px; padding: 1rem 1.3rem; margin: 0.4rem 0; max-width: 90%; line-height: 1.6; font-size: 1.1rem; }
.user { background-color: #ffffff; align-self: flex-end; margin-left: auto; }
.bot { background-color: #f3e8ff; align-self: flex-start; margin-right: auto; }
.chat-container { display: flex; flex-direction: column; gap: 0.6rem; overflow-y: auto; max-height: calc(100vh - 240px); margin-bottom: 1rem; }
.input-area { position: fixed; bottom: 0; left: 0; right: 0; background: #ede4ff; padding: 1.2rem 2rem; box-shadow: 0 -4px 20px rgba(0,0,0,0.08); }
.input-wrapper { max-width: 700px; margin: 0 auto; padding: 1rem 1.2rem; background: #f4eaff; border: 1px solid #d0b9ff; border-radius: 16px; }
</style>
""", unsafe_allow_html=True)

# --- TITLE ---
st.title("💜 ZYANA - Your AI Mental Health Companion")
st.caption("I'm here to support and listen to you like a true friend. If you're in crisis, please seek professional help.")

# --- CHAT DISPLAY ---
chat_placeholder = st.container()
with chat_placeholder:
    st.markdown('<div class="chat-container" id="chat-scroll">', unsafe_allow_html=True)
    for msg in st.session_state.messages[1:]:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(f'<div class="chat-bubble user"><strong>You:</strong><br>{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble bot"><strong>Zyana:</strong><br>{content}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- AUTO SCROLL ---
st.markdown("""
<script>
setTimeout(() => {
  const chatDiv = window.parent.document.querySelector('.chat-container');
  if (chatDiv) chatDiv.scrollTop = chatDiv.scrollHeight;
}, 100);
</script>
""", unsafe_allow_html=True)

# --- INPUT BOX ---
st.markdown('<div class="input-area">', unsafe_allow_html=True)
st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area("Type something kind...", key="input_text", height=80, label_visibility="collapsed", disabled=st.session_state.is_processing)
    submitted = st.form_submit_button("Send")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- ENTER TO SEND ---
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

# --- HANDLE CHAT ---
if submitted and user_input.strip() and not st.session_state.is_processing:
    st.session_state.is_processing = True
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        try:
            response = openai.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages,
            )
            bot_reply = response.choices[0].message["content"]
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})

            db.collection("chat_history").add({
                "user": user_input,
                "bot": bot_reply,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            st.session_state.is_processing = False
    st.rerun()
