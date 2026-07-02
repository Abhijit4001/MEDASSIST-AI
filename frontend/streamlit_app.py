import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

st.set_page_config(page_title="MedAssist AI", page_icon="hospital", layout="wide")

st.markdown(
    """
    <style>
      .main-header {
        border: 1px solid #dbe5eb;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        background: linear-gradient(135deg, #effdfa, #f7fbff);
      }
      .main-header h1 {
        margin: 0;
        color: #081625;
      }
      .main-header p {
        margin: .35rem 0 0;
        color: #627084;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-header">
      <h1>MedAssist AI</h1>
      <p>Your intelligent healthcare assistant for doctors, appointments, records, reminders, and visit summaries.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "patient_id" not in st.session_state:
    st.session_state.patient_id = 1

with st.sidebar:
    st.header("Settings")
    st.session_state.patient_id = st.number_input("Patient ID", min_value=1, value=1, step=1)
    st.divider()
    st.markdown("**Try asking**")
    example_prompts = [
        "Find a cardiologist in Mumbai",
        "Book Dr. Ananya on 2026-06-12 10:00",
        "Show my medical records",
        "Set appointment reminder",
        "Summary for appointment #1",
    ]
    for example in example_prompts:
        if st.button(example, use_container_width=True):
            st.session_state.pending_prompt = example

    st.divider()
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []

col1, col2, col3 = st.columns(3)
col1.metric("Active patient", f"#{st.session_state.patient_id}")
col2.metric("API", API_URL.replace("http://", "").replace("https://", ""))
col3.metric("Workspace", "Care chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pending_prompt = st.session_state.pop("pending_prompt", None)
prompt = pending_prompt or st.chat_input("How can I help you today?")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={"message": prompt, "patient_id": st.session_state.patient_id},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["response"]
                st.caption(f"Intent: `{data['intent']}`")
            except requests.RequestException as exc:
                reply = (
                    "Could not reach the API. Start the backend with `python -m app`. "
                    f"({exc})"
                )
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
