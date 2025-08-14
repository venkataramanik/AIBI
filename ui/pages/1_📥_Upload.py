import os, requests, streamlit as st
API=os.getenv("API_URL","http://api:8000")
TENANT=os.getenv("DEMO_TENANT","demo")
st.title("📥 Upload Data")
if not st.session_state.get("token"): st.warning("Login first on Home page."); st.stop()

def upload(kind):
    f=st.file_uploader(f"Upload {kind}.csv", type=["csv"], key=kind)
    if f:
        b=f.getvalue()
        r=requests.post(f"{API}/ingest/csv", params={"kind":kind,"tenant_id":TENANT}, data=b,
                        headers={"Authorization": f"Bearer {st.session_state.token}"})
        st.success(r.json() if r.ok else r.text)

for k in ["locations","carriers","items","shipments","inventory","orders"]:
    with st.expander(k.upper(), expanded=False): upload(k)
