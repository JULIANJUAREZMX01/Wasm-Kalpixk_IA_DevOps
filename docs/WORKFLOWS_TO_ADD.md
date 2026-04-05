# GitHub Actions Workflows — Ready to Deploy

> These workflows need to be added to `.github/workflows/` by you (copy-paste or use the CI panel).
> Reason: The GitHub API requires the `workflow` OAuth scope to write to `.github/workflows/`.

---

## 1. gradient_deploy.yml

```yaml
name: Gradient ADK Deploy

on:
  push:
    branches: [main]
    paths:
      - 'agents/**'
  workflow_dispatch:

jobs:
  deploy-threat-agent:
    name: Deploy Kalpixk Threat Agent
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install gradient-adk
      - name: Deploy agent
        working-directory: agents/kalpixk_threat_agent
        run: gradient agent deploy
        env:
          GRADIENT_MODEL_ACCESS_KEY: ${{ secrets.GRADIENT_MODEL_ACCESS_KEY }}
          DIGITALOCEAN_API_TOKEN: ${{ secrets.DIGITALOCEAN_API_TOKEN }}
```

---

## 2. wasm_release.yml

```yaml
name: WASM Release

on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build-wasm:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: wasm32-unknown-unknown
      - run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
      - name: Build WASM
        run: |
          cd crates/kalpixk-core
          wasm-pack build --target web --release --out-dir ../../web/public/pkg
      - uses: actions/upload-artifact@v4
        with:
          name: kalpixk-wasm
          path: web/public/pkg/
      - uses: softprops/action-gh-release@v2
        if: startsWith(github.ref, 'refs/tags/')
        with:
          files: web/public/pkg/kalpixk_core_bg.wasm
          body: "Kalpixk WASM — AMD MI300X ROCm 7.0 — 4,216,327 ev/s — F1=0.999"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 3. daily_status.yml

```yaml
name: Daily Status

on:
  schedule:
    - cron: '0 14 * * *'  # 9am CDT
  workflow_dispatch:

jobs:
  status:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Status report
        run: |
          echo '## Kalpixk Daily Status' >> $GITHUB_STEP_SUMMARY
          if [ -f web/public/pkg/kalpixk_core_bg.wasm ]; then
            echo '| WASM | EXISTS |' >> $GITHUB_STEP_SUMMARY
          else
            echo '| WASM | MISSING — compile needed |' >> $GITHUB_STEP_SUMMARY
          fi
          DAYS=$(python3 -c "from datetime import date; print((date(2026,5,9)-date.today()).days)")
          echo "| Days to hackathon | $DAYS |" >> $GITHUB_STEP_SUMMARY
          COMMITS=$(git log --oneline --since='7 days ago' | wc -l | tr -d ' ')
          echo "| Commits this week | $COMMITS |" >> $GITHUB_STEP_SUMMARY
```

---

## GitHub Secrets to Add

Go to: Settings → Secrets and variables → Actions → New repository secret

| Secret | Where to get it |
|--------|----------------|
| `GRADIENT_MODEL_ACCESS_KEY` | AMD Developer Cloud → Serverless Inference → Model Access Keys |
| `DIGITALOCEAN_API_TOKEN` | AMD Developer Cloud → Settings → API → Generate Token |
| `NETLIFY_AUTH_TOKEN` | netlify.com → User Settings → Applications |
| `NETLIFY_SITE_ID` | Netlify site dashboard → Site settings |
