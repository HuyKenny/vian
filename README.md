# vian.cz

Static price comparison of furniture and home décor from Czech e-shops (affiliate feeds from CJ), organised by room,
with a width filter in centimetres ("does it fit?") and variants of one model on one page.

- `scripts/fetch.py` — download offers from the networks into `data/raw/` (not committed)
- `scripts/taxonomy.py` — rooms and categories, classifier, colours, materials, styles, dimensions
- `scripts/catalog.py` — match offers across shops (EAN), merge variants of one model, stable slugs, price history
- `scripts/landings.py` — long-tail pages: category × colour / material / style / size / width / price
- `scripts/build.py` + `render.py` + `texts.py` — plain-Python static site generator → `dist/`
- `scripts/deploy.py` — Cloudflare Workers **static assets only** (no Worker script, nothing billed per request);
  product pages are split into shard Workers when one Worker would exceed 100 000 files
- `.github/workflows/build.yml` — nightly build in GitHub Actions (01:00 CET)

## Secrets

This repository is public. It contains code only: no API keys, no feed URLs, no catalogue data.
Keys live in GitHub Actions secrets; the build state is stored as an **encrypted** release asset (`scripts/state.sh`).
`scripts/verify_no_secrets.py` and gitleaks run on every build and fail it if a secret value shows up in the repo or the output.
Affiliate IDs inside product links (CJ website id) are public by nature.

Python 3.11+, standard library only. Illustrations made in Canva; fonts Fraunces and Onest (SIL OFL, see `static/fonts/`).
