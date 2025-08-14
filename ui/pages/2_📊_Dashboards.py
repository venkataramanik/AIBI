import os, requests, pandas as pd, streamlit as st
API=os.getenv("API_URL","http://api:8000")
st.title("📊 Dashboards")
if not st.session_state.get("token"): st.warning("Login first."); st.stop()

def run(sql):
    r=requests.post(f"{API}/query", json={"sql": sql}, headers={"Authorization": f"Bearer {st.session_state.token}"})
    if not r.ok: st.error(r.text); return None
    return r.json()

sql = '''
SELECT carrier_name, sum(shipments) AS shipments, avg(on_time_rate) AS on_time_rate, avg(cost_per_mile) AS cpm
FROM vw_carrier_kpi
GROUP BY carrier_name
ORDER BY shipments DESC
LIMIT 50
'''
res=run(sql)
if res:
    st.code(res["sql"], language="sql")
    st.dataframe(pd.DataFrame(res["rows"]), use_container_width=True)
