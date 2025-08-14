import os, requests
from fastapi import APIRouter, Depends, Body
from .deps import require_user
from .query import run_query

router = APIRouter(prefix="/demos", tags=["demos"])

def llm_text(prompt: str)->str:
    # Simple helper using the same provider selection as nlsql
    from .nlsql import _call_llm
    return _call_llm(prompt)

@router.get("/inventory-risk")
def inventory_risk(user=Depends(require_user)):
    sql = f"""
SELECT sku, location_id, days_of_supply, risk_flag
FROM vw_inventory_health
WHERE tenant_id = '{user.tenant_id}' AND risk_flag = 1
ORDER BY days_of_supply ASC
LIMIT 20
"""
    res = run_query(sql, tenant_id=user.tenant_id)
    rows = res["rows"]
    prompt = "Make 5 bullets highlighting low Days-of-Supply SKUs and suggest actions. Data: "+str(rows)
    return {"sql": res["sql"], "narrative": llm_text(prompt)}

@router.get("/carrier-qbr")
def carrier_qbr(user=Depends(require_user)):
    sql = f"""
SELECT carrier_name, sum(shipments) AS shipments, avg(on_time_rate) AS on_time_rate, avg(cost_per_mile) AS cost_per_mile
FROM vw_carrier_kpi
WHERE tenant_id = '{user.tenant_id}' AND ship_date >= addDays(today(), -30)
GROUP BY carrier_name
ORDER BY shipments DESC
LIMIT 50
"""
    res = run_query(sql, tenant_id=user.tenant_id)
    rows = res["rows"]
    prompt = "Write a short QBR summary (bullets) for carriers. Flag on_time_rate < 0.9 and cost_per_mile outliers. Data: "+str(rows)
    return {"sql": res["sql"], "narrative": llm_text(prompt)}

@router.get("/lane-insight")
def lane_insight(user=Depends(require_user)):
    sql = f"""
SELECT origin_state, dest_state, avg_cost_mi, p95_transit, volume
FROM vw_lane_perf
WHERE tenant_id = '{user.tenant_id}'
ORDER BY volume DESC
LIMIT 50
"""
    res = run_query(sql, tenant_id=user.tenant_id)
    rows = res["rows"]
    prompt = "Analyze lanes for savings and service risk (<=10 bullets). Data: "+str(rows)
    return {"sql": res["sql"], "narrative": llm_text(prompt)}

@router.post("/replenishment")
def replenishment(payload: dict = Body(...), user=Depends(require_user)):
    sku = payload.get("sku","SKU1"); location = payload.get("location_id","ATL_DC")
    usage_sql = f"""
SELECT anyHeavy(it.sku) AS sku, greatest(avg(o.qty), 0.0001) AS avg_daily
FROM fact_orders o LEFT JOIN dim_item it USING (tenant_id, sku_id)
WHERE o.tenant_id = '{user.tenant_id}' AND it.sku = '{sku}'
"""
    inv_sql = f"""
SELECT (on_hand + inbound - reserved) AS net, any(unit_cost) AS unit_cost
FROM fact_inventory WHERE tenant_id = '{user.tenant_id}' AND location_id = '{location}' AND sku_id IN
 (SELECT sku_id FROM dim_item WHERE tenant_id = '{user.tenant_id}' AND sku = '{sku}')
ORDER BY as_of_date DESC LIMIT 1
"""
    avg_daily = (run_query(usage_sql, tenant_id=user.tenant_id)["rows"] or [{"avg_daily":10.0}])[0]["avg_daily"]
    inv = (run_query(inv_sql, tenant_id=user.tenant_id)["rows"] or [{"net":100,"unit_cost":10.0}])[0]
    lead, safety = 7, 5
    reorder_point = avg_daily*(lead+safety)
    qty = max(0, reorder_point - inv["net"])
    prompt = f"Explain in <=5 bullets a replenishment for {sku}@{location}: avg_daily={avg_daily:.2f}, net={inv['net']}, lead={lead}, safety={safety}, qty={int(qty)}, unit_cost={inv['unit_cost']}."
    return {"inputs": {"sku":sku,"location":location,"avg_daily":avg_daily,"net_on_hand":inv["net"],"lead_time_days":lead,"safety_days":safety,"proposed_qty":int(qty),"unit_cost":inv["unit_cost"]},
            "narrative": llm_text(prompt)}
