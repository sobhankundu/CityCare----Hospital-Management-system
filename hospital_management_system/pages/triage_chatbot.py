import streamlit as st

from ml.chatbot import ChatState, respond
from utils.ui import inject_css, page_header

inject_css()
page_header("Triage Chatbot", eyebrow="AI-Assisted Triage")
st.caption(
    "Describe your symptoms in plain language. This assistant uses keyword/typo-tolerant "
    "matching plus the same ML model as the Symptom Checker -- it's not a large language "
    "model, so its responses are predictable and every recommendation is auditable."
)

if "chat_state" not in st.session_state:
    st.session_state.chat_state = ChatState()
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hi, I'm the triage assistant. What symptoms are you experiencing?"}
    ]

if st.button("Start a new conversation"):
    st.session_state.chat_state = ChatState()
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hi, I'm the triage assistant. What symptoms are you experiencing?"}
    ]
    st.rerun()

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Describe how you're feeling...")
if user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    reply, new_state = respond(user_input, st.session_state.chat_state)
    st.session_state.chat_state = new_state
    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
    st.rerun()
