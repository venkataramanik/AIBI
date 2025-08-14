import os, requests, streamlit as st
API=os.getenv("API_URL","http://api:8000")
TENANT=os.getenv("DEMO_TENANT","demo")
st.title("📥 Upload Data")
if not st.session_state.get("token"): st.warning("Login first on Home page."); st.stop()


def upload(kind):
    f = st.file_uploader(f"Upload {kind}.csv", type=["csv"], key=kind)
    if f:
        files = {"file": (f.name, f.getvalue(), "text/csv")}
        data = {"kind": kind, "tenant_id": TENANT}
        r = requests.post(
            f"{API}/ingest/upload",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {st.session_state.token}"},
        )
        if r.ok:
            st.success(r.json())
        else:
            st.error(f"{r.status_code}: {r.text}")
