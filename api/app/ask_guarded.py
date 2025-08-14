from pathlib import Path
from fastapi import APIRouter, Body, HTTPException, Header
from nemoguardrails import LLMRails, RailsConfig
from .deps import verify_token
from .query import run_query

router = APIRouter()

CFG_DIR = Path(__file__).resolve().parents[1] / "guardrails"
cfg = RailsConfig.from_path(str(CFG_DIR))
rails = LLMRails(cfg)

@router.post("/ask_guarded")
async def ask_guarded(
    prompt: str = Body(..., embed=True),
    authorization: str | None = Header(None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing auth")
    token = authorization.split()[1]
    user = verify_token(token)

    # Expose tenant_id to the Colang docstring ({{ tenant_id }})
    rails.register_prompt_context("tenant_id", user.tenant_id)

    # Provide both context and the user message (supported by LLMRails) 
    # so {{ question }} in the flow equals the last user utterance.
    messages = [
        {"role": "context", "content": {"tenant_id": user.tenant_id}},
        {"role": "user", "content": prompt},
    ]

    try:
        result = await rails.generate_async(messages=messages)
        # result may be a dict or object; normalize to text
        sql = getattr(result, "output", None) or result.get("content") or result.get("output", "")
    except Exception:
        result = rails.generate(messages=messages)
        sql = getattr(result, "output", None) or result.get("content") or result.get("output", "")

    lowered = (sql or "").lower()
    if any(bad in lowered for bad in ["insert", "update", "delete", "drop", "alter", "truncate", "create"]):
        raise HTTPException(400, "Only SELECT/WITH queries allowed.")
    if "tenant_id" not in lowered:
        raise HTTPException(400, "tenant_id filter required.")

    return run_query(sql, tenant_id=user.tenant_id)
