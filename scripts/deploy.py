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
import time
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


def wrangler(cfg, name, cmd=("deploy",), capture=False):
    """Cost guard: this site must stay assets-only (no Worker script, no D1/KV/R2/AI binding, no cron) — static asset
    requests are free, anything with code or storage is billed on the shared Cloudflare account."""
    bad = [k for k in FORBIDDEN if k in cfg]
    if bad:
        sys.exit(f"refusing to deploy {name}: billed features in config: {bad}")
    if set(cfg.get("assets", {})) - {"directory", "html_handling", "not_found_handling"}:
        sys.exit(f"refusing to deploy {name}: unexpected assets options")
    path = APP / f".wrangler-{name}.json"
    path.write_text(json.dumps(cfg, indent=1))
    r = subprocess.run(["npx", "--yes", WRANGLER, *cmd, "--config", str(path)], cwd=APP, capture_output=capture, text=capture)
    path.unlink(missing_ok=True)
    if capture:
        print(r.stdout[-3000:], r.stderr[-2000:], sep="\n")
    return r


def upload(cfg, name):
    """Upload a new version WITHOUT serving it (the slow part: tens of thousands of files). Returns its version id, or
    None when the Worker does not exist yet (first deploy of a new shard)."""
    r = wrangler(cfg, name, ("versions", "upload", "--message", "vian build"), capture=True)
    m = re.search(r"Worker Version ID:\s*([0-9a-f-]{36})", (r.stdout or "") + (r.stderr or ""))
    if r.returncode or not m:
        if "does not exist" in (r.stderr or "") + (r.stdout or "") or "10007" in (r.stderr or ""):
            return None
        sys.exit(f"version upload of {name} failed")
    return m.group(1)


def activate(cfg, name, version):
    """Serve the uploaded version (seconds) and apply its routes."""
    if wrangler(cfg, name, ("versions", "deploy", f"{version}@100%", "--yes", "--message", "vian build")).returncode:
        sys.exit(f"activating {name} failed")
    if wrangler(cfg, name, ("triggers", "deploy")).returncode:
        sys.exit(f"routes of {name} failed")


def base_cfg(name, directory):
    return {"name": name, "compatibility_date": "2026-10-01", "preview_urls": False, "observability": {"enabled": False},
            "assets": {"directory": str(directory), "html_handling": "auto-trailing-slash", "not_found_handling": "404-page"}}


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
    # Two phases, so visitors never see a half-deployed site (13. 11. 2026: a deploy of 20+ minutes showed new listings
    # linking to product pages the shards did not have yet, and the other order showed pages without their new CSS):
    #   1. upload every Worker's new version without serving it (the slow part),
    #   2. switch them all within seconds - main first, because it alone serves /assets/ and an /assets/ 404 is cached
    #      for a year; it also still carries the previous CSS/JS (build state), so old pages keep their styles.
    main_cfg = base_cfg("vian", DIST)
    main_cfg["workers_dev"] = False
    main_cfg["routes"] = [{"pattern": f"{ZONE}/*", "zone_name": ZONE}, {"pattern": f"www.{ZONE}/*", "zone_name": ZONE}]
    workers = [("vian", main_cfg)]
    for name, d, chars in shard_dirs:
        cfg = base_cfg(name, d)
        cfg["workers_dev"] = False
        cfg["routes"] = [{"pattern": f"{ZONE}/produkt/{c}*", "zone_name": ZONE} for c in chars]
        workers.append((name, cfg))
    t0 = time.time()
    versions = [(name, cfg, upload(cfg, name)) for name, cfg in workers]
    print(f"phase 1: {len(versions)} versions uploaded in {time.time() - t0:.0f}s, nothing served yet")
    t1 = time.time()
    for name, cfg, version in versions:
        if version:
            activate(cfg, name, version)
        elif wrangler(cfg, name).returncode:     # a brand-new shard Worker: its first deploy creates it
            sys.exit(f"first deploy of {name} failed")
    print(f"phase 2: all Workers switched in {time.time() - t1:.0f}s")


if __name__ == "__main__":
    main()
