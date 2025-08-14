# Cloud Runbook
1) ClickHouse Cloud: create DB `scm`. Save host, 8443, user, password.
2) LLM: NVIDIA AI Endpoints (NVIDIA_API_KEY) or Together (OPENAI_API_KEY + OPENAI_BASE_URL=https://api.together.xyz/v1).
3) Push repo to GitHub.
4) Render: New → Blueprint → your repo.
   - API env: CH_*, APP_SECRET, plus your LLM keys.
   - UI env: API_URL = public URL of API, DEMO_TENANT=demo.
5) UI: ⚙️ Admin → Mint token → Home paste token.
6) 📥 Upload seeds → 📊 Dashboards → 🤖 Ask AI (guarded) → 🧪 Demos.
