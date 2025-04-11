import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# --- Simulasi login user ---
CREDENTIALS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

# --- Login System ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 Login Inventory System")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login = st.button("Login")

    if login:
        user = CREDENTIALS.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.success(f"✅ Berhasil login sebagai {st.session_state.role.upper()}")
            st.rerun()
        else:
            st.error("❌ Username atau password salah.")
