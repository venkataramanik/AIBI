from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from .deps import require_user, issue_token
from .ingest import ingest_csv
from .query import run_query
from .nlsql import ask_sql
from .demos import router as demos_router
from .ask_guarded import router as ask_guarded_router

app = FastAPI(title="SCM AI BI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"])

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest/csv")
async def ingest_csv_route(kind: str, tenant_id: str, file: bytes = Body(...), user=Depends(require_user)):
    rows = ingest_csv(kind, tenant_id, file)
    return {"ingested": rows}

@app.post("/query")
async def query(sql: str = Body(..., embed=True), user=Depends(require_user)):
    result = run_query(sql, tenant_id=user.tenant_id)
    return result

@app.post("/ask")
async def ask(prompt: str = Body(..., embed=True), user=Depends(require_user)):
    return ask_sql(prompt, tenant_id=user.tenant_id)

# Dev-only token mint (remove in prod)
@app.post("/dev/mint-token")
def mint_token(payload: dict = Body(...)):
    email = payload.get("email","demo@example.com")
    tenant_id = payload.get("tenant_id","demo")
    return {"token": issue_token(email, tenant_id, role="admin", ttl=3600)}

app.include_router(demos_router)
app.include_router(ask_guarded_router)
