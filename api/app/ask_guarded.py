from fastapi import APIRouter, Depends, Body, HTTPException, Header
from nemoguardrails import LLMRails, RailsConfig
from .deps import verify_token
from .query import run_query

router = APIRouter()

cfg = RailsConfig.from_path("api/guardrails")
rails = LLMRails(cfg)

@router.post("/ask_guarded")
async def ask_guarded(prompt: str = Body(..., embed=True), authorization: str | None = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing auth")
    token = authorization.split()[1]
    user = verify_token(token)

    try:
        result = await rails.generate_async(messages=[{"role":"user","content":prompt}])
        sql = result.output.strip()
    except Exception:
        result = rails.generate(messages=[{"role":"user","content":prompt}])
        sql = (result.get("output") if isinstance(result, dict) else getattr(result, "output", "")) or ""

    lowered = sql.lower()
    if any(bad in lowered for bad in ["insert","update","delete","drop","alter","truncate","create"]):
        raise HTTPException(400, "Only SELECT/WITH queries allowed.")
    if "tenant_id" not in lowered:
        raise HTTPException(400, "tenant_id filter required.")
    return run_query(sql, tenant_id=user.tenant_id)
