# Gradient ADK — Setup Guide

> DigitalOcean Gradient AI Agent Development Kit  
> **FREE during Public Preview** — deploy agents with zero compute cost

## Quick Setup

```bash
# 1. Install
pip install gradient-adk

# 2. Get your keys from AMD Developer Cloud dashboard:
#    - GRADIENT_MODEL_ACCESS_KEY: Settings → Serverless Inference → Model Access Keys
#    - DIGITALOCEAN_API_TOKEN: Settings → API → Generate New Token
#    Scopes needed: genai (CRUD) + project (read)

# 3. Create .env
cat > .env << EOF
GRADIENT_MODEL_ACCESS_KEY=your_key_here
DIGITALOCEAN_API_TOKEN=your_token_here
EOF

# 4. Init agent
gradient agent init

# 5. Run locally
gradient agent run
# → http://localhost:8080/run

# 6. Test
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"event": {"dns_queries_per_second": 100, "failed_auth_attempts": 5}}'

# 7. Deploy
gradient agent deploy
# → https://agents.do-ai.run/v1/<id>/run
```

## Agents to Deploy

| Agent | Directory | Purpose |
|-------|-----------|---------|
| kalpixk-threat-agent | `agents/kalpixk_threat_agent/` | SIEM threat detection |
| kalpixk-wasm-demo | `agents/kalpixk_wasm_demo/` | Hackathon demo |

## GitHub Secrets Required

Add these in: Settings → Secrets and variables → Actions

```
GRADIENT_MODEL_ACCESS_KEY
DIGITALOCEAN_API_TOKEN
NETLIFY_AUTH_TOKEN      (for frontend deploy)
NETLIFY_SITE_ID         (for frontend deploy)
```

## Evaluation

```bash
gradient agent evaluate \
  --test-case-name "threat-detection-eval" \
  --dataset-file datasets/eval_threats.csv \
  --categories correctness,context_quality
```
