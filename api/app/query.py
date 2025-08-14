import re
from .deps import ch_query

ALLOWED_PREFIXES=("SELECT","WITH")
DEFAULT_LIMIT=500

def inject_tenant(sql: str, tenant_id: str)->str:
    if " tenant_id " in sql or "tenant_id=" in sql or "tenant_id='" in sql:
        return sql
    if re.search(r"from\s+(scm\.)?vw_", sql, re.I):
        return re.sub(r"(?i)(group by|order by|limit|$)", f" WHERE tenant_id = '{tenant_id}' \g<1>", sql, count=1)
    return sql

def enforce_limit(sql: str)->str:
    if re.search(r"(?i)\blimit\b", sql):
        return sql
    return sql.strip().rstrip(";")+f" LIMIT {DEFAULT_LIMIT}"

def run_query(sql: str, tenant_id: str):
    sql=sql.strip()
    if not sql or not sql.upper().startswith(ALLOWED_PREFIXES):
        raise ValueError("Only SELECT/WITH queries allowed")
    sql=inject_tenant(sql, tenant_id)
    sql=enforce_limit(sql)
    rows=ch_query(sql)
    return {"sql": sql, "rows": rows, "count": len(rows)}
