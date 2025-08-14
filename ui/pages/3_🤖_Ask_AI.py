import os, requests, pandas as pd, streamlit as st
API=os.getenv("API_URL","http://api:8000")
st.title("🤖 Ask AI (Guarded NL → SQL)")
if not st.session_state.get("token"): st.warning("Login first."); st.stop()

q=st.text_area("Question", "Which carriers had on-time < 90% last month?")
if st.button("Ask (Guarded)"):
    r=requests.post(f"{API}/ask_guarded", json={"prompt": q}, headers={"Authorization": f"Bearer {st.session_state.token}"})
    if r.ok:
        data=r.json(); st.subheader("SQL"); st.code(data.get("sql",""), language="sql"); st.subheader("Results"); st.dataframe(pd.DataFrame(data.get("rows",[])), use_container_width=True)
    else: st.error(r.text)
