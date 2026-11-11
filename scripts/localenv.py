"""Local development only: load API keys from the workspace credentials/ folder into os.environ.
In GitHub Actions the same names come from repository secrets. Values are never printed.
This file holds no secrets itself — only file and key NAMES."""
import os
from pathlib import Path

CRED = Path(os.environ.get("VIAN_CRED_DIR", "/home/kenny/ai/credentials"))
FILES = [".vian-credentials.env"]


def load():
    for name in FILES:
        p = CRED / name
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v.strip().strip("\"'"))
