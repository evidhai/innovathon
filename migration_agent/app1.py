import streamlit as st
import requests
import threading
import uvicorn

from migration_agent import app as bedrock_app


def run_backend():
    uvicorn.run(bedrock_app, host="0.0.0.0", port=8002, log_level="warning")

# Start backend only once
if "backend_started" not in st.session_state:
    thread = threading.Thread(target=run_backend, daemon=True)
    thread.start()
    st.session_state.backend_started = True


st.set_page_config(page_title="AWS Migration Assistant", layout="wide")
st.title("☁️ AWS Migration Assistant")
st.write("Ask anything related to AWS migration, cost, architecture, documentation etc")

user_input = st.text_area("Enter your question:", height=100)

if st.button("Run Assistant"):
    
    if not user_input.strip():
        st.warning("Please enter a question")
        st.stop()

    payload = {"input": user_input, "user_id": "streamlit-user"}

    try:
        response = requests.post(
            "http://127.0.0.1:8002/entrypoint/migration_assistant",
            json=payload,
            timeout=300,
        )

        if response.status_code == 200:
            result = response.json()
            st.success(result["result"])
        else:
            st.error(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        st.error(str(e))
