import os, requests, streamlit as st
API=os.getenv("API_URL","http://api:8000")
TENANT=os.getenv("DEMO_TENANT","demo")
st.title("⚙️ Admin (Demo Token)")
email = st.text_input("Demo email", value="demo@example.com")
if st.button("Mint demo token"):
    r=requests.post(f"{API}/dev/mint-token", json={"email": email, "tenant_id": TENANT})
    st.code(r.json().get("token","<error>") if r.ok else r.text)
