import os, requests
from .query import run_query
OLLAMA=os.getenv("OLLAMA_HOST","http://ollama:11434")
MODEL=os.getenv("OLLAMA_MODEL","llama3.1:8b")

SCHEMA_OVERVIEW = (
  "Views (read-only):\n"
  "- vw_carrier_kpi(tenant_id, ship_date, carrier_name, on_time_rate, cost_per_mile, shipments)\n"
  "- vw_lane_perf(tenant_id, origin_state, dest_state, avg_cost_mi, p95_transit, volume)\n"
  "- vw_inventory_health(tenant_id, as_of_date, sku, location_id, days_of_supply, turns, risk_flag)\n"
  "Rules: filter by tenant_id; default last 90 days; limit 500.\n"
)
PROMPT_TEMPLATE = (
  "Generate a ClickHouse SELECT using only the whitelisted views. "
  "Filter tenant_id = '{tenant_id}', default last 90 days if a date exists, LIMIT 500.\n"
  "Schema:\n{schema}\nQuestion: {q}\nSQL:\n"
)

# Optional hosted OSS LLM (OpenAI-compatible, e.g., Together)
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY","")
OPENAI_BASE_URL=os.getenv("OPENAI_BASE_URL","")

def _call_llm(prompt: str)->str:
    if OPENAI_API_KEY and OPENAI_BASE_URL:
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
        body={"model":"meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo","messages":[{"role":"user","content":prompt}],
              "max_tokens":512,"temperature":0.2}
        r=requests.post(f"{OPENAI_BASE_URL}/chat/completions", json=body, headers=headers, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    # Fallback to Ollama
    r=requests.post(f"{OLLAMA}/api/generate", json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=120)
    r.raise_for_status()
    return r.json().get("response","")

def ask_sql(question: str, tenant_id: str):
    prompt = PROMPT_TEMPLATE.format(schema=SCHEMA_OVERVIEW, q=question.strip(), tenant_id=tenant_id)
    sql = _call_llm(prompt).strip()
    return run_query(sql, tenant_id)
