import streamlit as st
import requests
import time
import threading
import streamlit_shadcn_ui as ui


# API base URL
api_base_url = "http://localhost:8001"


def init():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'status' not in st.session_state:
        st.session_state.status = 'unknown'
    if 'job_count' not in st.session_state:
        st.session_state.job_count = 0


init()


def get_access_token(username, password):
    response = requests.post(
        f"{api_base_url}/token", data={"username": username, "password": password})
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error("Failed to authenticate. Please check your username and password.")
        return None


if not st.session_state.authenticated:
    st.title('Admin Login')
    username = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        token = get_access_token(username, password)
        if token:
            st.session_state.authenticated = True
            st.session_state.token = token
            st.rerun()


def start_bot(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{api_base_url}/start_bot/", headers=headers)
    if response.status_code == 200:
        col1.toast("Bot started successfully!")
    else:
        st.error("Failed to start the bot. It might already be running.")

# Function to stop the bot


def stop_bot(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{api_base_url}/stop_bot/", headers=headers)
    if response.status_code == 200:
        st.toast("Bot stopped successfully!")
    else:
        st.error("Failed to stop the bot. It might not be running.")

# Function to get the bot status


def get_status(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{api_base_url}/status/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        st.session_state.status = data.get("status", "unknown")
        st.session_state.job_count = data.get("job_count", 0)
    else:
        st.error("Failed to get the bot status.")

# Polling function to update status


def update_status():
    while True:
        if st.session_state.authenticated:
            get_status(st.session_state.token)


# Interact with the API if authenticated
if st.session_state.authenticated:
    st.title('Job Bot Controller')
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Bot"):
            start_bot(st.session_state.token)
            get_status(st.session_state.token)

    with col2:
        if st.button("Stop Bot"):
            stop_bot(st.session_state.token)
            get_status(st.session_state.token)

    status_placeholder = col1.empty()

    with st.spinner("Checking status..."):
        get_status(st.session_state.token)

    # Display status
    with status_placeholder:
        ui.metric_card(
            title="Bot Status", content=st.session_state.status)
    with col2:
        ui.metric_card(title="Job Count", content=st.session_state.job_count)
