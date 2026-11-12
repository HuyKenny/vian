#!/usr/bin/env python3
"""Deploy dist/ as Workers static assets — no Worker script anywhere, so no request is ever billed.

    python3 scripts/deploy.py staging       # one Worker "vian-staging" on workers.dev (noindex build, must fit one Worker)
    python3 scripts/deploy.py production    # main Worker on vian.cz/* (+ www) and, if needed, shard Workers

A Worker version holds at most 100 000 files. When dist/ is bigger, product pages /produkt/<x>… are moved into shard
Workers by the first character of the slug; each shard gets the route vian.cz/produkt/<x>* (more specific routes
win over vian.cz/*). Every shard is assets-only too.
Needs CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID in the environment (GitHub secrets). Prints no secrets.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
DIST = APP / "dist"
LIMIT = 95_000
WRANGLER = "wrangler@4.151.3"
ZONE = "vian.cz"


def count(d):
    return sum(1 for p in d.rglob("*") if p.is_file())


FORBIDDEN = ("main", "d1_databases", "kv_namespaces", "r2_buckets", "durable_objects", "queues", "services", "ai", "browser",
             "vectorize", "hyperdrive", "analytics_engine_datasets", "triggers", "cron", "workflows")


def wrangler(cfg, name):
    """Cost guard: this site must stay assets-only (no Worker script, no D1/KV/R2/AI binding, no cron) — static asset
    requests are free, anything with code or storage is billed on the shared Cloudflare account."""
    bad = [k for k in FORBIDDEN if k in cfg]
    if bad:
        sys.exit(f"refusing to deploy {name}: billed features in config: {bad}")
    if set(cfg.get("assets", {})) - {"directory", "html_handling", "not_found_handling"}:
        sys.exit(f"refusing to deploy {name}: unexpected assets options")
    path = APP / f".wrangler-{name}.json"
    path.write_text(json.dumps(cfg, indent=1))
    r = subprocess.run(["npx", "--yes", WRANGLER, "deploy", "--config", str(path)], cwd=APP)
    path.unlink(missing_ok=True)
    if r.returncode:
        sys.exit(f"deploy of {name} failed")


def base_cfg(name, directory):
    return {"name": name, "compatibility_date": "2026-10-01", "preview_urls": False, "observability": {"enabled": False},
            "assets": {"directory": str(directory), "html_handling": "auto-trailing-slash", "not_found_handling": "404-page"}}


def keep_live_assets():
    """Copy the hashed CSS/JS the live site uses now into dist/assets. The main Worker (which alone serves /assets/) and
    the shard Workers go live minutes apart; without the old files, pages still served by the not-yet-updated side
    reference a hash that no longer exists and render without styles (seen 12. 11. 2026)."""
    out = DIST / "assets"
    try:
        html = subprocess.run(["curl", "-sfL", "--max-time", "20", "-A", "VianDeploy/1.0", f"https://{ZONE}/"],
                              capture_output=True, text=True, timeout=30).stdout
    except Exception as e:  # noqa: BLE001 - best effort, never block a deploy
        print(f"keep_live_assets: {e}")
        return
    kept = 0
    for name in sorted(set(re.findall(r'/assets/([\w.-]+\.(?:css|js))', html))):
        if (out / name).exists():
            continue
        r = subprocess.run(["curl", "-sfL", "--max-time", "20", "-A", "VianDeploy/1.0", "-o", str(out / name), f"https://{ZONE}/assets/{name}"])
        if r.returncode:
            (out / name).unlink(missing_ok=True)
        else:
            kept += 1
    print(f"keep_live_assets: kept {kept} live asset file(s)")


def plan_shards(slugs_by_char, room):
    """Greedy: consecutive first characters into shards of <= LIMIT files each."""
    shards, cur, n = [], [], 0
    for ch in sorted(slugs_by_char):
        c = slugs_by_char[ch]
        if cur and n + c > LIMIT - 200:
            shards.append(cur)
            cur, n = [], 0
        cur.append(ch)
        n += c
    if cur:
        shards.append(cur)
    return shards


def main():
    env = sys.argv[1] if len(sys.argv) > 1 else "staging"
    total = count(DIST)
    print(f"dist: {total} files")
    if env == "staging":
        if total > LIMIT:
            sys.exit(f"staging must fit one Worker ({total} > {LIMIT}); build with VIAN_MAX_PRODUCTS")
        cfg = base_cfg("vian-staging", DIST)
        cfg["workers_dev"] = True
        wrangler(cfg, "vian-staging")
        return
    keep_live_assets()
    shard_dirs = []
    if total > LIMIT:
        prod = DIST / "produkt"
        by_char = Counter(p.name[0] for p in prod.iterdir() if p.is_dir())
        need = total - LIMIT + 2000
        moved, shards = 0, plan_shards(by_char, need)
        for i, chars in enumerate(shards):
            d = APP / f"dist-s{i:02d}"
            shutil.rmtree(d, ignore_errors=True)
            (d / "produkt").mkdir(parents=True)
            for ch in chars:
                for p in list(prod.glob(f"{ch}*")):
                    shutil.move(str(p), d / "produkt" / p.name)
            shutil.copy(DIST / "404.html", d / "404.html")
            shutil.copy(DIST / "_headers", d / "_headers")
            shard_dirs.append((f"vian-s{i:02d}", d, chars))
            moved += count(d)
            if count(DIST) <= LIMIT:
                break
        print(f"sharded: {len(shard_dirs)} shard Workers, main keeps {count(DIST)} files")
    for name, d, chars in shard_dirs:
        if count(d) > LIMIT:
            sys.exit(f"shard {name} too big")
    # main first: it carries the old and the new CSS/JS, so pages of both versions keep their styles while the shards follow
    cfg = base_cfg("vian", DIST)
    cfg["workers_dev"] = False
    cfg["routes"] = [{"pattern": f"{ZONE}/*", "zone_name": ZONE}, {"pattern": f"www.{ZONE}/*", "zone_name": ZONE}]
    wrangler(cfg, "vian")
    for name, d, chars in shard_dirs:
        cfg = base_cfg(name, d)
        cfg["workers_dev"] = False
        cfg["routes"] = [{"pattern": f"{ZONE}/produkt/{c}*", "zone_name": ZONE} for c in chars]
        wrangler(cfg, name)


if __name__ == "__main__":
    main()
