import hmac
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def require_login():
    """Stop the page until the right password has been typed."""
    expected = os.getenv("DASHBOARD_PASSWORD")
    if not expected:
        st.error("DASHBOARD_PASSWORD is not set in the .env file")
        st.stop()

    if st.session_state.get("authenticated"):
        with st.sidebar:
            if st.button("Log out"):
                st.session_state["authenticated"] = False
                st.rerun()
        return

    st.title("NetOps Controller")
    with st.form("login"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        if hmac.compare_digest(password.encode(), expected.encode()):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Wrong password")
    st.stop()