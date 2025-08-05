import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import base64

# Load OpenRouter API key and base
openai.api_key = st.secrets["OPENROUTER_API_KEY"]
openai.api_base = "https://openrouter.ai/api/v1"
MODEL = "meta-llama/llama-3-8b-instruct"

# Decode Firebase service key from base64
firebase_key = st.secrets["FIREBASE_KEY_BASE64"]
firebase_dict = json.loads(base64.b64decode(firebase_key))

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_dict)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Streamlit page setup
st.set_page_config(page_title="Zyana", layout="centered")
st.title("💜 Zyana – Your AI Mental Health Companion")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I'm Zyana. How are you feeling today?"}
    ]

# Display messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

# Handle user input
if prompt := st.chat_input("Share your thoughts..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # Get response from OpenRouter
        response = openai.chat.completions.create(
            model=MODEL,
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content

    except Exception as e:
        reply = f"❌ Something went wrong:\n\n`{str(e)}`"

    # Show assistant reply
    st.chat_message("assistant").markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Log conversation to Firebase
    db.collection("chat_logs").add({
        "timestamp": datetime.utcnow(),
        "user_message": prompt,
        "bot_reply": reply
    })
