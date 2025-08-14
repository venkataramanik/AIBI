import os, requests, pandas as pd, streamlit as st
API=os.getenv("API_URL","http://api:8000")
st.title("🧪 Supply Chain Demos (Open-Source LLM)")
if not st.session_state.get("token"): st.warning("Login first."); st.stop()

def show_json(title, url, method="GET", payload=None):
    st.subheader(title)
    if st.button(f"Run: {title}"):
        if method=="GET":
            r=requests.get(url, headers={"Authorization": f"Bearer {st.session_state.token}"})
        else:
            r=requests.post(url, json=payload or {}, headers={"Authorization": f"Bearer {st.session_state.token}"})
        st.json(r.json() if r.ok else {"error": r.text})

left, right = st.columns(2)
with left:
    show_json("Inventory Risk Insight", f"{API}/demos/inventory-risk")
    show_json("Lane Performance Insight", f"{API}/demos/lane-insight")
with right:
    show_json("Carrier QBR Summary", f"{API}/demos/carrier-qbr")
    sku = st.text_input("SKU", "SKU1"); loc = st.text_input("Location", "ATL_DC")
    if st.button("Run: Replenishment What-if"):
        r=requests.post(f"{API}/demos/replenishment", json={"sku":sku,"location_id":loc}, headers={"Authorization": f"Bearer {st.session_state.token}"})
        st.json(r.json() if r.ok else {"error": r.text})
