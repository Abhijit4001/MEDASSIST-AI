import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

st.set_page_config(page_title="MedAssist AI", page_icon="🏥", layout="wide")

st.title("🏥 MedAssist AI")
st.caption("Your intelligent healthcare assistant — find doctors, book appointments, and more.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "patient_id" not in st.session_state:
    st.session_state.patient_id = 1

with st.sidebar:
    st.header("Settings")
    st.session_state.patient_id = st.number_input("Patient ID", min_value=1, value=1, step=1)
    st.markdown("**Try asking:**")
    st.markdown("- Find a cardiologist in Mumbai")
    st.markdown("- Book Dr. Ananya on 2026-06-12 10:00")
    st.markdown("- Show my medical records")
    st.markdown("- Set appointment reminder")
    st.markdown("- Summary for appointment #1")

    if st.button("Clear chat"):
        st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("How can I help you today?"):
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
                reply = f"Could not reach the API. Start the backend with `uvicorn app.main:app --reload`. ({exc})"
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
