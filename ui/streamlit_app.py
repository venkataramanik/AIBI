import os, requests, streamlit as st
API=os.getenv("API_URL","http://api:8000")
TENANT=os.getenv("DEMO_TENANT","demo")

st.set_page_config(page_title="SCM AI BI", layout="wide")
st.title("SCM AI BI Dashboard")

if "token" not in st.session_state:
    st.session_state.token=None

with st.sidebar:
    st.header("Session")
    if st.session_state.token:
        st.success("Logged in")
        if st.button("Logout"): st.session_state.token=None; st.experimental_rerun()
    else:
        st.info("Go to ⚙️ Admin to mint a demo token and paste it here.")

if not st.session_state.token:
    token = st.text_input("Paste Access Token", value="", type="password")
    if token:
        st.session_state.token = token
st.rerun()

else:
    st.write("Use pages: 📥 Upload, 📊 Dashboards, 🤖 Ask AI, 🧪 Supply Chain Demos, ⚙️ Admin.")

