#!/usr/bin/env python3
"""Update only ACB Detailed Quote Form PHP snippet (email logo fix)."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"


def api(method: str, path: str, payload=None):
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode() or "{}")


def main() -> None:
    code = (ROOT / "acb-detailed-quote-snippet.php").read_text(encoding="utf-8").strip()
    if code.startswith("<?php"):
        code = code[5:].lstrip()
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    name = "ACB Detailed Quote Form"
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "AJAX + nonce for detailed quote form on /get-quote/ (sales@americacustomboxes.com)",
        "code": code,
        "scope": "global",
        "active": True,
        "priority": 6,
    }
    if not existing:
        raise SystemExit("Snippet not found")
    api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
    print("Updated snippet", existing["id"], "— email logo now embeds as PNG CID")


if __name__ == "__main__":
    main()
