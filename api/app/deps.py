import os, time, json, requests
from jose import jwt
from fastapi import Header, HTTPException

SECRET = os.getenv("APP_SECRET","change-me")
ALGO = "HS256"

class User:
    def __init__(self, sub: str, tenant_id: str, role: str="analyst"):
        self.sub=sub; self.tenant_id=tenant_id; self.role=role

def issue_token(email: str, tenant_id: str, role: str="analyst", ttl=3600):
    payload={"sub":email,"tenant_id":tenant_id,"role":role,"exp":int(time.time())+ttl}
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def verify_token(token: str)->User:
    try:
        data=jwt.decode(token, SECRET, algorithms=[ALGO])
        return User(data["sub"], data["tenant_id"], data.get("role","analyst"))
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

async def require_user(authorization: str | None = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing auth")
    token=authorization.split()[1]
    return verify_token(token)

# ClickHouse client (supports Cloud HTTPS + auth)
CH_HOST=os.getenv("CH_HOST","clickhouse")
CH_PORT=os.getenv("CH_PORT","8123")
CH_DB=os.getenv("CH_DB","scm")
CH_USER=os.getenv("CH_USER","")
CH_PASSWORD=os.getenv("CH_PASSWORD","")
CH_SECURE=os.getenv("CH_SECURE","false").lower() in ("1","true","yes")

def ch_query(sql: str):
    scheme = "https" if CH_SECURE or str(CH_PORT) == "443" or ("clickhouse.cloud" in str(CH_HOST)) else "http"
    url = f"{scheme}://{CH_HOST}:{CH_PORT}/?database={CH_DB}&default_format=JSONEachRow"
    auth = (CH_USER, CH_PASSWORD) if CH_USER or CH_PASSWORD else None
    r = requests.post(url, data=sql.encode("utf-8"), auth=auth)
    r.raise_for_status()
    return [json.loads(l) for l in r.text.splitlines() if l.strip()]
